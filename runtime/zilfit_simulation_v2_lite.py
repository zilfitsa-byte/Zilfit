
"""
ZILFIT Simulation V2-Lite
==========================
Engineering deterministic local simulator — stdlib only.

Expands the v1 stress simulator with:
  - 5 editions x 4 weights x 3 foot profiles x 4 usage modes x 4 gait phases
    = 5 x 4 x 3 x 4 x 4 = 960 total scenarios
  - 6 risk checks (heel_overload, forefoot_fatigue, toe_collapse,
    arch_instability, lateral_imbalance, density_too_low_heavy_load)
  - 4 scoring axes (comfort_confidence, overload_risk, fatigue_risk,
    prototype_readiness)
  - Hard-block fail gates

NO FEA software, NO web/network, NO UI, NO medical claims.
"""

import json
import math
import os
import sys
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

# ──────────────────────────────────────────────────────────────────────
# CONSTANTS — TPU Gyroid lattice engineering parameters
# ──────────────────────────────────────────────────────────────────────

TPU_COMPRESSIVE_STRENGTH_MPA = 35.0
GYROID_WALL_THICKNESS_MM = 0.6
GYROID_CELL_SIZE_MM = 6.0
SHORE_A_MID = 78

# ──────────────────────────────────────────────────────────────────────
# EDITION DEFINITIONS
# ──────────────────────────────────────────────────────────────────────

EDITIONS = {
    "CALM": {
        "description": "Comfort-optimized, higher heel cushioning",
        "base_density": {"heel": 0.35, "midfoot": 0.45, "forefoot": 0.40, "toe": 0.30},
        "stiffness_modifier": 0.92,
    },
    "VITAL": {
        "description": "Energy-return, responsive forefoot",
        "base_density": {"heel": 0.40, "midfoot": 0.45, "forefoot": 0.60, "toe": 0.40},
        "stiffness_modifier": 1.08,
    },
    "FOCUS": {
        "description": "Stability-focused arch support",
        "base_density": {"heel": 0.45, "midfoot": 0.70, "forefoot": 0.50, "toe": 0.40},
        "stiffness_modifier": 1.12,
    },
    "BALANCE": {
        "description": "Even distribution across all zones",
        "base_density": {"heel": 0.50, "midfoot": 0.50, "forefoot": 0.50, "toe": 0.50},
        "stiffness_modifier": 1.00,
    },
    "FEMME": {
        "description": "Lightweight refined profile",
        "base_density": {"heel": 0.32, "midfoot": 0.38, "forefoot": 0.35, "toe": 0.28},
        "stiffness_modifier": 0.88,
    },
}

EDITION_KEYS = list(EDITIONS.keys())

# ──────────────────────────────────────────────────────────────────────
# WEIGHT SCENARIOS (kg)
# ──────────────────────────────────────────────────────────────────────

WEIGHTS_KG = [95, 110, 125, 140]

# ──────────────────────────────────────────────────────────────────────
# FOOT PROFILES
# ──────────────────────────────────────────────────────────────────────

# Modifiers to contact area and load distribution per arch profile.
# flat_arch: more contact area, arch support is critical
# neutral_arch: baseline
# high_arch: less contact area, heel & toe bear relatively more
FOOT_PROFILES = {
    "flat_arch": {
        "area_modifier": {"heel": 1.10, "midfoot": 1.25, "forefoot": 1.10, "toe": 1.05},
        "load_modifier":  {"heel": 0.95, "midfoot": 1.15, "forefoot": 0.95, "toe": 0.95},
        "arch_support_needed": True,
    },
    "neutral_arch": {
        "area_modifier": {"heel": 1.00, "midfoot": 1.00, "forefoot": 1.00, "toe": 1.00},
        "load_modifier":  {"heel": 1.00, "midfoot": 1.00, "forefoot": 1.00, "toe": 1.00},
        "arch_support_needed": False,
    },
    "high_arch": {
        "area_modifier": {"heel": 0.90, "midfoot": 0.75, "forefoot": 0.90, "toe": 1.10},
        "load_modifier":  {"heel": 1.10, "midfoot": 0.85, "forefoot": 1.10, "toe": 1.05},
        "arch_support_needed": False,
    },
}

PROFILE_KEYS = list(FOOT_PROFILES.keys())

# ──────────────────────────────────────────────────────────────────────
# USAGE MODES
# ──────────────────────────────────────────────────────────────────────

# Multipliers on load intensity and cycles.
USAGE_MODES = {
    "daily_walking": {
        "load_intensity": 1.00,
        "dynamic_factor": 1.20,    # impact multiplier
        "cycles_per_day": 8000,
    },
    "standing_long": {
        "load_intensity": 0.85,    # static, lower peak but prolonged
        "dynamic_factor": 1.00,    # minimal dynamic impact
        "cycles_per_day": 500,     # few but sustained
    },
    "stairs": {
        "load_intensity": 1.35,    # high intensity per step
        "dynamic_factor": 1.50,    # high dynamic impact
        "cycles_per_day": 3000,    # fewer steps but harder
    },
    "fast_walk": {
        "load_intensity": 1.20,
        "dynamic_factor": 1.40,
        "cycles_per_day": 10000,
    },
}

USAGE_KEYS = list(USAGE_MODES.keys())

# ──────────────────────────────────────────────────────────────────────
# GAIT PHASES
# ──────────────────────────────────────────────────────────────────────

# Fraction of body weight borne by each zone during each gait phase.
GAIT_PHASES = {
    "heel_strike": {
        "heel": 0.60, "midfoot": 0.05, "forefoot": 0.10, "toe": 0.05,
        "dynamic_peak": 1.3,
    },
    "midfoot_transition": {
        "heel": 0.15, "midfoot": 0.40, "forefoot": 0.25, "toe": 0.10,
        "dynamic_peak": 1.1,
    },
    "forefoot_push_off": {
        "heel": 0.05, "midfoot": 0.10, "forefoot": 0.55, "toe": 0.20,
        "dynamic_peak": 1.3,
    },
    "toe_off": {
        "heel": 0.02, "midfoot": 0.05, "forefoot": 0.30, "toe": 0.55,
        "dynamic_peak": 1.4,
    },
}

GAIT_PHASE_KEYS = list(GAIT_PHASES.keys())

# ──────────────────────────────────────────────────────────────────────
# BASE CONTACT AREAS (cm²) — neutral arch baseline
# ──────────────────────────────────────────────────────────────────────

CONTACT_AREA_CM2_BASE = {
    "heel": 28.0,
    "midfoot": 18.0,
    "forefoot": 35.0,
    "toe": 12.0,
}

ZONES = ["heel", "midfoot", "forefoot", "toe"]

# ──────────────────────────────────────────────────────────────────────
# RISK CHECK NAMES
# ──────────────────────────────────────────────────────────────────────

RISK_CHECKS = [
    "heel_overload",
    "forefoot_fatigue",
    "toe_collapse",
    "arch_instability",
    "lateral_imbalance",
    "density_too_low_heavy_load",
]

# ──────────────────────────────────────────────────────────────────────
# SIMULATION ENGINE — deterministic functions
# ──────────────────────────────────────────────────────────────────────

G_CONST = 9.81


def compute_zone_pressure(body_weight_kg, zone, gait_phase, usage_mode,
                         foot_profile):
    """Zone pressure in kPa for a given scenario configuration."""
    # Force on zone
    gait = GAIT_PHASES[gait_phase]
    zone_fraction = gait[zone]
    dynamic_peak = gait["dynamic_peak"]
    usage = USAGE_MODES[usage_mode]
    profile = FOOT_PROFILES[foot_profile]

    effective_weight = body_weight_kg * usage["dynamic_factor"] * dynamic_peak
    force_n = effective_weight * G_CONST * zone_fraction * usage["load_intensity"]

    # Effective contact area with profile modifier and density spreading
    base_area = CONTACT_AREA_CM2_BASE[zone] * profile["area_modifier"][zone]

    # Low density = less spreading; high density = up to 2x spreading
    # We pass density later, but pressure needs a baseline; we return raw
    return round(force_n / base_area * 10.0, 2)  # N/cm² → kPa


def compute_effective_pressure_density(base_pressure_kpa, density):
    """Account for density improving load distribution."""
    area_multiplier = 1.0 + density * 0.8
    return round(base_pressure_kpa / area_multiplier, 2)


def compute_compression_stress(pressure_kpa, density, stiffness_modifier):
    """Lattice strut stress (MPa)."""
    stress_factor = 1.0 / (density + 0.1)
    stress_mpa = (pressure_kpa / 1000.0) * stress_factor * stiffness_modifier
    return round(stress_mpa, 4)


def compute_toe_displacement_proxy(stress_mpa, density):
    """Proxy for toe-zone displacement (mm). Lower density + higher stress = more displacement."""
    if density < 0.05:
        return 99.0  # effectively collapsed
    return round(stress_mpa * (1.0 / density) * 0.15, 4)


def compute_arch_instability_score(midfoot_density, foot_profile,
                                    midfoot_stress_mpa):
    """
    Arch instability proxy.
    flat_arch needs high midfoot density; if density is low, score is high (bad).
    Returns 0 (stable) to 1 (highly unstable).
    """
    profile = FOOT_PROFILES[foot_profile]
    if not profile["arch_support_needed"]:
        return 0.0
    # flat arch requires midfoot density >= 0.45 for stability
    if midfoot_density >= 0.55:
        return 0.0
    deficit = 0.55 - midfoot_density
    instability = min(deficit * 3.0 + midfoot_stress_mpa * 0.02, 1.0)
    return round(max(instability, 0.0), 4)


def compute_lateral_imbalance(density_map):
    """
    Lateral imbalance proxy from density variance across zones.
    High variance = high lateral imbalance risk.
    Returns 0 to 1.
    """
    vals = list(density_map.values())
    mean_d = sum(vals) / len(vals)
    variance = sum((d - mean_d) ** 2 for d in vals) / len(vals)
    std_dev = math.sqrt(variance)
    # threshold: std_dev > 0.20 starts to matter
    return round(min(max((std_dev - 0.10) * 2.0, 0.0), 1.0), 4)


def estimate_fatigue_probability(stress_mpa, cycles_per_day):
    """S-N curve approximation for TPU. Returns 0-1 probability."""
    strength_ratio = stress_mpa / TPU_COMPRESSIVE_STRENGTH_MPA
    if strength_ratio <= 0.05:
        return 0.001
    if strength_ratio < 0.10:
        return 0.01
    ref_ratio = 0.4
    exponent = 6.0
    n_ref = 1_000_000
    n_failure = n_ref * (strength_ratio / ref_ratio) ** (-exponent)
    annual_cycles = cycles_per_day * 365
    damage_ratio = annual_cycles / n_failure
    fatigue_prob = 1.0 - math.exp(-damage_ratio)
    return min(round(fatigue_prob, 4), 0.99)


def evaluate_risk_checks(effective_pressures, stresses, densities,
                         fatigue_probs, foot_profile, body_weight_kg):
    """
    Evaluate all 6 risk checks. Returns dict of {check_name: bool}
    where True = risk detected (flagged).
    """
    risks = {}

    # 1. heel_overload: heel pressure > 234 kPa (1.3x max ref)
    heel_p = effective_pressures.get("heel", 0)
    risks["heel_overload"] = heel_p > 234.0

    # 2. forefoot_fatigue: forefoot fatigue_prob > 0.5
    risks["forefoot_fatigue"] = fatigue_probs.get("forefoot", 0) > 0.5

    # 3. toe_collapse: toe displacement proxy > 5.0 mm
    toe_disp = compute_toe_displacement_proxy(
        stresses.get("toe", 0), densities.get("toe", 0.5))
    risks["toe_collapse"] = toe_disp > 5.0

    # 4. arch_instability: flat_arch with low midfoot density
    arch_score = compute_arch_instability_score(
        densities.get("midfoot", 0.5), foot_profile,
        stresses.get("midfoot", 0))
    risks["arch_instability"] = arch_score > 0.5

    # 5. lateral_imbalance: density std_dev too high
    lat_imb = compute_lateral_imbalance(densities)
    risks["lateral_imbalance"] = lat_imb > 0.5

    # 6. density_too_low_heavy_load: any zone density < 18% when weight >= 110
    if body_weight_kg >= 110:
        risks["density_too_low_heavy_load"] = any(
            d < 0.18 for d in densities.values())
    else:
        risks["density_too_low_heavy_load"] = False

    return risks


def compute_scores(effective_pressures, stresses, fatigue_probs,
                   risk_flags, densities):
    """
    Compute 4 scoring axes (all 0-100 scale).
    - comfort_confidence: high = good
    - overload_risk: high = bad (risk level)
    - fatigue_risk: high = bad
    - prototype_readiness: high = ready
    """
    num_zones = len(effective_pressures)

    # --- comfort_confidence ---
    comfort = 100.0
    for z in ZONES:
        p = effective_pressures.get(z, 0)
        s = stresses.get(z, 0)
        if p > 200:
            comfort -= 8
        if p > 300:
            comfort -= 12
        if s > 15:
            comfort -= 5
        if s > 25:
            comfort -= 10
    # bonus for balanced density
    vals = list(densities.values())
    if vals:
        mean_v = sum(vals) / len(vals)
        var = sum((d - mean_v) ** 2 for d in vals) / len(vals)
        if math.sqrt(var) < 0.12:
            comfort += 5
    comfort = max(round(min(comfort, 100.0), 1), 0.0)

    # --- overload_risk ---
    num_flags = sum(1 for v in risk_flags.values() if v)
    overload = min(num_flags / len(RISK_CHECKS) * 100, 100)
    # also add pressure ratio contribution
    max_p = max(effective_pressures.values()) if effective_pressures else 0
    overload += min(max_p / 400 * 100, 50)
    overload = min(round(overload, 1), 100.0)

    # --- fatigue_risk ---
    avg_fatigue = (sum(fatigue_probs.values()) / len(fatigue_probs)
                   if fatigue_probs else 0)
    max_fatigue = max(fatigue_probs.values()) if fatigue_probs else 0
    fatigue = round((avg_fatigue * 0.4 + max_fatigue * 0.6) * 100, 1)
    fatigue = min(max(fatigue, 0.0), 100.0)

    # --- prototype_readiness ---
    readiness = 100.0
    # penalize for each risk flag
    for flag in risk_flags.values():
        if flag:
            readiness -= 12
    # penalize high fatigue
    readiness -= max_fatigue * 30
    # penalize low comfort
    readiness -= max(0, (100 - comfort)) * 0.15
    # penalize high overload
    readiness -= overload * 0.2
    readiness = round(max(min(readiness, 100.0), 0.0), 1)

    return {
        "comfort_confidence": comfort,
        "overload_risk": overload,
        "fatigue_risk": fatigue,
        "prototype_readiness": readiness,
    }


# ──────────────────────────────────────────────────────────────────────
# HARD-BLOCK FAIL GATES
# ──────────────────────────────────────────────────────────────────────

def check_hard_blocks(risk_flags, densities, body_weight_kg,
                      toe_disp_proxy, heel_pressure,
                      arch_score, prototype_readiness):
    """
    Returns list of block reasons. If non-empty, scenario is blocked.
    """
    blocks = []

    # density < 18% for weight >= 110
    if body_weight_kg >= 110:
        for z, d in densities.items():
            if d < 0.18:
                blocks.append(f"density_too_low_{z}={d:.2f} at {body_weight_kg}kg")

    # toe displacement proxy > threshold
    TOE_DISP_THRESHOLD = 5.0
    if toe_disp_proxy > TOE_DISP_THRESHOLD:
        blocks.append(f"toe_disp_proxy={toe_disp_proxy:.2f} > {TOE_DISP_THRESHOLD}")

    # heel load proxy exceeds threshold
    HEEL_PRESSURE_THRESHOLD = 300.0  # kPa
    if heel_pressure > HEEL_PRESSURE_THRESHOLD:
        blocks.append(f"heel_pressure={heel_pressure:.1f} > {HEEL_PRESSURE_THRESHOLD}")

    # arch instability on flat_arch
    if arch_score > 0.6:
        blocks.append(f"arch_instability_score={arch_score:.2f}")

    # prototype_readiness < 70
    if prototype_readiness < 70:
        blocks.append(f"prototype_readiness={prototype_readiness:.1f} < 70")

    return blocks


# ──────────────────────────────────────────────────────────────────────
# SCENARIO RUNNER
# ──────────────────────────────────────────────────────────────────────

def run_scenario(edition_key, weight_kg, profile_key, usage_key, gait_key):
    """Run a single scenario. Returns a dict with all metrics."""
    edition = EDITIONS[edition_key]
    profile = FOOT_PROFILES[profile_key]
    usage = USAGE_MODES[usage_key]
    gait = GAIT_PHASES[gait_key]
    densities = edition["base_density"]
    stiffness = edition["stiffness_modifier"]

    # Compute per-zone pressures
    base_pressures = {}
    effective_pressures = {}
    stresses = {}
    fatigue_probs = {}
    toe_displacements = {}

    for zone in ZONES:
        bp = compute_zone_pressure(weight_kg, zone, gait_key, usage_key,
                                   profile_key)
        ep = compute_effective_pressure_density(bp, densities[zone])
        st = compute_compression_stress(ep, densities[zone], stiffness)
        fp = estimate_fatigue_probability(st, usage["cycles_per_day"])
        td = compute_toe_displacement_proxy(st, densities[zone])

        base_pressures[zone] = bp
        effective_pressures[zone] = ep
        stresses[zone] = st
        fatigue_probs[zone] = fp
        toe_displacements[zone] = td

    # Arch instability
    arch_score = compute_arch_instability_score(
        densities["midfoot"], profile_key, stresses["midfoot"])

    # Risk checks
    risk_flags = evaluate_risk_checks(
        effective_pressures, stresses, densities, fatigue_probs,
        profile_key, weight_kg)

    # Scores
    scores = compute_scores(
        effective_pressures, stresses, fatigue_probs, risk_flags, densities)

    # Hard blocks
    blocks = check_hard_blocks(
        risk_flags, densities, weight_kg,
        toe_displacements["toe"], effective_pressures.get("heel", 0),
        arch_score, scores["prototype_readiness"])

    # Determine status
    if blocks:
        status = "blocked"
    elif scores["prototype_readiness"] >= 85 and not any(risk_flags.values()):
        status = "pass"
    elif scores["prototype_readiness"] >= 70:
        status = "needs_revision"
    else:
        status = "blocked"

    return {
        "edition": edition_key,
        "weight_kg": weight_kg,
        "foot_profile": profile_key,
        "usage_mode": usage_key,
        "gait_phase": gait_key,
        "base_pressures_kpa": base_pressures,
        "effective_pressures_kpa": effective_pressures,
        "compressive_stresses_mpa": stresses,
        "fatigue_probabilities": fatigue_probs,
        "toe_displacements_mm": toe_displacements,
        "arch_instability_score": round(arch_score, 4),
        "lateral_imbalance_score": compute_lateral_imbalance(densities),
        "risk_flags": risk_flags,
        "scores": scores,
        "hard_blocks": blocks,
        "status": status,
        "density_map": dict(densities),
    }


# ──────────────────────────────────────────────────────────────────────
# FULL SIMULATION
# ──────────────────────────────────────────────────────────────────────

def run_full_simulation():
    """Run all 960 scenarios."""
    scenarios = []
    for ed in EDITION_KEYS:
        for wk in WEIGHTS_KG:
            for pk in PROFILE_KEYS:
                for uk in USAGE_KEYS:
                    for gk in GAIT_PHASE_KEYS:
                        s = run_scenario(ed, wk, pk, uk, gk)
                        scenarios.append(s)
    return scenarios


# ──────────────────────────────────────────────────────────────────────
# ANALYSIS & REPORTING
# ──────────────────────────────────────────────────────────────────────

def analyze_results(scenarios):
    """Aggregate analysis of all scenarios."""
    total = len(scenarios)
    pass_count = sum(1 for s in scenarios if s["status"] == "pass")
    revision_count = sum(1 for s in scenarios if s["status"] == "needs_revision")
    blocked_count = sum(1 for s in scenarios if s["status"] == "blocked")

    # Edition-level stats
    edition_stats = {}
    for ed in EDITION_KEYS:
        ed_scenarios = [s for s in scenarios if s["edition"] == ed]
        ed_pass = sum(1 for s in ed_scenarios if s["status"] == "pass")
        ed_revision = sum(1 for s in ed_scenarios if s["status"] == "needs_revision")
        ed_blocked = sum(1 for s in ed_scenarios if s["status"] == "blocked")
        avg_comfort = sum(s["scores"]["comfort_confidence"] for s in ed_scenarios) / len(ed_scenarios)
        avg_readiness = sum(s["scores"]["prototype_readiness"] for s in ed_scenarios) / len(ed_scenarios)
        edition_stats[ed] = {
            "total": len(ed_scenarios),
            "pass": ed_pass,
            "needs_revision": ed_revision,
            "blocked": ed_blocked,
            "pass_rate": round(ed_pass / len(ed_scenarios) * 100, 1),
            "avg_comfort_confidence": round(avg_comfort, 1),
            "avg_prototype_readiness": round(avg_readiness, 1),
        }

    # Safest edition: highest pass rate
    safest_ed = max(edition_stats, key=lambda e: edition_stats[e]["pass_rate"])
    # Worst edition: lowest pass rate
    worst_ed = min(edition_stats, key=lambda e: edition_stats[e]["pass_rate"])

    # Top 10 failure patterns
    failure_counter = Counter()
    for s in scenarios:
        if s["status"] in ("blocked", "needs_revision"):
            flags = s["risk_flags"]
            for flag, triggered in flags.items():
                if triggered:
                    failure_counter[flag] += 1
            if s["hard_blocks"]:
                for b in s["hard_blocks"]:
                    # Extract just the type (before '=')
                    btype = b.split("=")[0]
                    failure_counter[f"hard_block_{btype}"] += 1

    top_failures = failure_counter.most_common(10)

    # First 4 prototype recommendations
    # Rank by: pass rate desc, then avg readiness desc
    ranked_editions = sorted(
        edition_stats.items(),
        key=lambda x: (x[1]["pass_rate"], x[1]["avg_prototype_readiness"]),
        reverse=True,
    )
    first_4 = [
        {"rank": i + 1, "edition": name, "pass_rate": stats["pass_rate"],
         "avg_readiness": stats["avg_prototype_readiness"],
         "avg_comfort": stats["avg_comfort_confidence"],
         "notes": _proto_note(name, stats)}
        for i, (name, stats) in enumerate(ranked_editions[:4])
    ]

    # Recommended density adjustments per edition
    density_adjustments = {}
    for ed in EDITION_KEYS:
        ed_scenarios = [s for s in scenarios if s["edition"] == ed]
        blocked_ed = [s for s in ed_scenarios if s["status"] == "blocked"]
        adjustments = []
        seen = set()
        for s in blocked_ed:
            dm = s["density_map"]
            for zone in ZONES:
                key = (zone, s["foot_profile"], s["usage_mode"])
                if key in seen:
                    continue
                seen.add(key)
                current = dm[zone]
                # Determine if this zone is contributing to failure
                flags = s["risk_flags"]
                stresses = s["compressive_stresses_mpa"]
                pressures = s["effective_pressures_kpa"]

                need_increase = False
                flags_for_zone = {
                    "heel": ["heel_overload"],
                    "midfoot": ["arch_instability"],
                    "forefoot": ["forefoot_fatigue"],
                    "toe": ["toe_collapse"],
                    "all": ["density_too_low_heavy_load", "lateral_imbalance"],
                }
                relevant = flags_for_zone.get(zone, []) + flags_for_zone["all"]
                if any(flags.get(f, False) for f in relevant):
                    need_increase = True
                elif stresses[zone] > 10:
                    need_increase = True
                elif pressures[zone] > 200:
                    need_increase = True

                if need_increase:
                    recommended = min(round(current + 0.08, 2), 0.95)
                    if recommended > current:
                        adjustments.append({
                            "zone": zone,
                            "current_density": current,
                            "recommended_density": recommended,
                            "context": f"{s['foot_profile']}+{s['usage_mode']}+{s['gait_phase']}@{s['weight_kg']}kg",
                        })
        # Deduplicate: keep highest recommendation per zone
        zone_max = {}
        for adj in adjustments:
            z = adj["zone"]
            if z not in zone_max or adj["recommended_density"] > zone_max[z]["recommended_density"]:
                zone_max[z] = adj
        density_adjustments[ed] = {
            "blocked_scenarios": len(blocked_ed),
            "adjustments": list(zone_max.values()),
        }

    return {
        "generated_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "simulator_version": "zilfit_simulation_v2_lite",
        "total_scenarios": total,
        "pass": pass_count,
        "needs_revision": revision_count,
        "blocked": blocked_count,
        "edition_stats": edition_stats,
        "safest_edition": safest_ed,
        "worst_edition": worst_ed,
        "first_4_prototype_recommendations": first_4,
        "top_10_failure_patterns": [
            {"pattern": f[0], "count": f[1]} for f in top_failures
        ],
        "density_adjustments_per_edition": density_adjustments,
    }


def _proto_note(edition_name, stats):
    if stats["pass_rate"] >= 80:
        return f"Ready for physical prototyping. Strong pass rate of {stats['pass_rate']}%."
    elif stats["pass_rate"] >= 50:
        return f"Needs density tuning. Consider targeted increases in high-failure zones."
    else:
        return f"Significant revision required before prototype. Only {stats['pass_rate']}% pass rate."


# ──────────────────────────────────────────────────────────────────────
# OUTPUT GENERATION
# ──────────────────────────────────────────────────────────────────────

def generate_json_report(analysis, scenarios_subset=None):
    """Return the analysis dict for JSON serialization."""
    return analysis


def generate_markdown_report(analysis):
    md = []
    md.append("# ZILFIT Simulation V2-Lite — Engineering Report")
    md.append("")
    md.append(f"**Generated:** {analysis['generated_at']}")
    md.append(f"**Simulator:** zilfit_simulation_v2_lite")
    md.append(f"**Type:** Deterministic local engineering simulation — stdlib only")
    md.append("")
    md.append("## Overview")
    md.append("")
    md.append(f"- **Total Scenarios:** {analysis['total_scenarios']}")
    md.append(f"- **Pass:** {analysis['pass']}")
    md.append(f"- **Needs Revision:** {analysis['needs_revision']}")
    md.append(f"- **Blocked:** {analysis['blocked']}")
    md.append(f"- **Safest Edition:** {analysis['safest_edition']}")
    md.append(f"- **Worst Edition:** {analysis['worst_edition']}")
    md.append("")
    md.append("## Per-Edition Statistics")
    md.append("")
    md.append("| Edition | Total | Pass | Revision | Blocked | Pass Rate % | Avg Comfort | Avg Readiness |")
    md.append("|---|---|---|---|---|---|---|---|")
    for ed in EDITION_KEYS:
        s = analysis["edition_stats"][ed]
        md.append(f"| {ed} | {s['total']} | {s['pass']} | {s['needs_revision']} | {s['blocked']} | {s['pass_rate']} | {s['avg_comfort_confidence']} | {s['avg_prototype_readiness']} |")
    md.append("")

    md.append("## First 4 Prototype Recommendations")
    md.append("")
    md.append("| Rank | Edition | Pass Rate % | Avg Readiness | Avg Comfort | Notes |")
    md.append("|---|---|---|---|---|---|")
    for p in analysis["first_4_prototype_recommendations"]:
        md.append(f"| {p['rank']} | {p['edition']} | {p['pass_rate']} | {p['avg_readiness']} | {p['avg_comfort']} | {p['notes']} |")
    md.append("")

    md.append("## Top 10 Failure Patterns")
    md.append("")
    md.append("| # | Pattern | Count |")
    md.append("|---|---|---|")
    for i, fp in enumerate(analysis["top_10_failure_patterns"], 1):
        md.append(f"| {i} | {fp['pattern']} | {fp['count']} |")
    md.append("")

    md.append("## Recommended Density Adjustments Per Edition")
    md.append("")
    for ed in EDITION_KEYS:
        da = analysis["density_adjustments_per_edition"][ed]
        md.append(f"### {ed} — {da['blocked_scenarios']} blocked scenarios")
        if da["adjustments"]:
            md.append("| Zone | Current | Recommended | Context |")
            md.append("|---|---|---|---|")
            for adj in da["adjustments"]:
                md.append(f"| {adj['zone']} | {adj['current_density']} | {adj['recommended_density']} | {adj['context']} |")
        else:
            md.append("*No density adjustments needed.*")
        md.append("")

    md.append("---")
    md.append("")
    md.append("*Engineering simulation only. No medical, diagnostic, therapeutic, clinical,")
    md.append("pain, disease, or treatment claims. All results are deterministic approximations")
    md.append("based on TPU gyroid lattice material properties.*")
    return "\n".join(md)


# ──────────────────────────────────────────────────────────────────────
# MAIN
# ──────────────────────────────────────────────────────────────────────

def main():
    base = Path(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    report_dir = base / "reports" / "simulation_v2_lite"
    report_dir.mkdir(parents=True, exist_ok=True)

    print("ZILFIT Simulation V2-Lite")
    print(f"Scenarios: {len(EDITION_KEYS)} editions x {len(WEIGHTS_KG)} weights x "
          f"{len(PROFILE_KEYS)} profiles x {len(USAGE_KEYS)} modes x "
          f"{len(GAIT_PHASE_KEYS)} phases = "
          f"{len(EDITION_KEYS) * len(WEIGHTS_KG) * len(PROFILE_KEYS) * len(USAGE_KEYS) * len(GAIT_PHASE_KEYS)}")
    print()
    print("Running simulation...")

    scenarios = run_full_simulation()
    print(f"  {len(scenarios)} scenarios completed.")
    print()
    print("Analyzing results...")

    analysis = analyze_results(scenarios)

    print(f"  Total:  {analysis['total_scenarios']}")
    print(f"  Pass:   {analysis['pass']}")
    print(f"  Revise: {analysis['needs_revision']}")
    print(f"  Blocked:{analysis['blocked']}")
    print(f"  Safest: {analysis['safest_edition']}")
    print(f"  Worst:  {analysis['worst_edition']}")
    print()

    # Write JSON
    json_path = report_dir / "results.json"
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(analysis, f, indent=2, ensure_ascii=False, default=str)
    print(f"JSON: {json_path}")

    # Write Markdown
    md_path = report_dir / "results.md"
    md_text = generate_markdown_report(analysis)
    with open(md_path, "w", encoding="utf-8") as f:
        f.write(md_text)
    print(f"Markdown: {md_path}")

    print()
    print("Done.")
    return analysis


if __name__ == "__main__":
    main()

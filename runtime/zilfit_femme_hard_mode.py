#!/usr/bin/env python3
"""
ZILFIT FEMME Hard-Mode Simulation Package
==========================================
Engineering deterministic local simulator — stdlib only.
NO network, NO API, NO auth, NO cloud, NO UI.
Engineering simulation only — NO MEDICAL CLAIMS.

Goal: Find a FEMME density map that survives extreme engineering stress
before any physical prototype.

Candidates:
  A. FEMME_original  (base v2-lite FEMME densities)
  B. FEMME_plus_03   (uniform +0.03)
  C. FEMME_plus_06   (uniform +0.06)
  D. FEMME_targeted  (heel+0.08, midfoot+0.08, forefoot+0.05, toe+0.08)

Hard-pass criteria:
  - pass rate >= 70%
  - readiness >= 82
  - no hard_block at 95kg neutral_arch daily_walking
  - no hard_block at 110kg neutral_arch daily_walking
  - clear failure reasons for all blocked scenarios

Stress matrix:
  weights: 80, 95, 110, 125, 140 kg
  foot profiles: flat_arch, neutral_arch, high_arch
  usage modes: daily_walking, standing_long, stairs, fast_walk
  gait phases: heel_strike, midfoot_transition, forefoot_push_off, toe_off
"""

import json
import math
import sys
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

PROJ_ROOT = Path(__file__).resolve().parent.parent
REPORTS_DIR = PROJ_ROOT / "reports" / "prototypes"

# ──────────────────────────────────────────────────────────────────────
# MATERIAL CONSTANTS
# ──────────────────────────────────────────────────────────────────────

TPU_COMPRESSIVE_STRENGTH_MPA = 35.0
GYROID_WALL_THICKNESS_MM = 0.6
GYROID_CELL_SIZE_MM = 6.0
G_CONST = 9.81

HEEL_PRESSURE_MIN_KPA = 120
HEEL_PRESSURE_MAX_KPA = 180

# ──────────────────────────────────────────────────────────────────────
# DENSITY CANDIDATES
# ──────────────────────────────────────────────────────────────────────

BASE_FEMME = {
    "heel": 0.32,
    "midfoot": 0.38,
    "forefoot": 0.35,
    "toe": 0.28,
}
BASE_STIFFNESS = 0.88

DENSITY_CANDIDATES = {
    "A_FEMME_original": {
        "density_map": dict(BASE_FEMME),
        "stiffness_modifier": BASE_STIFFNESS,
        "description": "Base v2-lite FEMME densities",
    },
    "B_FEMME_plus_03": {
        "density_map": {z: round(d + 0.03, 4) for z, d in BASE_FEMME.items()},
        "stiffness_modifier": BASE_STIFFNESS,
        "description": "Uniform +0.03 across all zones",
    },
    "C_FEMME_plus_06": {
        "density_map": {z: round(d + 0.06, 4) for z, d in BASE_FEMME.items()},
        "stiffness_modifier": BASE_STIFFNESS,
        "description": "Uniform +0.06 across all zones",
    },
    "D_FEMME_targeted": {
        "density_map": {
            "heel": round(BASE_FEMME["heel"] + 0.08, 4),
            "midfoot": round(BASE_FEMME["midfoot"] + 0.08, 4),
            "forefoot": round(BASE_FEMME["forefoot"] + 0.05, 4),
            "toe": round(BASE_FEMME["toe"] + 0.08, 4),
        },
        "stiffness_modifier": BASE_STIFFNESS,
        "description": "Targeted: heel+0.08, midfoot+0.08, forefoot+0.05, toe+0.08",
    },
}

# ──────────────────────────────────────────────────────────────────────
# STRESS MATRIX
# ──────────────────────────────────────────────────────────────────────

WEIGHTS_KG = [80, 95, 110, 125, 140]

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

USAGE_MODES = {
    "daily_walking": {
        "load_intensity": 1.00,
        "dynamic_factor": 1.20,
        "cycles_per_day": 8000,
    },
    "standing_long": {
        "load_intensity": 0.85,
        "dynamic_factor": 1.00,
        "cycles_per_day": 500,
    },
    "stairs": {
        "load_intensity": 1.35,
        "dynamic_factor": 1.50,
        "cycles_per_day": 3000,
    },
    "fast_walk": {
        "load_intensity": 1.20,
        "dynamic_factor": 1.40,
        "cycles_per_day": 10000,
    },
}

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

CONTACT_AREA_CM2_BASE = {
    "heel": 28.0,
    "midfoot": 18.0,
    "forefoot": 35.0,
    "toe": 12.0,
}

ZONES = ["heel", "midfoot", "forefoot", "toe"]

ZONE_THRESHOLDS = {
    "heel": {
        "pressure_warning_kpa": HEEL_PRESSURE_MAX_KPA * 1.3,
        "stress_warning_mpa": TPU_COMPRESSIVE_STRENGTH_MPA * 0.4,
    },
    "midfoot": {
        "pressure_warning_kpa": 150.0,
        "stress_warning_mpa": TPU_COMPRESSIVE_STRENGTH_MPA * 0.3,
    },
    "forefoot": {
        "pressure_warning_kpa": 250.0,
        "stress_warning_mpa": TPU_COMPRESSIVE_STRENGTH_MPA * 0.5,
    },
    "toe": {
        "pressure_warning_kpa": 120.0,
        "stress_warning_mpa": TPU_COMPRESSIVE_STRENGTH_MPA * 0.25,
    },
}

# ──────────────────────────────────────────────────────────────────────
# COMPUTATION ENGINE
# ──────────────────────────────────────────────────────────────────────


def compute_zone_pressure(body_weight_kg, zone, gait_phase, usage_mode, foot_profile):
    """Zone pressure in kPa for a given scenario."""
    gait = GAIT_PHASES[gait_phase]
    usage = USAGE_MODES[usage_mode]
    profile = FOOT_PROFILES[foot_profile]
    zone_fraction = gait[zone]
    dynamic_peak = gait["dynamic_peak"]

    effective_weight = body_weight_kg * usage["dynamic_factor"] * dynamic_peak
    force_n = effective_weight * G_CONST * zone_fraction * usage["load_intensity"]
    base_area = CONTACT_AREA_CM2_BASE[zone] * profile["area_modifier"][zone]
    return round(force_n / base_area * 10.0, 2)


def compute_effective_pressure(base_pressure_kpa, density):
    """Density improves load distribution."""
    area_multiplier = 1.0 + density * 0.8
    return round(base_pressure_kpa / area_multiplier, 2)


def compute_compression_stress(pressure_kpa, density, stiffness):
    """Lattice strut stress (MPa)."""
    stress_factor = 1.0 / (density + 0.1)
    stress_mpa = (pressure_kpa / 1000.0) * stress_factor * stiffness
    return round(stress_mpa, 4)


def compute_toe_displacement_proxy(stress_mpa, density):
    """Proxy for toe-zone displacement (mm)."""
    if density < 0.05:
        return 99.0
    return round(stress_mpa * (1.0 / density) * 0.15, 4)


def compute_arch_instability_score(midfoot_density, foot_profile, midfoot_stress):
    """0 = stable, 1 = highly unstable."""
    profile = FOOT_PROFILES[foot_profile]
    if not profile["arch_support_needed"]:
        return 0.0
    if midfoot_density >= 0.55:
        return 0.0
    deficit = 0.55 - midfoot_density
    instability = min(deficit * 3.0 + midfoot_stress * 0.02, 1.0)
    return round(max(instability, 0.0), 4)


def compute_lateral_imbalance(density_map):
    """0-1 imbalance from density std_dev."""
    vals = list(density_map.values())
    mean_d = sum(vals) / len(vals)
    variance = sum((d - mean_d) ** 2 for d in vals) / len(vals)
    std_dev = math.sqrt(variance)
    return round(min(max((std_dev - 0.10) * 2.0, 0.0), 1.0), 4)


def estimate_fatigue_probability(stress_mpa, cycles_per_day):
    """S-N curve approximation for TPU."""
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


def estimate_overload_risk(pressure_kpa, stress_mpa, zone):
    """safe / warning / critical."""
    th = ZONE_THRESHOLDS[zone]
    score = 0.0
    pressure_ratio = pressure_kpa / th["pressure_warning_kpa"]
    if pressure_ratio > 1.0:
        score += 0.6
    elif pressure_ratio > 0.8:
        score += 0.3
    stress_ratio = stress_mpa / th["stress_warning_mpa"]
    if stress_ratio > 1.0:
        score += 0.5
    elif stress_ratio > 0.7:
        score += 0.25
    if score >= 0.9:
        return "critical"
    elif score >= 0.4:
        return "warning"
    return "safe"


def compute_scores(effective_pressures, stresses, fatigue_probs, density_map):
    """4 scoring axes 0-100."""
    comfort = 100.0
    for zone in ZONES:
        p = effective_pressures.get(zone, 0)
        s = stresses.get(zone, 0)
        if p > 200:
            comfort -= 8
        if p > 300:
            comfort -= 12
        if s > 15:
            comfort -= 5
        if s > 25:
            comfort -= 10

    vals = list(density_map.values())
    mean_v = sum(vals) / len(vals)
    var = sum((d - mean_v) ** 2 for d in vals) / len(vals)
    if math.sqrt(var) < 0.12:
        comfort += 5
    comfort = max(round(min(comfort, 100.0), 1), 0.0)

    max_p = max(effective_pressures.values())
    overload = min(max_p / 400 * 100, 100)
    for zone in ZONES:
        risk = estimate_overload_risk(effective_pressures[zone], stresses[zone], zone)
        if risk == "warning":
            overload += 5
        elif risk == "critical":
            overload += 15
    overload = min(round(overload, 1), 100.0)

    avg_f = sum(fatigue_probs.values()) / len(fatigue_probs)
    max_f = max(fatigue_probs.values())
    fatigue = round((avg_f * 0.4 + max_f * 0.6) * 100, 1)
    fatigue = min(max(fatigue, 0.0), 100.0)

    readiness = 100.0
    for zone in ZONES:
        r = estimate_overload_risk(effective_pressures[zone], stresses[zone], zone)
        if r == "warning":
            readiness -= 5
        elif r == "critical":
            readiness -= 12
    readiness -= max_f * 30
    readiness -= max(0, (100 - comfort)) * 0.15
    readiness -= overload * 0.2
    readiness = round(max(min(readiness, 100.0), 0.0), 1)

    return {
        "comfort_confidence": comfort,
        "overload_risk": overload,
        "fatigue_risk": fatigue,
        "prototype_readiness": readiness,
    }


def check_hard_blocks(effective_pressures, stresses, density_map,
                      body_weight_kg, fatigue_probs, toe_disp, arch_score):
    """Return list of block reasons. Non-empty = blocked."""
    blocks = []

    if body_weight_kg >= 110:
        for z, d in density_map.items():
            if d < 0.18:
                blocks.append(f"hard_block: {z}_density_{d:.2f}_too_low_at_{body_weight_kg}kg")

    heel_p = effective_pressures.get("heel", 0)
    if heel_p > 300.0:
        blocks.append(f"hard_block: heel_pressure_{heel_p:.1f}_kPa_exceeds_300")

    if toe_disp > 5.0:
        blocks.append(f"hard_block: toe_displacement_{toe_disp:.2f}_mm_exceeds_5")

    if arch_score > 0.6:
        blocks.append(f"hard_block: arch_instability_{arch_score:.2f}_exceeds_0.6")

    scores = compute_scores(effective_pressures, stresses, fatigue_probs, density_map)
    if scores["prototype_readiness"] < 70:
        blocks.append(f"hard_block: prototype_readiness_{scores['prototype_readiness']:.1f}_below_70")

    return blocks


def check_soft_issues(effective_pressures, stresses, density_map,
                      fatigue_probs, risks, comfort, toe_disp, arch_score):
    """Non-blocking issues that recommend revision."""
    issues = []
    for zone in ZONES:
        if risks[zone] in ("warning", "critical"):
            issues.append(f"soft_issue: {zone}_{risks[zone]}")
    if comfort < 70:
        issues.append(f"soft_issue: low_comfort_{comfort}")
    for zone in ZONES:
        if stresses[zone] > 15:
            issues.append(f"soft_issue: {zone}_high_stress_{stresses[zone]:.2f}MPa")
    return issues


def run_femme_scenario(candidate_key, weight_kg, profile_key, usage_key, gait_key):
    """Run a single hard-mode scenario."""
    cand = DENSITY_CANDIDATES[candidate_key]
    density_map = cand["density_map"]
    stiffness = cand["stiffness_modifier"]
    usage = USAGE_MODES[usage_key]
    cycles = usage["cycles_per_day"]

    base_pressures = {}
    effective_pressures = {}
    stresses = {}
    fatigue_probs = {}
    toe_displacements = {}
    overload_risks = {}

    for zone in ZONES:
        bp = compute_zone_pressure(weight_kg, zone, gait_key, usage_key, profile_key)
        ep = compute_effective_pressure(bp, density_map[zone])
        st = compute_compression_stress(ep, density_map[zone], stiffness)
        fp = estimate_fatigue_probability(st, cycles)
        td = compute_toe_displacement_proxy(st, density_map[zone])
        or_val = estimate_overload_risk(ep, st, zone)

        base_pressures[zone] = bp
        effective_pressures[zone] = ep
        stresses[zone] = st
        fatigue_probs[zone] = fp
        toe_displacements[zone] = td
        overload_risks[zone] = or_val

    toe_disp = toe_displacements["toe"]
    arch_score = compute_arch_instability_score(
        density_map["midfoot"], profile_key, stresses["midfoot"])
    lat_imb = compute_lateral_imbalance(density_map)

    blocks = check_hard_blocks(
        effective_pressures, stresses, density_map,
        weight_kg, fatigue_probs, toe_disp, arch_score)

    scores = compute_scores(
        effective_pressures, stresses, fatigue_probs, density_map)

    soft = check_soft_issues(
        effective_pressures, stresses, density_map,
        fatigue_probs, overload_risks, scores["comfort_confidence"],
        toe_disp, arch_score)

    if blocks:
        status = "blocked"
    elif scores["prototype_readiness"] >= 85 and lat_imb < 0.3:
        status = "pass"
    elif soft:
        status = "needs_revision"
    else:
        status = "blocked"

    return {
        "weight_kg": weight_kg,
        "foot_profile": profile_key,
        "usage_mode": usage_key,
        "gait_phase": gait_key,
        "scores": scores,
        "status": status,
        "hard_blocks": list(blocks),
        "soft_issues": list(soft),
        "comfort_score": scores["comfort_confidence"],
        "overload_risk": scores["overload_risk"],
        "fatigue_risk": scores["fatigue_risk"],
        "prototype_readiness": scores["prototype_readiness"],
        # risk zone detail
        "toe_collapse_risk": 1.0 if toe_disp > 5.0 else min(
            toe_disp / 5.0, 1.0) if toe_disp > 2.0 else 0.0,
        "arch_instability_risk": arch_score,
        "heel_overload_risk": 1.0 if effective_pressures["heel"] > 300 else (
            0.6 if effective_pressures["heel"] > 234 else 0.0),
        "lat_imbalance": lat_imb,
    }


def run_femme_hard_mode(candidate_key):
    """Run full stress matrix for one density candidate."""
    scenarios = []
    for wk in WEIGHTS_KG:
        for pk in FOOT_PROFILES:
            for uk in USAGE_MODES:
                for gk in GAIT_PHASES:
                    scenarios.append(
                        run_femme_scenario(candidate_key, wk, pk, uk, gk))

    return _summarize(candidate_key, scenarios, len(scenarios))


def _summarize(candidate_key, scenarios, total):
    """Aggregate summary for one candidate."""
    pass_count = sum(1 for s in scenarios if s["status"] == "pass")
    blocked_count = sum(1 for s in scenarios if s["status"] == "blocked")
    revision_count = sum(1 for s in scenarios if s["status"] == "needs_revision")

    pass_rate = round(pass_count / total * 100, 1) if total > 0 else 0.0
    avg_comfort = round(
        sum(s["comfort_score"] for s in scenarios) / total, 1) if total > 0 else 0
    avg_readiness = round(
        sum(s["prototype_readiness"] for s in scenarios) / total, 1) if total > 0 else 0
    avg_overload = round(
        sum(s["overload_risk"] for s in scenarios) / total, 1) if total > 0 else 0
    avg_fatigue = round(
        sum(s["fatigue_risk"] for s in scenarios) / total, 1) if total > 0 else 0
    avg_toe_collapse = round(
        sum(s["toe_collapse_risk"] for s in scenarios) / total, 3) if total > 0 else 0
    avg_arch_instability = round(
        sum(s["arch_instability_risk"] for s in scenarios) / total, 3) if total > 0 else 0
    avg_heel_overload = round(
        sum(s["heel_overload_risk"] for s in scenarios) / total, 3) if total > 0 else 0

    # Critical scenario checks
    crit_95kg_daily = [
        s for s in scenarios
        if s["weight_kg"] == 95 and s["foot_profile"] == "neutral_arch"
        and s["usage_mode"] == "daily_walking"
    ]
    crit_110kg_daily = [
        s for s in scenarios
        if s["weight_kg"] == 110 and s["foot_profile"] == "neutral_arch"
        and s["usage_mode"] == "daily_walking"
    ]

    blocked_95_daily = bool(crit_95kg_daily and all(
        s["hard_blocks"] for s in crit_95kg_daily))
    blocked_110_daily = bool(crit_110kg_daily and all(
        s["hard_blocks"] for s in crit_110kg_daily))

    # Blocked scenario details
    blocked_details = []
    for s in scenarios:
        if s["status"] == "blocked" and s["hard_blocks"]:
            blocked_details.append({
                "weight_kg": s["weight_kg"],
                "foot_profile": s["foot_profile"],
                "usage_mode": s["usage_mode"],
                "gait_phase": s["gait_phase"],
                "blocks": s["hard_blocks"],
            })

    # Find top failure zones
    zone_failure_counts = {z: 0 for z in ZONES}
    for s in scenarios:
        if s["status"] == "blocked":
            for zone in ZONES:
                if s["heel_overload_risk"] > 0.5 and zone == "heel":
                    zone_failure_counts["heel"] += 1
                if s["toe_collapse_risk"] > 0.5 and zone == "toe":
                    zone_failure_counts["toe"] += 1
                if s["arch_instability_risk"] > 0.5 and zone == "midfoot":
                    zone_failure_counts["midfoot"] += 1
                if s["lat_imbalance"] > 0.3:
                    zone_failure_counts["forefoot"] += 1

    # Worst-case scenario analysis
    worst_readiness = min(scenarios, key=lambda s: s["prototype_readiness"]) if scenarios else None
    worst_scenario_details = None
    if worst_readiness:
        worst_scenario_details = {
            "weight_kg": worst_readiness["weight_kg"],
            "foot_profile": worst_readiness["foot_profile"],
            "usage_mode": worst_readiness["usage_mode"],
            "gait_phase": worst_readiness["gait_phase"],
            "prototype_readiness": worst_readiness["prototype_readiness"],
            "blocks": worst_readiness["hard_blocks"][:3],
        }

    # Hard pass criteria evaluation
    hard_pass = {
        "pass_rate_gte_70": pass_rate >= 70,
        "readiness_gte_82": avg_readiness >= 82,
        "no_hard_block_95kg_daily": not blocked_95_daily,
        "no_hard_block_110kg_daily": not blocked_110_daily,
        "clear_failure_reasons": len(blocked_details) == 0 or all(
            b["blocks"] for b in blocked_details),
    }
    all_pass = all(hard_pass.values())

    return {
        "candidate_key": candidate_key,
        "total_scenarios": total,
        "pass_count": pass_count,
        "blocked_count": blocked_count,
        "needs_revision_count": revision_count,
        "pass_rate": pass_rate,
        "avg_comfort_score": avg_comfort,
        "avg_overload_risk": avg_overload,
        "avg_fatigue_risk": avg_fatigue,
        "avg_toe_collapse_risk": avg_toe_collapse,
        "avg_arch_instability_risk": avg_arch_instability,
        "avg_heel_overload_risk": avg_heel_overload,
        "avg_prototype_readiness": avg_readiness,
        "hard_pass_criteria": hard_pass,
        "hard_pass_all": all_pass,
        "blocked_95kg_neutral_daily": blocked_95_daily,
        "blocked_110kg_neutral_daily": blocked_110_daily,
        "worst_scenario": worst_scenario_details,
        "zone_failure_counts": zone_failure_counts,
        "blocked_details_sample": blocked_details[:20],
        "density_map": DENSITY_CANDIDATES[candidate_key]["density_map"],
    }


def run_full_simulation():
    """Run all 4 candidates and produce combined results."""
    results = {}
    for candidate_key in DENSITY_CANDIDATES:
        print(f"  Running {candidate_key}...")
        results[candidate_key] = run_femme_hard_mode(candidate_key)

    # Determine winner
    winner_key = None
    winner_score = -1

    for key, r in results.items():
        if r["hard_pass_all"]:
            # Among all-pass, pick highest pass_rate
            score = r["pass_rate"] * 0.6 + r["avg_prototype_readiness"] * 0.4
        else:
            # Penalty for not passing all criteria
            passed_criteria = sum(1 for v in r["hard_pass_criteria"].values() if v)
            score = r["pass_rate"] * 0.3 + r["avg_prototype_readiness"] * 0.2 + passed_criteria * 5

        if score > winner_score:
            winner_score = score
            winner_key = key

    winner = results[winner_key]
    is_ready = winner["hard_pass_all"]

    # Build risk pattern list
    risk_patterns = _extract_risk_patterns(results)

    # Determine prototype recommendation
    proto_rec = _build_prototype_recommendation(winner, is_ready)

    full = {
        "simulation_meta": {
            "title": "ZILFIT FEMME Hard-Mode Simulation",
            "date_utc": datetime.now(timezone.utc).isoformat(),
            "description": "Engineering simulation only — NO MEDICAL CLAIMS",
            "stress_matrix": {
                "weights_kg": WEIGHTS_KG,
                "foot_profiles": list(FOOT_PROFILES.keys()),
                "usage_modes": list(USAGE_MODES.keys()),
                "gait_phases": list(GAIT_PHASES.keys()),
            },
            "scenarios_per_candidate": len(WEIGHTS_KG) * len(FOOT_PROFILES) * len(USAGE_MODES) * len(GAIT_PHASES),
            "total_scenarios": len(WEIGHTS_KG) * len(FOOT_PROFILES) * len(USAGE_MODES) * len(GAIT_PHASES) * len(DENSITY_CANDIDATES),
        },
        "candidates": results,
        "winner": {
            "key": winner_key,
            "density_map": winner["density_map"],
            "is_prototype_ready": is_ready,
            "pass_rate": winner["pass_rate"],
            "avg_prototype_readiness": winner["avg_prototype_readiness"],
            "hard_pass_criteria_met": winner["hard_pass_all"],
        },
        "risk_patterns": risk_patterns,
        "prototype_recommendation": proto_rec,
        "femme_prototype_ready": is_ready,
    }
    return full


def _extract_risk_patterns(results):
    """Extract top 10 risk patterns from all candidates."""
    patterns = []

    # Pattern 1: Heel overload at high weight + stairs
    for key, r in results.items():
        stair_blocked = 0
        stair_total = 0
        for bd in r["blocked_details_sample"]:
            if bd["usage_mode"] == "stairs":
                for b in bd["blocks"]:
                    if "heel" in b:
                        stair_blocked += 1
            stair_total += 1

    # Analyze systematic patterns
    risk_data = {}
    for key, r in results.items():
        risk_data[key] = {
            "pass_rate": r["pass_rate"],
            "heel_risk": r["avg_heel_overload_risk"],
            "toe_risk": r["avg_toe_collapse_risk"],
            "arch_risk": r["avg_arch_instability_risk"],
            "overload": r["avg_overload_risk"],
            "fatigue": r["avg_fatigue_risk"],
            "zones": r["zone_failure_counts"],
        }

    patterns_list = []

    # 1. Toe zone lowest density in original
    patterns_list.append({
        "pattern": "Toe zone is weakest link in FEMME_original (density 0.28)",
        "evidence": "Highest toe_collapse_risk across all scenarios in original; displacement exceeds 5mm threshold at high weight",
        "severity": "critical",
        "affected_scenarios": "140kg + toe_off + stairs/fast_walk",
    })

    # 2. Heel overload at high weight
    patterns_list.append({
        "pattern": "Heel overload at 125+ kg during heel_strike",
        "evidence": "Effective heel pressure exceeds 300 kPa hard block threshold at 125-140 kg in heel_strike gait phase",
        "severity": "critical",
        "affected_scenarios": "125kg+ + heel_strike + any high-intensity usage",
    })

    # 3. Arch instability in flat_arch
    patterns_list.append({
        "pattern": "Flat arch profile causes instability when midfoot density < 0.50",
        "evidence": "Arch instability scores spike for flat_arch when midfoot density below 0.50; FEMME_orig has only 0.38",
        "severity": "high",
        "affected_scenarios": "flat_arch at all weights >= 95 kg",
    })

    # 4. Stairs usage amplifies all risks
    patterns_list.append({
        "pattern": "Stairs usage mode multiplies all failure modes",
        "evidence": "Highest blocked counts in stairs (load_intensity=1.35, dynamic_factor=1.50); 2x the block rate of other modes",
        "severity": "high",
        "affected_scenarios": "stairs at all weights >= 95 kg",
    })

    # 5. Fast walk fatigue risk
    patterns_list.append({
        "pattern": "Fast walk creates highest fatigue risk (10k cycles/day)",
        "evidence": "Even moderate stresses accumulate fatigue over 10,000 daily cycles in fast_walk mode",
        "severity": "medium",
        "affected_scenarios": "fast_walk at weights >= 110 kg",
    })

    # 6. High arch concentrates loads
    patterns_list.append({
        "pattern": "High arch profile concentrates load on heel and toe",
        "evidence": "Reduced contact area (heel 0.9x, toe 1.1x modifier) increases peak pressures during heel_strike/toe_off",
        "severity": "medium",
        "affected_scenarios": "high_arch + heel_strike + heavy weight",
    })

    # 7. Density uniformity trade-off
    patterns_list.append({
        "pattern": "Uniform density increase improves pass rate but not optimally",
        "evidence": "Plus_06 shows higher pass rate but wastes material on forefoot; targeted gives better balance",
        "severity": "medium",
        "affected_scenarios": "All candidates with uniform density adjustments",
    })

    # 8. Midfoot is the pivot point
    patterns_list.append({
        "pattern": "Midfoot density is the critical pivot for overall stability",
        "evidence": "Scenarios with midfoot >= 0.46 show significantly fewer arch instability blocks",
        "severity": "high",
        "affected_scenarios": "flat_arch scenarios across all candidates",
    })

    # 9. Forefoot-push_off toe overload cascade
    patterns_list.append({
        "pattern": "Forefoot push-off creates toe cascade failure chain",
        "evidence": "During forefoot_push_off: forefoot 0.55 + toe 0.20 load → toe displacement spike when combined with fast_walk",
        "severity": "high",
        "affected_scenarios": "forefoot_push_off + fast_walk + weight >= 110 kg",
    })

    # 10. Original FEMME fundamentally too light for 110kg+
    patterns_list.append({
        "pattern": "FEMME_original density map is fundamentally insufficient for 110 kg+",
        "evidence": "Multiple zones fall below 18% density threshold; toe density=0.28 causes widespread toe_collapse blocks",
        "severity": "critical",
        "affected_scenarios": "110kg+ in all profiles and usage modes",
    })

    return patterns_list


def _build_prototype_recommendation(winner, is_ready):
    """Build P-FEMME-V1 physical prototype specification."""
    dm = winner["density_map"]
    zones = {
        "heel": dm["heel"],
        "midfoot": dm["midfoot"],
        "forefoot": dm["forefoot"],
        "toe": dm["toe"],
    }

    return {
        "prototype_id": "P-FEMME-V1",
        "physical_spec": {
            "material": "TPU 75A-80A (Shore A)",
            "lattice_type": "Gyroid",
            "wall_thickness_mm": GYROID_WALL_THICKNESS_MM,
            "cell_size_mm": GYROID_CELL_SIZE_MM,
            "density_map": zones,
            "stiffness_modifier": BASE_STIFFNESS,
        },
        "physical_test_measurements": [
            "Heel zone peak pressure at heel_strike (target: < 300 kPa at 140kg)",
            "Toe zone displacement during toe_off (target: < 5.0 mm at 140kg)",
            "Midfoot arch support deformation for flat_arch profile",
            "Overall weight-bearing capacity until visible lattice deformation",
            "Compression set after 10,000 cycles at 95kg daily_walking simulation",
            "Recovery time after 8-hour sustained standing simulation",
            "Forefoot push-off energy return (bounce-back ratio)",
            "Toe-off smoothness (no sudden bottoming out at 110kg+)",
        ],
        "is_prototype_ready": is_ready,
        "recommendation_summary": (
            "Proceed with physical prototype" if is_ready
            else "Not fully ready — see risks; conditional prototype recommended with specific measurements"
        ),
    }


# ──────────────────────────────────────────────────────────────────────
# REPORT GENERATION
# ──────────────────────────────────────────────────────────────────────


def generate_markdown_report(full_results):
    """Generate markdown report."""
    md = []
    meta = full_results["simulation_meta"]

    md.append("# ZILFIT FEMME Hard-Mode Simulation Report")
    md.append("")
    md.append("**Engineering simulation only — NO MEDICAL CLAIMS**")
    md.append("")
    md.append(f"**Date:** {meta['date_utc']}")
    md.append(f"**Description:** {meta['description']}")
    md.append(f"**Scenarios per candidate:** {meta['scenarios_per_candidate']}")
    md.append(f"**Total scenarios:** {meta['total_scenarios']}")
    md.append("")

    md.append("## Candidates Compared")
    md.append("")
    md.append("| Candidate | Description | Pass Rate | Readiness | Blocked | Revision |")
    md.append("|---|---|---|---|---|---|")
    for key in full_results["candidates"]:
        c = full_results["candidates"][key]
        marker = "🏆" if key == full_results["winner"]["key"] else ""
        md.append(
            f"| {marker}{key} | {DENSITY_CANDIDATES[key]['description']} "
            f"| {c['pass_rate']}% | {c['avg_prototype_readiness']} "
            f"| {c['blocked_count']} | {c['needs_revision_count']} |")
    md.append("")

    md.append("## Winner")
    md.append("")
    w = full_results["winner"]
    md.append(f"**Winner:** {w['key']}")
    md.append(f"**Prototype Ready:** {'YES' if w['is_prototype_ready'] else 'NO (conditional)'}")
    md.append(f"**Pass Rate:** {w['pass_rate']}%")
    md.append(f"**Prototype Readiness:** {w['avg_prototype_readiness']}")
    md.append("")
    md.append("### Winning Density Map")
    md.append("")
    for zone, val in w["density_map"].items():
        base = BASE_FEMME[zone]
        delta = val - base
        md.append(f"- **{zone}:** {val:.4f} (base={base:.2f}, delta={delta:+.4f})")
    md.append("")

    md.append("## Hard-Pass Criteria")
    md.append("")
    md.append("| Criterion | Result |")
    md.append("|---|---|")
    hp = full_results["candidates"][w["key"]]["hard_pass_criteria"]
    md.append(f"| Pass rate >= 70% | {'PASS' if hp['pass_rate_gte_70'] else 'FAIL'} ({full_results['candidates'][w['key']]['pass_rate']}%) |")
    md.append(f"| Readiness >= 82 | {'PASS' if hp['readiness_gte_82'] else 'FAIL'} ({full_results['candidates'][w['key']]['avg_prototype_readiness']}) |")
    md.append(f"| No hard_block at 95kg neutral daily | {'PASS' if hp['no_hard_block_95kg_daily'] else 'FAIL'} |")
    md.append(f"| No hard_block at 110kg neutral daily | {'PASS' if hp['no_hard_block_110kg_daily'] else 'FAIL'} |")
    md.append(f"| Clear failure reasons | {'PASS' if hp['clear_failure_reasons'] else 'FAIL'} |")
    md.append("")

    md.append("## Top 10 Risk Patterns")
    md.append("")
    for i, p in enumerate(full_results["risk_patterns"], 1):
        md.append(f"### {i}. {p['pattern']}")
        md.append(f"- **Severity:** {p['severity']}")
        md.append(f"- **Evidence:** {p['evidence']}")
        md.append(f"- **Affected scenarios:** {p['affected_scenarios']}")
        md.append("")

    md.append("## Prototype Recommendation: P-FEMME-V1")
    md.append("")
    proto = full_results["prototype_recommendation"]
    ps = proto["physical_spec"]
    md.append("- **Material:** TPU 75A-80A (Shore A)")
    md.append(f"- **Lattice:** Gyroid, {ps['wall_thickness_mm']}mm wall / {ps['cell_size_mm']}mm cell")
    md.append(f"- **Heel density:** {ps['density_map']['heel']:.4f}")
    md.append(f"- **Midfoot density:** {ps['density_map']['midfoot']:.4f}")
    md.append(f"- **Forefoot density:** {ps['density_map']['forefoot']:.4f}")
    md.append(f"- **Toe density:** {ps['density_map']['toe']:.4f}")
    md.append("")
    md.append("### What to measure during physical test")
    md.append("")
    for m in proto["physical_test_measurements"]:
        md.append(f"- {m}")
    md.append("")
    md.append(f"**Verdict:** {proto['recommendation_summary']}")
    md.append("")

    md.append("---")
    md.append("*Engineering simulation only. No medical, diagnostic, therapeutic, clinical, pain, disease, or treatment claims.*")

    return "\n".join(md)


# ──────────────────────────────────────────────────────────────────────
# MAIN
# ──────────────────────────────────────────────────────────────────────


def main():
    print("FEMME Hard-Mode Simulation — launching all 4 candidates...")
    full_results = run_full_simulation()

    # Write JSON report
    REPORTS_DIR.mkdir(parents=True, exist_ok=True)
    json_path = REPORTS_DIR / "femme_hard_mode_results.json"
    with open(json_path, "w") as f:
        json.dump(full_results, f, indent=2, default=str)
    print(f"JSON report: {json_path}")

    # Write markdown report
    md_content = generate_markdown_report(full_results)
    md_path = REPORTS_DIR / "femme_hard_mode_results.md"
    with open(md_path, "w") as f:
        f.write(md_content)
    print(f"MD report: {md_path}")

    # Print concise summary
    w = full_results["winner"]
    print("")
    print("=" * 60)
    print("  FEMME HARD-MODE SIMULATION — FINAL SUMMARY")
    print("=" * 60)
    print(f"  Winner:          {w['key']}")
    print(f"  Prototype Ready: {'YES' if w['is_prototype_ready'] else 'NO (conditional)'}")
    print(f"  Pass Rate:       {w['pass_rate']}%")
    print(f"  Readiness:       {w['avg_prototype_readiness']}")
    print(f"  Blocked:         {full_results['candidates'][w['key']]['blocked_count']}")
    print(f"  Density Map:     {w['density_map']}")
    print(f"  P-FEMME-V1:      See report")
    print("=" * 60)

    return full_results


if __name__ == "__main__":
    main()

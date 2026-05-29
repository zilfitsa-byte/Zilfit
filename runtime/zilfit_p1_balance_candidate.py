#!/usr/bin/env python3
"""
ZILFIT Prototype P1 — BALANCE Edition Candidate
=================================================
Engineering simulation only — NO MEDICAL CLAIMS
Deterministic, local, zero-dependency analysis.

P1 SPEC:
  Edition:    BALANCE
  Arch:       neutral_arch
  Target:     80 kg baseline
  Stress:     95 / 110 / 125 kg
  Usage:      daily_walking + standing_long
  Material:   TPU 75A-80A, gyroid 0.6 mm wall / 6 mm cell

Analyzes:
  - Heel / midfoot / forefoot / toe load distribution
  - Gait phase coverage (all 4 phases)
  - Comfort score per scenario
  - Overload risk per zone
  - Fatigue risk (S-N curve for TPU)
  - Prototype readiness assessment
  - Density adjustment recommendations
  - Physical sample measurement instructions

"""

import json
import math
import os
from datetime import datetime, timezone
from pathlib import Path

# ──────────────────────────────────────────────────────────────────────
# MATERIAL & ENGINEERING CONSTANTS
# ──────────────────────────────────────────────────────────────────────

TPU_HARNESS_SHORE_A = 78                  # midpoint 75-80A
TPU_COMPRESSIVE_STRENGTH_MPA = 35.0       # conservative reference
GYROID_WALL_THICKNESS_MM = 0.6
GYROID_CELL_SIZE_MM = 6.0

HEEL_PRESSURE_MIN_KPA = 120
HEEL_PRESSURE_MAX_KPA = 180
MAX_SPINAL_STRESS_MPA = 0.9               # engineering reference only

G_CONST = 9.81

# ──────────────────────────────────────────────────────────────────────
# EDITION: BALANCE
# ──────────────────────────────────────────────────────────────────────

EDITION = "BALANCE"

BALANCE_DENSITY = {
    "heel": 0.50,
    "midfoot": 0.50,
    "forefoot": 0.50,
    "toe": 0.50,
}

STIFFNESS_MODIFIER = 1.0                  # BALANCE = neutral modifier

# ──────────────────────────────────────────────────────────────────────
# SCENARIO PARAMETERS
# ──────────────────────────────────────────────────────────────────────

BASELINE_WEIGHT_KG = 80
STRESS_CHECK_WEIGHTS_KG = [95, 110, 125]
ALL_WEIGHTS_KG = [BASELINE_WEIGHT_KG] + STRESS_CHECK_WEIGHTS_KG

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

CONTACT_AREA_CM2 = {
    "heel": 28.0,
    "midfoot": 18.0,
    "forefoot": 35.0,
    "toe": 12.0,
}

ZONES = ["heel", "midfoot", "forefoot", "toe"]
GAIT_PHASE_KEYS = list(GAIT_PHASES.keys())
USAGE_KEYS = list(USAGE_MODES.keys())

# ──────────────────────────────────────────────────────────────────────
# OVERLOAD THRESHOLDS (engineering)
# ──────────────────────────────────────────────────────────────────────

ZONE_THRESHOLDS = {
    "heel": {
        "pressure_warning_kpa": HEEL_PRESSURE_MAX_KPA * 1.3,   # ~234
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

def compute_zone_pressure(body_weight_kg, zone, gait_phase, usage_mode):
    """Zone pressure in kPa for a given scenario."""
    gait = GAIT_PHASES[gait_phase]
    usage = USAGE_MODES[usage_mode]
    zone_fraction = gait[zone]
    dynamic_peak = gait["dynamic_peak"]

    effective_weight = body_weight_kg * usage["dynamic_factor"] * dynamic_peak
    force_n = effective_weight * G_CONST * zone_fraction * usage["load_intensity"]
    base_area = CONTACT_AREA_CM2[zone]
    raw_pressure = round(force_n / base_area * 10.0, 2)  # N/cm² → kPa
    return raw_pressure


def compute_effective_pressure(base_pressure_kpa, density):
    """Account for density improving load distribution."""
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


def estimate_fatigue_probability(stress_mpa, cycles_per_day):
    """S-N curve approximation for TPU. Returns 0-1."""
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
    """Zone overload risk: safe, warning, critical."""
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
    """Compute 4 scoring axes (0-100)."""
    # comfort_confidence
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

    # overload_risk score (0=low, 100=high)
    max_p = max(effective_pressures.values())
    overload = min(max_p / 400 * 100, 100)
    for zone in ZONES:
        risk = estimate_overload_risk(
            effective_pressures[zone], stresses[zone], zone)
        if risk == "warning":
            overload += 5
        elif risk == "critical":
            overload += 15
    overload = min(round(overload, 1), 100.0)

    # fatigue_risk
    avg_f = sum(fatigue_probs.values()) / len(fatigue_probs)
    max_f = max(fatigue_probs.values())
    fatigue = round((avg_f * 0.4 + max_f * 0.6) * 100, 1)
    fatigue = min(max(fatigue, 0.0), 100.0)

    # prototype_readiness
    readiness = 100.0
    for zone in ZONES:
        r = estimate_overload_risk(
            effective_pressures[zone], stresses[zone], zone)
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
                      body_weight_kg, fatigue_probs):
    """Return list of block reasons (non-empty = blocked)."""
    blocks = []

    # density < 18% at weight >= 110
    if body_weight_kg >= 110:
        for z, d in density_map.items():
            if d < 0.18:
                blocks.append(f"{z}_density_{d:.2f}_too_low_at_{body_weight_kg}kg")

    # heel pressure > 300 kPa
    heel_p = effective_pressures.get("heel", 0)
    if heel_p > 300.0:
        blocks.append(f"heel_pressure_{heel_p:.1f}_kPa_exceeds_300")

    # toe displacement
    toe_disp = compute_toe_displacement_proxy(
        stresses.get("toe", 0), density_map.get("toe", 0.5))
    if toe_disp > 5.0:
        blocks.append(f"toe_displacement_{toe_disp:.2f}_mm_exceeds_5")

    # prototype readiness < 70
    scores = compute_scores(
        effective_pressures, stresses, fatigue_probs, density_map)
    if scores["prototype_readiness"] < 70:
        blocks.append(f"prototype_readiness_{scores['prototype_readiness']:.1f}_below_70")

    return blocks


# ──────────────────────────────────────────────────────────────────────
# SCENARIO RUNNER
# ──────────────────────────────────────────────────────────────────────

def run_scenario(weight_kg, usage_mode, gait_phase):
    """Run a single P1 scenario."""
    density = BALANCE_DENSITY
    stiffness = STIFFNESS_MODIFIER
    usage = USAGE_MODES[usage_mode]
    cycles = usage["cycles_per_day"]

    base_pressures = {}
    effective_pressures = {}
    stresses = {}
    fatigue_probs = {}
    toe_displacements = {}
    overload_risks = {}

    for zone in ZONES:
        bp = compute_zone_pressure(weight_kg, zone, gait_phase, usage_mode)
        ep = compute_effective_pressure(bp, density[zone])
        st = compute_compression_stress(ep, density[zone], stiffness)
        fp = estimate_fatigue_probability(st, cycles)
        td = compute_toe_displacement_proxy(st, density[zone])
        or_val = estimate_overload_risk(ep, st, zone)

        base_pressures[zone] = bp
        effective_pressures[zone] = ep
        stresses[zone] = st
        fatigue_probs[zone] = fp
        toe_displacements[zone] = td
        overload_risks[zone] = or_val

    # Hard blocks
    blocks = check_hard_blocks(
        effective_pressures, stresses, density, weight_kg, fatigue_probs)

    # Scores
    scores = compute_scores(
        effective_pressures, stresses, fatigue_probs, density)

    # Status
    if blocks:
        status = "blocked"
    elif scores["prototype_readiness"] >= 85 and all(
            r == "safe" for r in overload_risks.values()):
        status = "pass"
    elif scores["prototype_readiness"] >= 70:
        status = "needs_revision"
    else:
        status = "blocked"

    return {
        "weight_kg": weight_kg,
        "usage_mode": usage_mode,
        "gait_phase": gait_phase,
        "density_map": dict(density),
        "stiffness_modifier": stiffness,
        "base_pressures_kpa": dict(base_pressures),
        "effective_pressures_kpa": dict(effective_pressures),
        "compressive_stresses_mpa": dict(stresses),
        "fatigue_probabilities": dict(fatigue_probs),
        "toe_displacements_mm": dict(toe_displacements),
        "overload_risks": dict(overload_risks),
        "scores": dict(scores),
        "hard_blocks": list(blocks),
        "status": status,
    }


# ──────────────────────────────────────────────────────────────────────
# FULL P1 SIMULATION
# ──────────────────────────────────────────────────────────────────────

def run_p1_simulation():
    """Run all P1 BALANCE scenarios."""
    scenarios = []
    for wk in ALL_WEIGHTS_KG:
        for uk in USAGE_KEYS:
            for gk in GAIT_PHASE_KEYS:
                scenarios.append(run_scenario(wk, uk, gk))
    return scenarios


# ──────────────────────────────────────────────────────────────────────
# ANALYSIS
# ──────────────────────────────────────────────────────────────────────

def analyze_p1(scenarios):
    """Full analysis of P1 scenarios."""
    total = len(scenarios)
    pass_count = sum(1 for s in scenarios if s["status"] == "pass")
    revision_count = sum(1 for s in scenarios if s["status"] == "needs_revision")
    blocked_count = sum(1 for s in scenarios if s["status"] == "blocked")

    # Per-weight analysis
    weight_analysis = {}
    for wk in ALL_WEIGHTS_KG:
        wk_sc = [s for s in scenarios if s["weight_kg"] == wk]
        wk_pass = sum(1 for s in wk_sc if s["status"] == "pass")
        wk_rev = sum(1 for s in wk_sc if s["status"] == "needs_revision")
        wk_block = sum(1 for s in wk_sc if s["status"] == "blocked")
        avg_comfort = sum(s["scores"]["comfort_confidence"] for s in wk_sc) / len(wk_sc)
        avg_readiness = sum(s["scores"]["prototype_readiness"] for s in wk_sc) / len(wk_sc)

        # Worst zone across this weight's scenarios
        zone_risk_counts = {z: {"safe": 0, "warning": 0, "critical": 0} for z in ZONES}
        max_stress_zone = ""
        max_stress_val = 0
        max_fatigue_zone = ""
        max_fatigue_val = 0

        for s in wk_sc:
            for z in ZONES:
                zone_risk_counts[z][s["overload_risks"][z]] += 1
                if s["compressive_stresses_mpa"][z] > max_stress_val:
                    max_stress_val = s["compressive_stresses_mpa"][z]
                    max_stress_zone = f'{z}@{s["gait_phase"]}+{s["usage_mode"]}'
                if s["fatigue_probabilities"][z] > max_fatigue_val:
                    max_fatigue_val = s["fatigue_probabilities"][z]
                    max_fatigue_zone = f'{z}@{s["gait_phase"]}+{s["usage_mode"]}'

        weight_analysis[str(wk)] = {
            "total": len(wk_sc),
            "pass": wk_pass,
            "needs_revision": wk_rev,
            "blocked": wk_block,
            "pass_rate": round(wk_pass / len(wk_sc) * 100, 1),
            "avg_comfort_confidence": round(avg_comfort, 1),
            "avg_prototype_readiness": round(avg_readiness, 1),
            "zone_risk_summary": zone_risk_counts,
            "max_stress_zone": max_stress_zone,
            "max_stress_mpa": round(max_stress_val, 4),
            "max_fatigue_zone": max_fatigue_zone,
            "max_fatigue_probability": round(max_fatigue_val, 4),
        }

    # Gait phase analysis
    gait_analysis = {}
    for gk in GAIT_PHASE_KEYS:
        gk_sc = [s for s in scenarios if s["gait_phase"] == gk]
        avg_comfort = sum(s["scores"]["comfort_confidence"] for s in gk_sc) / len(gk_sc)
        avg_readiness = sum(s["scores"]["prototype_readiness"] for s in gk_sc) / len(gk_sc)
        critical_count = sum(
            1 for s in gk_sc
            for z in ZONES if s["overload_risks"][z] == "critical")
        gait_analysis[gk] = {
            "avg_comfort": round(avg_comfort, 1),
            "avg_readiness": round(avg_readiness, 1),
            "critical_zones": critical_count,
        }

    # Usage mode analysis
    usage_analysis = {}
    for uk in USAGE_KEYS:
        uk_sc = [s for s in scenarios if s["usage_mode"] == uk]
        avg_comfort = sum(s["scores"]["comfort_confidence"] for s in uk_sc) / len(uk_sc)
        avg_readiness = sum(s["scores"]["prototype_readiness"] for s in uk_sc) / len(uk_sc)
        usage_analysis[uk] = {
            "avg_comfort": round(avg_comfort, 1),
            "avg_readiness": round(avg_readiness, 1),
            "blocked_count": sum(1 for s in uk_sc if s["status"] == "blocked"),
        }

    # Density adjustment recommendations
    density_adjustments = {}
    for zone in ZONES:
        current = BALANCE_DENSITY[zone]
        # Find scenarios where this zone has warning/critical
        problem_scenarios = [
            s for s in scenarios
            if s["overload_risks"][zone] in ("warning", "critical")
            or s["compressive_stresses_mpa"][zone] > 8.0
        ]
        if problem_scenarios:
            # Calculate needed density increase
            worst_stress = max(s["compressive_stresses_mpa"][zone] for s in problem_scenarios)
            # Target: bring stress below 8 MPa threshold
            # stress = pressure / 1000 * (1/(density+0.1)) * stiffness
            # => density = 1 / (stress * 1000 / (pressure * stiffness)) - 0.1
            # Rough recommendation: increment by 0.05 per warning level
            max_weight = max(s["weight_kg"] for s in problem_scenarios)
            recommended = current
            if any(s["overload_risks"][zone] == "critical" for s in problem_scenarios):
                recommended = min(round(current + 0.12, 2), 0.95)
            elif worst_stress > 12:
                recommended = min(round(current + 0.10, 2), 0.95)
            elif worst_stress > 8:
                recommended = min(round(current + 0.05, 2), 0.95)
            else:
                recommended = min(round(current + 0.03, 2), 0.95)

            if recommended > current:
                density_adjustments[zone] = {
                    "current": current,
                    "recommended": recommended,
                    "change": round(recommended - current, 2),
                    "worst_stress_mpa": round(worst_stress, 4),
                    "worst_weight_kg": max_weight,
                    "problem_scenario_count": len(problem_scenarios),
                }

    # Overall P1 verdict
    overall_blocks = []
    for s in scenarios:
        overall_blocks.extend(s["hard_blocks"])

    unique_blocks = list(set(overall_blocks))

    if blocked_count == 0 and all(
            s["status"] == "pass"
            for s in scenarios if s["weight_kg"] == BASELINE_WEIGHT_KG):
        if max(s["scores"]["prototype_readiness"] for s in scenarios) >= 85:
            overall_verdict = "pass"
        else:
            overall_verdict = "needs_revision"
    elif blocked_count > total * 0.3:
        overall_verdict = "blocked"
    else:
        overall_verdict = "needs_revision"

    # Top risks
    top_risks = []
    risk_counter = {}
    for s in scenarios:
        for z in ZONES:
            if s["overload_risks"][z] in ("warning", "critical"):
                key = f'{z}_{s["overload_risks"][z]}_{s["usage_mode"]}_{s["gait_phase"]}'
                risk_counter[key] = risk_counter.get(key, 0) + 1
    for k, v in sorted(risk_counter.items(), key=lambda x: -x[1])[:8]:
        top_risks.append({"scenario": k, "occurrences": v})

    # Determine what to measure when printed
    measurement_instructions = _generate_measurement_instructions()

    avg_comfort_all = sum(s["scores"]["comfort_confidence"] for s in scenarios) / len(scenarios)
    avg_readiness_all = sum(s["scores"]["prototype_readiness"] for s in scenarios) / len(scenarios)

    return {
        "generated_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "edition": EDITION,
        "material": {
            "tpu_shore_a": TPU_HARNESS_SHORE_A,
            "gyroid_wall_thickness_mm": GYROID_WALL_THICKNESS_MM,
            "gyroid_cell_size_mm": GYROID_CELL_SIZE_MM,
            "compressive_strength_mpa": TPU_COMPRESSIVE_STRENGTH_MPA,
        },
        "density_map": dict(BALANCE_DENSITY),
        "stiffness_modifier": STIFFNESS_MODIFIER,
        "baseline_weight_kg": BASELINE_WEIGHT_KG,
        "stress_check_weights_kg": list(STRESS_CHECK_WEIGHTS_KG),
        "total_scenarios": total,
        "pass": pass_count,
        "needs_revision": revision_count,
        "blocked": blocked_count,
        "avg_comfort_confidence": round(avg_comfort_all, 1),
        "avg_prototype_readiness": round(avg_readiness_all, 1),
        "overall_verdict": overall_verdict,
        "per_weight": weight_analysis,
        "per_gait_phase": gait_analysis,
        "per_usage_mode": usage_analysis,
        "density_adjustments": density_adjustments,
        "top_risks": top_risks,
        "hard_blocks": unique_blocks,
        "measurement_instructions": measurement_instructions,
    }


def _generate_measurement_instructions():
    """List of what to measure and compare against simulation when P1 is printed."""
    return {
        "physical_dimensions": [
            "Overall insole length and width (compare to target size)",
            "Lattice wall thickness at 5+ points (target: 0.6 mm ± 0.1 mm)",
            "Cell size at 5+ points (target: 6.0 mm ± 0.5 mm)",
            "Total thickness at heel / midfoot / forefoot / toe zones",
        ],
        "mechanical_tests": [
            "Compression test at each zone: apply known force, measure displacement",
            "Compare measured displacement to simulation toe_displacement_mm",
            "Hardness test: Shore A durometer at heel and forefoot",
            "Repeated compression (1000 cycles): check for permanent set",
        ],
        "comfort_validation": [
            "Subjective comfort rating on 1-10 scale (engineering survey only)",
            "Pressure mapping under foot with in-shoe pressure sensor mat",
            "Compare measured pressure distribution to effective_pressures_kpa",
            "Note any zone where measured pressure differs > 30% from simulated",
        ],
        "fatigue_observation": [
            "Inspect for visible deformation after 1000 load cycles",
            "Check for crack initiation at strut junctions under magnification",
            "Record any permanent set height loss at each zone",
        ],
        "comparison_to_simulation": [
            "Compare measured zone pressures vs effective_pressures_kpa table",
            "Compare measured compressive displacement vs toe_displacement_mm",
            "Note which zones deviate most from simulation predictions",
            "Document environmental conditions (temperature, humidity) during test",
        ],
    }


# ──────────────────────────────────────────────────────────────────────
# REPORT GENERATION
# ──────────────────────────────────────────────────────────────────────

def generate_json_report(analysis):
    """Return analysis dict ready for JSON serialization."""
    return analysis


def generate_markdown_report(analysis):
    """Generate full engineering markdown report."""
    md = []
    md.append("# ZILFIT Prototype P1 — BALANCE Candidate")
    md.append("")
    md.append("## Engineering Simulation Report")
    md.append("")
    md.append(f"**Generated:** {analysis['generated_at']}")
    md.append(f"**Edition:** {analysis['edition']}")
    md.append(f"**Baseline Weight:** {analysis['baseline_weight_kg']} kg")
    md.append(f"**Stress Checks:** {','.join(str(w) for w in analysis['stress_check_weights_kg'])} kg")
    md.append(f"**Usage:** daily_walking + standing_long")
    md.append("")
    md.append("---")
    md.append("")
    md.append("*Engineering simulation only. No medical, diagnostic, therapeutic, clinical,*")
    md.append("*pain, disease, or treatment claims. All results are deterministic approximations.*")
    md.append("")
    md.append("## Material Parameters")
    md.append("")
    m = analysis["material"]
    md.append(f"- TPU Shore A: {m['tpu_shore_a']}")
    md.append(f"- Gyroid wall thickness: {m['gyroid_wall_thickness_mm']} mm")
    md.append(f"- Gyroid cell size: {m['gyroid_cell_size_mm']} mm")
    md.append(f"- Compressive strength: {m['compressive_strength_mpa']} MPa")
    md.append("")

    md.append("## Density Map")
    md.append("")
    md.append("| Zone | Density |")
    md.append("|---|---|")
    for zone, d in analysis["density_map"].items():
        md.append(f"| {zone} | {d:.2f} |")
    md.append("")

    md.append("## Overall Verdict")
    md.append("")
    md.append(f"**Verdict: {analysis['overall_verdict'].upper()}**")
    md.append("")
    md.append(f"- Total scenarios: {analysis['total_scenarios']}")
    md.append(f"- Pass: {analysis['pass']}")
    md.append(f"- Needs revision: {analysis['needs_revision']}")
    md.append(f"- Blocked: {analysis['blocked']}")
    md.append(f"- Avg comfort confidence: {analysis['avg_comfort_confidence']}")
    md.append(f"- Avg prototype readiness: {analysis['avg_prototype_readiness']}")
    md.append("")

    # Hard blocks
    if analysis["hard_blocks"]:
        md.append("## Hard Blocks")
        md.append("")
        for b in sorted(set(analysis["hard_blocks"])):
            md.append(f"- {b}")
        md.append("")

    md.append("## Per-Weight Analysis")
    md.append("")
    md.append("| Weight | Total | Pass | Revision | Blocked | Pass Rate % | Avg Comfort | Avg Readiness |")
    md.append("|---|---|---|---|---|---|---|---|")
    for wk, wa in analysis["per_weight"].items():
        md.append(f"| {wk} kg | {wa['total']} | {wa['pass']} | {wa['needs_revision']} | {wa['blocked']} | {wa['pass_rate']} | {wa['avg_comfort_confidence']} | {wa['avg_prototype_readiness']} |")
    md.append("")

    md.append("## Per-Gait-Phase Analysis")
    md.append("")
    md.append("| Phase | Avg Comfort | Avg Readiness | Critical Zones |")
    md.append("|---|---|---|---|")
    for gk, ga in analysis["per_gait_phase"].items():
        md.append(f"| {gk} | {ga['avg_comfort']} | {ga['avg_readiness']} | {ga['critical_zones']} |")
    md.append("")

    md.append("## Per-Usage Analysis")
    md.append("")
    md.append("| Usage | Avg Comfort | Avg Readiness | Blocked |")
    md.append("|---|---|---|---|")
    for uk, ua in analysis["per_usage_mode"].items():
        md.append(f"| {uk} | {ua['avg_comfort']} | {ua['avg_readiness']} | {ua['blocked_count']} |")
    md.append("")

    md.append("## Density Adjustments Needed")
    md.append("")
    if analysis["density_adjustments"]:
        md.append("| Zone | Current | Recommended | Change | Worst Stress (MPa) |")
        md.append("|---|---|---|---|---|")
        for zone, adj in analysis["density_adjustments"].items():
            md.append(f"| {zone} | {adj['current']:.2f} | {adj['recommended']:.2f} | +{adj['change']:.2f} | {adj['worst_stress_mpa']} |")
    else:
        md.append("*No density adjustments needed.*")
    md.append("")

    md.append("## Top Risks")
    md.append("")
    if analysis["top_risks"]:
        md.append("| # | Risk Scenario | Occurrences |")
        md.append("|---|---|---|")
        for i, r in enumerate(analysis["top_risks"], 1):
            md.append(f"| {i} | {r['scenario']} | {r['occurrences']} |")
    else:
        md.append("*No overload risks detected.*")
    md.append("")

    md.append("## What to Measure When Printed")
    md.append("")
    mi = analysis["measurement_instructions"]
    for section, items in mi.items():
        md.append(f"### {section.replace('_', ' ').title()}")
        for item in items:
            md.append(f"- {item}")
        md.append("")

    md.append("## Simulation Constants")
    md.append("")
    md.append(f"- Contact areas (cm²): heel={CONTACT_AREA_CM2['heel']}, midfoot={CONTACT_AREA_CM2['midfoot']}, forefoot={CONTACT_AREA_CM2['forefoot']}, toe={CONTACT_AREA_CM2['toe']}")
    md.append(f"- Gait phases: {', '.join(GAIT_PHASE_KEYS)}")
    md.append(f"- Usage modes: {', '.join(USAGE_KEYS)}")
    md.append(f"- Dynamic factors: walking={USAGE_MODES['daily_walking']['dynamic_factor']}, standing={USAGE_MODES['standing_long']['dynamic_factor']}")
    md.append(f"- Cycles/day: walking={USAGE_MODES['daily_walking']['cycles_per_day']}, standing={USAGE_MODES['standing_long']['cycles_per_day']}")
    md.append("")
    md.append("---")
    md.append("*Report generated by zilfit_p1_balance_candidate.py — stdlib only, local only.*")

    return "\n".join(md)


# ──────────────────────────────────────────────────────────────────────
# MAIN
# ──────────────────────────────────────────────────────────────────────

def main():
    base = Path(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    report_dir = base / "reports" / "prototypes"
    report_dir.mkdir(parents=True, exist_ok=True)

    n = len(ALL_WEIGHTS_KG) * len(USAGE_KEYS) * len(GAIT_PHASE_KEYS)
    print(f"ZILFIT Prototype P1 — BALANCE Candidate")
    print(f"Scenarios: {len(ALL_WEIGHTS_KG)} weights × {len(USAGE_KEYS)} modes × "
          f"{len(GAIT_PHASE_KEYS)} phases = {n}")
    print()

    print("Running simulation...")
    scenarios = run_p1_simulation()
    print(f"  {len(scenarios)} scenarios completed.")
    print()

    print("Analyzing results...")
    analysis = analyze_p1(scenarios)
    print(f"  Total:  {analysis['total_scenarios']}")
    print(f"  Pass:   {analysis['pass']}")
    print(f"  Revise: {analysis['needs_revision']}")
    print(f"  Blocked:{analysis['blocked']}")
    print(f"  Verdict:{analysis['overall_verdict'].upper()}")
    print(f"  Comfort:{analysis['avg_comfort_confidence']:.1f}")
    print(f"  Ready: {analysis['avg_prototype_readiness']:.1f}")
    print()

    # Per-weight summary
    for wk, wa in analysis["per_weight"].items():
        print(f"  {wk} kg: pass_rate={wa['pass_rate']}% comfort={wa['avg_comfort_confidence']} "
              f"readiness={wa['avg_prototype_readiness']} "
              f"max_stress={wa['max_stress_zone']}({wa['max_stress_mpa']} MPa) "
              f"max_fatigue={wa['max_fatigue_zone']}({wa['max_fatigue_probability']})")
    print()

    # Density adjustments
    if analysis["density_adjustments"]:
        print("  Density adjustments recommended:")
        for zone, adj in analysis["density_adjustments"].items():
            print(f"    {zone}: {adj['current']:.2f} → {adj['recommended']:.2f} "
                  f"(+{adj['change']:.2f}) worst={adj['worst_stress_mpa']} MPa")
    else:
        print("  No density adjustments needed.")
    print()

    # Top risks
    if analysis["top_risks"]:
        print("  Top risks:")
        for r in analysis["top_risks"][:5]:
            print(f"    {r['occurrences']}x  {r['scenario']}")
    else:
        print("  No overload risks detected.")
    print()

    # Write JSON
    json_path = report_dir / "p1_balance_candidate.json"
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(analysis, f, indent=2, ensure_ascii=False, default=str)
    print(f"JSON: {json_path}")

    # Write Markdown
    md_path = report_dir / "p1_balance_candidate.md"
    md_text = generate_markdown_report(analysis)
    with open(md_path, "w", encoding="utf-8") as f:
        f.write(md_text)
    print(f"Markdown: {md_path}")

    print()
    print(f"P1 VERDICT: {analysis['overall_verdict'].upper()}")
    if analysis["overall_verdict"] == "pass":
        print("P1 is ready for first physical sample.")
    elif analysis["overall_verdict"] == "needs_revision":
        print("P1 needs density revision before physical sample.")
    else:
        print("P1 is BLOCKED — do not proceed to physical sample.")

    return analysis


if __name__ == "__main__":
    main()

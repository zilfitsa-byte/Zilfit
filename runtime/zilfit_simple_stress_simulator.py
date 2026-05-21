#!/usr/bin/env python3
"""
ZILFIT Simple Local Stress Simulator
=====================================
ENGINEERING SIMULATION ONLY — NO MEDICAL CLAIMS
Deterministic, local, zero-dependency stress analysis for ZILFIT editions.

Simulates:
  - Heel / midfoot / forefoot / toe load distribution across gyroid TPU lattice
  - Density map application per edition
  - Compression risk estimation
  - Overload zone detection
  - Fatigue probability (daily cadence, walking usage)
  - Prototype readiness ranking

Editions:   CALM, VITAL, FOCUS, BALANCE, FEMME
Weights:    95 kg, 110 kg, 125 kg
Usage:      Walking, daily cadence, normal arch, TPU gyroid lattice
"""

import json
import math
import os
from datetime import datetime
from pathlib import Path

# ──────────────────────────────────────────────────────────────────────
# CONSTANTS — TPU gyroid lattice engineering parameters
# ──────────────────────────────────────────────────────────────────────

# TPU 75A-80A Shore hardness (from knowledge base)
TPU_HARNESS_SHORE_A = 78  # midpoint of 75-80A range

# Gyroid cell size 0.6 mm wall thickness (from knowledge base)
GYROID_WALL_THICKNESS_MM = 0.6
GYROID_CELL_SIZE_MM = 6.0

# TPU compressive strength reference (MPa) — engineering reference range
TPU_COMPRESSIVE_STRENGTH_MPA = 35.0  # conservative reference for 75A-80A TPU

# Spinal stress constraint (MPa) — from knowledge base
MAX_SPINAL_STRESS_MPA = 0.9

# Heel pressure reference range (kPa) — from knowledge base
HEEL_PRESSURE_MIN_KPA = 120
HEEL_PRESSURE_MAX_KPA = 180

# ──────────────────────────────────────────────────────────────────────
# EDITION DEFINITIONS
# Each edition has a relative density multiplier (0.0-1.0) applied to
# the base gyroid lattice.  Higher density = more material = stiffer.
#
# Density per region [heel, midfoot, forefoot, toe]:
#   CALM   — comfort-focused, higher heel cushion
#   VITAL  — energy-return focused, stiffer forefoot
#   FOCUS  — stability-focused, stiff midfoot
#   BALANCE — even distribution across all zones
#   FEMME  — lightweight, refined profile
# ──────────────────────────────────────────────────────────────────────

EDITIONS = {
    "CALM": {
        "description": "Comfort-optimized, higher heel cushioning",
        "density": {
            "heel": 0.35,       # softer heel for shock absorption
            "midfoot": 0.45,
            "forefoot": 0.40,
            "toe": 0.30,
        },
        "stiffness_modifier": 0.92,  # slightly softer overall
    },
    "VITAL": {
        "description": "Energy-return, responsive forefoot",
        "density": {
            "heel": 0.40,
            "midfoot": 0.45,
            "forefoot": 0.60,       # stiff forefoot for push-off rebound
            "toe": 0.40,
        },
        "stiffness_modifier": 1.08,
    },
    "FOCUS": {
        "description": "Stability-focused arch support",
        "density": {
            "heel": 0.45,
            "midfoot": 0.70,       # reinforced midfoot for arch control
            "forefoot": 0.50,
            "toe": 0.40,
        },
        "stiffness_modifier": 1.12,
    },
    "BALANCE": {
        "description": "Even distribution across all zones",
        "density": {
            "heel": 0.50,
            "midfoot": 0.50,
            "forefoot": 0.50,
            "toe": 0.50,
        },
        "stiffness_modifier": 1.0,
    },
    "FEMME": {
        "description": "Lightweight refined profile",
        "density": {
            "heel": 0.32,          # lower density for lighter feel
            "midfoot": 0.38,
            "forefoot": 0.35,
            "toe": 0.28,
        },
        "stiffness_modifier": 0.88,
    },
}

# ──────────────────────────────────────────────────────────────────────
# WEIGHT SCENARIOS
# ──────────────────────────────────────────────────────────────────────

WEIGHTS_KG = [95, 110, 125]

# Walking gait load distribution (proportion of body weight on each zone).
# These are engineering approximations for mid-stance walking cadence.
WALKING_LOAD_FRACTION = {
    "heel": 0.40,       # heel strike absorbs ~40% body weight
    "midfoot": 0.15,    # arch transition carries ~15%
    "forefoot": 0.30,   # push-off zone carries ~30%
    "toe": 0.15,        # toe-off carries ~15%
}

# Contact area per zone (cm²) — engineering estimate normal arch
CONTACT_AREA_CM2 = {
    "heel": 28.0,
    "midfoot": 18.0,
    "forefoot": 35.0,
    "toe": 12.0,
}

ZONES = ["heel", "midfoot", "forefoot", "toe"]

# ──────────────────────────────────────────────────────────────────────
# SIMULATION ENGINE
# ──────────────────────────────────────────────────────────────────────


def compute_zone_pressure(body_weight_kg, zone, density):
    """
    Compute estimated pressure (kPa) on a given zone.

    Formula:
      force_N = body_weight_kg * g * zone_fraction
      effective_area = contact_area * density_factor
        where density_factor reduces area as density increases
        (denser lattice spreads load more efficiently)
      pressure_kPa = (force_N / effective_area_cm2) * 10
    """
    g = 9.81
    fraction = WALKING_LOAD_FRACTION[zone]
    force_n = body_weight_kg * g * fraction

    # Gyroid lattice density increases effective load-spreading area
    # Low density = less area utilization; high density = up to 2x spreading
    area_multiplier = 1.0 + density * 0.8
    effective_area_cm2 = CONTACT_AREA_CM2[zone] * area_multiplier

    pressure_kpa = (force_n / effective_area_cm2) * 10.0  # convert to kPa (1 kPa = 10 N/m²)

    return round(pressure_kpa, 2)


def compute_compression_stress(pressure_kpa, density, stiffness_modifier):
    """
    Estimate local compressive stress (MPa) within the gyroid cell wall.
    
    The stress in the lattice strut is amplified above the nominal pressure
    due to the geometry of the gyroid.  The amplification factor depends on
    density:
      - Low density → fewer struts sharing the load → higher stress per strut
      - High density → more struts → lower stress per strut
    
    A simplified strut stress factor:  stress_factor = 1 / (density + 0.1)
    Then: stress_MPa = (pressure_kpa / 1000) * stress_factor * stiffness_modifier
    
    This accounts for the fact that stiffer editions transmit more load
    directly through the lattice without dissipation.
    """
    stress_factor = 1.0 / (density + 0.1)
    compression_mpa = (pressure_kpa / 1000.0) * stress_factor * stiffness_modifier
    return round(compression_mpa, 4)


def estimate_overload_risk(compression_mpa, pressure_kpa, zone, edition):
    """
    Determine overload risk for a zone.
    
    Three failure modes:
      1. Pressure exceeds TPU deformation threshold for comfort
      2. Compression stress approaches TPU yield
      3. Zone-specific engineering limits exceeded

    Returns risk level: 'safe', 'warning', 'critical'
    """
    # Zone-specific engineering thresholds
    thresholds = {
        "heel": {
            "pressure_warning_kpa": HEEL_PRESSURE_MAX_KPA * 1.3,   # ~234 kPa
            "stress_warning_mpa": TPU_COMPRESSIVE_STRENGTH_MPA * 0.4,  # ~14 MPa
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

    th = thresholds[zone]
    overload_score = 0.0

    # Pressure ratio relative to warning threshold
    pressure_ratio = pressure_kpa / th["pressure_warning_kpa"]
    if pressure_ratio > 1.0:
        overload_score += 0.6
    elif pressure_ratio > 0.8:
        overload_score += 0.3

    # Stress ratio relative to warning threshold (safety factor of ~2.5 applied)
    stress_ratio = compression_mpa / th["stress_warning_mpa"]
    if stress_ratio > 1.0:
        overload_score += 0.5
    elif stress_ratio > 0.7:
        overload_score += 0.25

    if overload_score >= 0.9:
        return "critical"
    elif overload_score >= 0.4:
        return "warning"
    return "safe"


def estimate_fatigue_probability(compression_mpa, cycles_per_day=8000):
    """
    Estimate fatigue probability for daily walking cadence (~8000 steps/day).

    S-N curve approximation for elastomeric TPU:
      - Below 10% of compressive strength: negligible fatigue risk
      - 10-30%: low risk over 10^6 cycles
      - 30-60%: moderate risk
      - Above 60%: high risk of permanent deformation < 10^5 cycles
    
    Fatigue exponent for TPU: ~6 (material property)
    """
    strength_ratio = compression_mpa / TPU_COMPRESSIVE_STRENGTH_MPA
    
    # S-N curve: N = N0 * (stress_ratio / ref)^(-exponent)
    # ref ≈ 0.4 at 10^6 cycles for TPU
    ref_ratio = 0.4
    exponent = 6.0
    
    if strength_ratio <= 0.05:
        return 0.001  # negligible
    elif strength_ratio < 0.1:
        return 0.01
    
    # Estimated cycles to failure
    n_ref = 1_000_000
    n_failure = n_ref * (strength_ratio / ref_ratio) ** (-exponent)
    
    # Daily cycles vs failure threshold
    annual_cycles = cycles_per_day * 365
    damage_ratio = annual_cycles / n_failure
    
    # Fatigue probability = 1 - exp(-damage_ratio)
    fatigue_prob = 1.0 - math.exp(-damage_ratio)
    
    return min(round(fatigue_prob, 4), 0.99)  # cap at 99%


def compute_comfort_confidence(overload_map, stress_map, edition_density):
    """
    Compute a 0-100 comfort confidence score.
    
    Factors:
      - Lower overload → higher score
      - Stress below TPU comfort zone → higher score
      - Balanced density distribution → higher score
    """
    score = 100.0

    # Penalty for each zone with warnings/critical overload
    for zone, risk in overload_map.items():
        if risk == "warning":
            score -= 10.0
        elif risk == "critical":
            score -= 20.0

    # Penalty for high stress zones
    for zone, stress in stress_map.items():
        if stress > 15.0:  # MPa
            score -= 5.0
        if stress > 25.0:
            score -= 10.0

    # Penalty for density imbalance (standard deviation)
    density_values = list(edition_density.values())
    mean_d = sum(density_values) / len(density_values)
    variance = sum((d - mean_d) ** 2 for d in density_values) / len(density_values)
    std_dev = math.sqrt(variance)
    
    # High imbalance penalizes comfort (uneven cushioning feel)
    if std_dev > 0.20:
        score -= 8.0
    
    return max(round(score, 1), 0.0)


def evaluate_prototype_status(overall_risk, fatigue_max, comfort_score):
    """
    Determine pass/needs_revision/blocked status.
    
    - pass:       no critical zones, low fatigue, reasonable comfort
    - needs_revision: warning zones or moderate fatigue
    - blocked:    critical overload or high fatigue probability
    """
    if overall_risk == "critical" or fatigue_max > 0.7:
        return "blocked"
    elif overall_risk == "warning" or fatigue_max > 0.3:
        return "needs_revision"
    else:
        return "pass"


# ──────────────────────────────────────────────────────────────────────
# MAIN SIMULATION
# ──────────────────────────────────────────────────────────────────────

def run_simulation():
    """Run the full simulation across all editions and weights."""
    print("=" * 70)
    print("  ZILFIT Simple Stress Simulator — Engineering Simulation")
    print("  Deterministic, local, zero-dependency analysis")
    print("=" * 70)
    print()

    all_results = []

    for edition_name, edition_data in EDITIONS.items():
        print(f"  Testing Edition: {edition_name}")
        print(f"  Description: {edition_data['description']}")

        edition_results = {
            "edition": edition_name,
            "description": edition_data["description"],
            "density_map": edition_data["density"],
            "stiffness_modifier": edition_data["stiffness_modifier"],
            "weight_scenarios": [],
        }

        for weight_kg in WEIGHTS_KG:
            print(f"    └── Weight: {weight_kg} kg")

            zone_data = {}
            worst_overload = "safe"
            max_fatigue_prob = 0.0
            worst_zone = None

            for zone in ZONES:
                density = edition_data["density"][zone]
                
                # Compute pressure
                pressure_kpa = compute_zone_pressure(weight_kg, zone, density)
                
                # Compute compression stress in lattice strut
                compression_mpa = compute_compression_stress(
                    pressure_kpa, density, edition_data["stiffness_modifier"]
                )
                
                # Estimate overload risk
                risk = estimate_overload_risk(
                    compression_mpa, pressure_kpa, zone, edition_name
                )
                
                # Estimate fatigue probability (daily walking ~8000 steps)
                fatigue_prob = estimate_fatigue_probability(compression_mpa)
                
                # Track worst-case
                if risk == "critical":
                    worst_overload = "critical"
                    worst_zone = zone
                elif risk == "warning" and worst_overload != "critical":
                    worst_overload = "warning"
                    worst_zone = zone
                
                max_fatigue_prob = max(max_fatigue_prob, fatigue_prob)

                zone_data[zone] = {
                    "density": density,
                    "pressure_kpa": pressure_kpa,
                    "compression_stress_mpa": compression_mpa,
                    "overload_risk": risk,
                    "fatigue_probability": fatigue_prob,
                    "load_fraction": WALKING_LOAD_FRACTION[zone],
                    "contact_area_cm2": CONTACT_AREA_CM2[zone],
                }

                risk_icon = {"safe": "✓", "warning": "⚠", "critical": "✗"}[risk]
                print(f"        {zone:10s}: {pressure_kpa:7.1f} kPa  |  "
                      f"stress {compression_mpa:.3f} MPa  |  "
                      f"risk {risk_icon} {risk:8s}  |  "
                      f"fatigue {fatigue_prob:.3f}")

            # Compute overall comfort confidence
            stress_map = {z: zone_data[z]["compression_stress_mpa"] for z in ZONES}
            overload_map = {z: zone_data[z]["overload_risk"] for z in ZONES}
            comfort_score = compute_comfort_confidence(
                overload_map, stress_map, edition_data["density"]
            )

            # Determine prototype status
            status = evaluate_prototype_status(
                worst_overload, max_fatigue_prob, comfort_score
            )

            weight_scenario = {
                "weight_kg": weight_kg,
                "zones": zone_data,
                "worst_overload": worst_overload,
                "worst_zone": worst_zone,
                "max_fatigue_probability": round(max_fatigue_prob, 4),
                "comfort_confidence": comfort_score,
                "prototype_status": status,
            }
            edition_results["weight_scenarios"].append(weight_scenario)

        # Compute aggregate comfort across weights for edition ranking
        avg_comfort = sum(
            s["comfort_confidence"] for s in edition_results["weight_scenarios"]
        ) / len(edition_results["weight_scenarios"])
        edition_results["avg_comfort_confidence"] = round(avg_comfort, 1)
        
        # Overall status (worst across weights)
        statuses = [s["prototype_status"] for s in edition_results["weight_scenarios"]]
        if "blocked" in statuses:
            edition_results["overall_status"] = "blocked"
        elif "needs_revision" in statuses:
            edition_results["overall_status"] = "needs_revision"
        else:
            edition_results["overall_status"] = "pass"

        all_results.append(edition_results)
        print()

    return all_results


# ──────────────────────────────────────────────────────────────────────
# REPORT GENERATION
# ──────────────────────────────────────────────────────────────────────

def generate_summary_and_recommendations(results):
    """
    Analyze all results and produce actionable recommendations.
    Returns a summary dict with rankings, best/worst edition, and adjustments.
    """
    summary = {
        "generated_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "editions_tested": list(EDITIONS.keys()),
        "weights_tested_kg": WEIGHTS_KG,
        "assumptions": {
            "usage": "walking",
            "cadence": "daily (~8000 steps)",
            "arch_type": "normal arch",
            "material": "TPU gyroid lattice 0.6mm wall / 6mm cell",
            "shore_hardness": f"75A-80A (midpoint: {TPU_HARNESS_SHORE_A}A)",
        },
        "edition_ranking": [],
        "best_edition": None,
        "worst_edition": None,
        "density_adjustments": {},
        "prototype_readiness": {},
        "risks_detected": [],
    }

    # Rank editions by average comfort confidence (descending)
    ranked = sorted(
        results, key=lambda r: r["avg_comfort_confidence"], reverse=True
    )
    
    for rank, edition in enumerate(ranked, 1):
        name = edition["edition"]
        summary["edition_ranking"].append({
            "rank": rank,
            "edition": name,
            "avg_comfort": edition["avg_comfort_confidence"],
            "overall_status": edition["overall_status"],
        })
        summary["prototype_readiness"][name] = edition["overall_status"]

    summary["best_edition"] = ranked[0]["edition"]
    summary["worst_edition"] = ranked[-1]["edition"]

    # Detect risks across all scenarios
    for edition in results:
        for scenario in edition["weight_scenarios"]:
            for zone, zdata in scenario["zones"].items():
                if zdata["overload_risk"] in ("warning", "critical"):
                    summary["risks_detected"].append({
                        "edition": edition["edition"],
                        "weight_kg": scenario["weight_kg"],
                        "zone": zone,
                        "risk": zdata["overload_risk"],
                        "pressure_kpa": zdata["pressure_kpa"],
                        "stress_mpa": zdata["compression_stress_mpa"],
                        "fatigue_probability": zdata["fatigue_probability"],
                    })

    # Generate density adjustment recommendations per edition
    for edition in results:
        name = edition["edition"]
        adj = {"edition": name, "recommendations": []}
        
        for scenario in edition["weight_scenarios"]:
            weight = scenario["weight_kg"]
            for zone, zdata in scenario["zones"].items():
                if zdata["overload_risk"] == "critical":
                    current_d = zdata["density"]
                    recommended_d = min(round(current_d + 0.10, 2), 0.95)
                    adj["recommendations"].append({
                        "weight_kg": weight,
                        "zone": zone,
                        "current_density": current_d,
                        "recommended_density": recommended_d,
                        "reason": (
                            f"Critical overload risk in {zone} at {weight}kg. "
                            f"Increase lattice density from {current_d} to {recommended_d} "
                            f"to distribute load across more struts."
                        ),
                    })
                elif zdata["overload_risk"] == "warning":
                    current_d = zdata["density"]
                    recommended_d = min(round(current_d + 0.05, 2), 0.90)
                    adj["recommendations"].append({
                        "weight_kg": weight,
                        "zone": zone,
                        "current_density": current_d,
                        "recommended_density": recommended_d,
                        "reason": (
                            f"Warning-level stress in {zone} at {weight}kg. "
                            f"Consider increasing lattice density from {current_d} to {recommended_d}."
                        ),
                    })
        
        # Deduplicate recommendations by max suggested density per zone
        if adj["recommendations"]:
            # Keep only the highest weight recommendation per zone
            zone_recs = {}
            for rec in adj["recommendations"]:
                z = rec["zone"]
                if z not in zone_recs or rec["weight_kg"] > zone_recs[z]["weight_kg"]:
                    zone_recs[z] = rec
            adj["recommendations"] = list(zone_recs.values())
        
        summary["density_adjustments"][name] = adj

    # Determine recommended first prototype
    # Best edition that is not blocked at any weight
    for edition in ranked:
        if edition["overall_status"] == "pass":
            summary["recommended_first_prototype"] = edition["edition"]
            break
    else:
        # If nothing passes, recommend the least-bad
        summary["recommended_first_prototype"] = ranked[0]["edition"]
        summary["recommended_first_prototype_note"] = (
            f"No edition shows full 'pass' status across all weights. "
            f"{ranked[0]['edition']} has the highest comfort confidence "
            f"and should be prioritized for physical prototype iteration."
        )

    return summary


def render_terminal_table(results):
    """
    Render a comprehensive ASCII table for terminal display.
    """
    width = 80

    def separator(char="─"):
        return "┌" + char * (width - 2) + "┐"

    def hr(char="─"):
        return "├" + char * (width - 2) + "┤"

    def content_row(text, indent=2):
        padded = "│" + " " * indent + text.ljust(width - 2 - indent) + "│"
        return padded

    lines = []

    # Header
    lines.append(separator())
    lines.append(content_row("ZILFIT STRESS SIMULATION — PROTOTYPE READINESS REPORT"))
    lines.append(content_row(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"))
    lines.append(content_row(f"Material: TPU Gyroid | Wall: {GYROID_WALL_THICKNESS_MM}mm | Cell: {GYROID_CELL_SIZE_MM}mm"))
    lines.append(content_row(f"Shore: {TPU_HARNESS_SHORE_A}A | Walking cadence | Normal arch"))
    lines.append(separator())
    lines.append("")

    # Per-edition per-weight table
    edition_headers = ["Edition / Weight"]
    for zone in ZONES:
        edition_headers.append(f"{zone} P(kPa)")
        edition_headers.append(f"{zone} Stress")
        edition_headers.append(f"{zone} Risk")

    # Column widths: first col=22, rest=10 each
    col_widths = [22] + [10] * (3 * len(ZONES))
    # Recalculate total width
    total_w = sum(col_widths) + len(col_widths) + 1
    
    col_widths = [22] + [12] * (3 * len(ZONES))
    total_w = sum(col_widths) + len(col_widths) + 1

    def make_row(vals):
        parts = []
        for v, w in zip(vals, col_widths):
            parts.append(str(v)[:w].ljust(w))
        return "│" + "│".join(parts) + "│"

    def make_sep():
        return "├" + "┼".join("─" * w for w in col_widths) + "┤"

    # Table header
    lines.append("┌" + "┬".join("─" * w for w in col_widths) + "┐")
    
    header_vals = []
    for zone in ZONES:
        header_vals.extend([f"{zone.capitalize()} P(kPa)", f"{zone.capitalize()} Stress", f"{zone.capitalize()} Risk"])
    header_vals = ["Edition / Weight"] + header_vals
    # Truncate header values to fit
    header_vals = [h[:col_widths[i]] for i, h in enumerate(header_vals)]
    lines.append(make_row(header_vals))
    
    for edition in results:
        name = edition["edition"]
        for scenario in edition["weight_scenarios"]:
            row_vals = [f"{name} ({scenario['weight_kg']}kg)"]
            for zone in ZONES:
                zd = scenario["zones"][zone]
                row_vals.append(f"{zd['pressure_kpa']:.1f}")
                row_vals.append(f"{zd['compression_stress_mpa']:.3f}")
                risk_char = {"safe": "safe", "warning": "WARN", "critical": "CRIT"}[zd["overload_risk"]]
                row_vals.append(risk_char)
            lines.append(make_row(row_vals))
        lines.append(make_sep())

    lines.append("")

    # Summary section
    summary = generate_summary_and_recommendations(results)

    lines.append(separator())
    lines.append(content_row("SUMMARY"))
    lines.append(separator())
    lines.append("")

    lines.append("┌" + "─" * (width - 2) + "┐")
    lines.append(content_row(f"Best Edition:        {summary['best_edition']}"))
    lines.append(content_row(f"Worst Edition:       {summary['worst_edition']}"))
    lines.append(content_row(f"Risks Detected:      {len(summary['risks_detected'])}"))
    lines.append(content_row(f"Recommended First Prototype: {summary['recommended_first_prototype']}"))
    lines.append("└" + "─" * (width - 2) + "┘")
    lines.append("")

    # Edition ranking
    lines.append("Edition Ranking (by average comfort confidence):")
    for item in summary["edition_ranking"]:
        lines.append(
            f"  #{item['rank']}  {item['edition']:10s}  "
            f"comfort {item['avg_comfort']:5.1f}  "
            f"status: {item['overall_status']}"
        )
    lines.append("")

    # Risk details
    if summary["risks_detected"]:
        lines.append("Risk Details:")
        for risk in summary["risks_detected"]:
            lines.append(
                f"  ✗ {risk['edition']} @ {risk['weight_kg']}kg  "
                f"zone={risk['zone']}  "
                f"risk={risk['risk']}  "
                f"pressure={risk['pressure_kpa']} kPa  "
                f"stress={risk['stress_mpa']} MPa"
            )
        lines.append("")

    # Density adjustments
    for edition_name, adj in summary["density_adjustments"].items():
        if adj["recommendations"]:
            lines.append(f"Density Adjustments — {edition_name}:")
            for rec in adj["recommendations"]:
                lines.append(
                    f"  {rec['zone']:10s}: {rec['current_density']} → {rec['recommended_density']} "
                    f"(weight {rec['weight_kg']}kg)"
                )
            lines.append("")

    return "\n".join(lines)


def generate_markdown_report(results, summary):
    """Generate a human-readable Markdown report."""
    lines = []
    lines.append("# ZILFIT Stress Simulation Report")
    lines.append("")
    lines.append(f"**Generated:** {summary['generated_at']}")
    lines.append(f"**Type:** Engineering Simulation — Local / Deterministic / Zero-Dependency")
    lines.append("")
    lines.append("## Material Parameters")
    lines.append("")
    lines.append(f"| Parameter | Value |")
    lines.append(f"|---|---|")
    lines.append(f"| Material | TPU Gyroid Lattice |")
    lines.append(f"| Shore Hardness | 75A-80A (midpoint: {TPU_HARNESS_SHORE_A}A) |")
    lines.append(f"| Wall Thickness | {GYROID_WALL_THICKNESS_MM}mm |")
    lines.append(f"| Cell Size | {GYROID_CELL_SIZE_MM}mm |")
    lines.append(f"| Compressive Strength (ref) | {TPU_COMPRESSIVE_STRENGTH_MPA} MPa |")
    lines.append(f"| Usage | Walking, daily cadence (~8000 steps/day) |")
    lines.append(f"| Arch Type | Normal arch |")
    lines.append(f"| Weight Scenarios | {WEIGHTS_KG} kg |")
    lines.append("")
    lines.append("## Simulation Methodology")
    lines.append("")
    lines.append("1. **Pressure Distribution:** Estimate zone pressure using body weight,")
    lines.append("   gait load fractions, and contact area with density-based spreading factor.")
    lines.append("2. **Compression Stress:** Estimate lattice strut stress using density-dependent")
    lines.append("   amplification factor and edition stiffness modifier.")
    lines.append("3. **Overload Risk:** Compare stress and pressure against TPU engineering")
    lines.append("   thresholds and zone-specific safety factors.")
    lines.append("4. **Fatigue Probability:** S-N curve approximation for elastomeric TPU,")
    lines.append("   estimating annual stress cycles vs. failure threshold.")
    lines.append("5. **Comfort Confidence:** Composite score (0-100) penalizing overload zones,")
    lines.append("   high stress, and density imbalance.")
    lines.append("6. **Prototype Status:** pass / needs_revision / blocked based on aggregate metrics.")
    lines.append("")
    lines.append("## Edition Results")
    lines.append("")

    for edition in results:
        name = edition["edition"]
        lines.append(f"### {name}")
        lines.append(f"*{edition['description']}*")
        lines.append("")
        lines.append(f"**Overall Status:** `{edition['overall_status']}`  |  **Avg Comfort:** {edition['avg_comfort_confidence']}/100")
        lines.append("")

        for scenario in edition["weight_scenarios"]:
            weight = scenario["weight_kg"]
            lines.append(f"#### {weight} kg")
            lines.append(f"- **Status:** `{scenario['prototype_status']}`  |  **Comfort:** {scenario['comfort_confidence']}/100  |  **Max Fatigue:** {scenario['max_fatigue_probability']:.4f}")
            if scenario["worst_zone"]:
                lines.append(f"- **Worst Zone:** {scenario['worst_zone']} ({scenario['worst_overload']})")
            lines.append("")
            lines.append("| Zone | Density | Pressure (kPa) | Stress (MPa) | Risk | Fatigue |")
            lines.append("|---|---|---|---|---|---|")
            for zone in ZONES:
                zd = scenario["zones"][zone]
                lines.append(
                    f"| {zone} | {zd['density']:.2f} | {zd['pressure_kpa']:.1f} | "
                    f"{zd['compression_stress_mpa']:.3f} | {zd['overload_risk']} | "
                    f"{zd['fatigue_probability']:.4f} |"
                )
            lines.append("")
        lines.append("---")
        lines.append("")

    lines.append("\n## Summary\n")
    lines.append(f"- **Best Edition:** {summary['best_edition']}")
    lines.append(f"- **Worst Edition:** {summary['worst_edition']}")
    lines.append(f"- **Risks Detected:** {len(summary['risks_detected'])}")
    lines.append(f"- **Recommended First Prototype:** {summary['recommended_first_prototype']}")
    lines.append("")

    lines.append("### Edition Ranking\n")
    lines.append("| Rank | Edition | Avg Comfort | Status |")
    lines.append("|---|---|---|---|")
    for item in summary["edition_ranking"]:
        lines.append(f"| #{item['rank']} | {item['edition']} | {item['avg_comfort']:.1f} | {item['overall_status']} |")
    lines.append("")

    if summary["risks_detected"]:
        lines.append("### Risk Details\n")
        lines.append("| Edition | Weight (kg) | Zone | Risk | Pressure (kPa) | Stress (MPa) | Fatigue |")
        lines.append("|---|---|---|---|---|---|---|")
        for risk in summary["risks_detected"]:
            lines.append(
                f"| {risk['edition']} | {risk['weight_kg']} | {risk['zone']} | "
                f"{risk['risk']} | {risk['pressure_kpa']} | {risk['stress_mpa']} | "
                f"{risk['fatigue_probability']} |"
            )
        lines.append("")

    lines.append("### Recommended Density Adjustments\n")
    for edition_name, adj in summary["density_adjustments"].items():
        if adj["recommendations"]:
            lines.append(f"#### {edition_name}")
            lines.append("")
            for rec in adj["recommendations"]:
                lines.append(f"- **{rec['zone']}** ({rec['weight_kg']}kg): "
                           f"density {rec['current_density']} → {rec['recommended_density']}")
                lines.append(f"  - *Reason:* {rec['reason']}")
            lines.append("")

    if "recommended_first_prototype_note" in summary:
        lines.append(f"\n> **Note:** {summary['recommended_first_prototype_note']}\n")

    lines.append("---")
    lines.append("")
    lines.append("*This report is an engineering simulation for research purposes only.*")
    lines.append("*No medical, diagnostic, therapeutic, clinical, pain, disease, or treatment claims are made.*")
    lines.append("*All data is simulated using deterministic models based on TPU material properties and biomechanical walking gait analysis.*")

    return "\n".join(lines)


def main():
    """Entry point: run simulation, generate reports, print summary."""
    base_dir = Path(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    report_dir = base_dir / "reports" / "simulation"
    report_dir.mkdir(parents=True, exist_ok=True)

    # Run simulation
    results = run_simulation()

    # Generate summary
    summary = generate_summary_and_recommendations(results)

    # Write JSON
    json_path = report_dir / "simulation_results.json"
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump({
            "simulation": results,
            "summary": summary,
        }, f, indent=2, ensure_ascii=False)

    # Write Markdown
    md_text = generate_markdown_report(results, summary)
    md_path = report_dir / "simulation_results.md"
    with open(md_path, "w", encoding="utf-8") as f:
        f.write(md_text)

    # Print terminal table
    print()
    print(render_terminal_table(results))

    # Print final summary
    print()
    print("=" * 70)
    print("FILES CREATED")
    print("=" * 70)
    print(f"  1. {json_path}")
    print(f"  2. {md_path}")
    print()

    print("=" * 70)
    print("EDITIONS TESTED")
    print("=" * 70)
    for name in EDITIONS:
        print(f"  - {name}")
    print()

    print("=" * 70)
    print("RISKS DETECTED")
    print("=" * 70)
    if summary["risks_detected"]:
        for risk in summary["risks_detected"]:
            print(f"  ✗ {risk['edition']} @ {risk['weight_kg']}kg  zone={risk['zone']}  risk={risk['risk']}")
    else:
        print("  No risks detected.")
    print()

    print("=" * 70)
    print("RECOMMENDED FIRST PROTOTYPE")
    print("=" * 70)
    print(f"  Edition: {summary['recommended_first_prototype']}")
    if "recommended_first_prototype_note" in summary:
        print(f"  Note: {summary['recommended_first_prototype_note']}")
    print()
    print("=" * 70)
    print("Simulation complete. All data is engineering-simulation only.")
    print("No medical, diagnostic, or treatment claims are made.")
    print("=" * 70)


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""Z-Physics Agent: Mechanical physics and load calculations.

Takes Z-Bio output (pressure map) as input plus material properties,
performs load case analysis across three gait phases, and validates
against material yield with safety factor calculations.

Engineering-only — no medical claims.
"""
from __future__ import annotations

import argparse
import json
import sys
import uuid
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from runtime.run_z_bio_agent import build_bio_output as bio_build

# ---------------------------------------------------------------------------
# Material properties (TPU 75A-80A, engineering reference range)
# ---------------------------------------------------------------------------

MATERIAL_PROPS = {
    "name": "TPU 75A-80A",
    "yield_strength_mpa": 32.0,
    "young_modulus_mpa": 55.0,
    "elongation_at_break_pct": 400.0,
    "shore_hardness": "75A-80A",
}

GAIT_PHASES = ["heel_strike", "midstance", "toe_off"]
ZONES = ["heel", "arch", "metatarsal", "toe_box", "lateral_edge"]


def _build_task_id() -> str:
    return f"zphys-{uuid.uuid4().hex[:8]}"


def stress_strain_from_pressure(
    pressure_kpa: float,
    wall_thickness_mm: float,
    cell_size_mm: float,
) -> dict:
    """Simplified plate-bending estimate for gyroid lattice wall stress.

    Treats a single lattice cell wall as a thin plate loaded by local
    plantar pressure. Returns engineering estimate only — FEA required.
    """
    # Convert to consistent SI units
    p_pa = pressure_kpa * 1000.0          # kPa -> Pa
    t_m = wall_thickness_mm / 1000.0      # mm -> m
    a_m = cell_size_mm / 1000.0           # mm -> m

    # Thin plate max stress (simply supported square plate, coeff ~= 0.28)
    # sigma_max = k * p * a^2 / t^2
    k_plate = 0.28
    sigma_max_pa = k_plate * p_pa * (a_m ** 2) / (t_m ** 2)
    sigma_max_mpa = sigma_max_pa / 1e6

    # Strain from Hooke's law
    young_modulus = MATERIAL_PROPS["young_modulus_mpa"]
    epsilon = sigma_max_mpa / young_modulus if young_modulus > 0 else 0.0

    return {
        "max_stress_mpa": round(sigma_max_mpa, 4),
        "strain": round(epsilon, 6),
        "stress_unit": "MPa",
        "method": "thin_plate_approximation",
        "coeff_k": k_plate,
        "pressure_input_kpa": round(pressure_kpa, 2),
    }


def safety_factor_from_stress(max_stress_mpa: float) -> dict:
    yield_strength = MATERIAL_PROPS["yield_strength_mpa"]
    if max_stress_mpa <= 0:
        sf = float("inf")
    else:
        sf = yield_strength / max_stress_mpa
    status = "OK" if sf >= 2.0 else ("REVIEW" if sf >= 1.5 else "FAIL")
    return {
        "yield_strength_mpa": yield_strength,
        "max_stress_mpa": round(max_stress_mpa, 4),
        "safety_factor": round(sf, 4) if sf != float("inf") else 999.0,
        "target_minimum_sf": 2.0,
        "status": status,
    }


def perform_load_case_analysis(
    bio_output: dict | None = None,
    foot_length_mm: float = 265.0,
    weight_kg: float = 75.0,
    activity: str = "walking",
    pronation: str = "mild_over",
) -> dict:
    """Run load case analysis for all gait phases and zones."""
    # Get pressure data — either from provided Z-Bio output or recompute
    if bio_output is not None and bio_output.get("biomech_signal"):
        pressure_map = bio_output["biomech_signal"]["pressure_map_kpa"]
        zone_guidance = bio_output.get("design_proposal", {}).get("zone_map", {})
    else:
        bio = bio_build(weight_kg=weight_kg, foot_length_mm=foot_length_mm,
                        width_mm=100.0, arch_height_mm=25.0,
                        activity=activity, pronation=pronation, use_case="daily_wear")
        pressure_map = bio["biomech_signal"]["pressure_map_kpa"]
        zone_guidance = bio.get("design_proposal", {}).get("zone_map", {})

    load_cases: dict[str, dict] = {}
    wall_thickness_map: dict[str, float] = {}
    max_stress_all = 0.0
    min_sf_all = float("inf")
    critical_zone = ""
    critical_phase = ""

    for phase in GAIT_PHASES:
        phase_results: dict[str, dict] = {}
        for zone in ZONES:
            pressure_kpa = pressure_map[phase].get(zone, 0.0)
            zg = zone_guidance.get(zone, {})
            wall_mm = zg.get("wall_thickness_mm", 0.6)
            cell_mm = zg.get("cell_size_mm", 6.0)
            wall_thickness_map[zone] = max(wall_thickness_map.get(zone, 0.0), wall_mm)

            ss = stress_strain_from_pressure(pressure_kpa, wall_mm, cell_mm)
            sf = safety_factor_from_stress(ss["max_stress_mpa"])

            phase_results[zone] = {
                "pressure_kpa": round(pressure_kpa, 2),
                "wall_thickness_mm": wall_mm,
                "stress_strain": ss,
                "safety_factor": sf,
            }

            if ss["max_stress_mpa"] > max_stress_all:
                max_stress_all = ss["max_stress_mpa"]
                min_sf_all = sf["safety_factor"]
                critical_zone = zone
                critical_phase = phase

        load_cases[phase] = phase_results

    # Determine overall engineering decision
    if min_sf_all >= 2.0:
        decision = "PASS"
        approved = True
    elif min_sf_all >= 1.5:
        decision = "CONDITIONAL_PASS"
        approved = False
    else:
        decision = "FAIL"
        approved = False

    return {
        "agent_name": "Z-Physics",
        "task_id": _build_task_id(),
        "output_class": "DESIGN_PROPOSAL",
        "confidence": 0.78,
        "timestamp_utc": datetime.now(timezone.utc).isoformat(),
        "material_properties": MATERIAL_PROPS,
        "load_case": {
            "phases_analyzed": GAIT_PHASES,
            "zones_analyzed": ZONES,
            "results": load_cases,
            "critical_combination": {
                "zone": critical_zone,
                "phase": critical_phase,
                "max_stress_mpa": round(max_stress_all, 4),
                "safety_factor": round(min_sf_all, 4) if min_sf_all != float("inf") else 999.0,
            },
        },
        "pressure_logic": (
            "Pressure values are derived from literature-based gait phase weight "
            "distribution fractions adjusted for individual pronation type. Peak "
            "pressure per zone per phase drives the thin-plate stress calculation. "
            "Values are engineering estimates — not measured data."
        ),
        "thickness_reasoning": (
            f"Wall thicknesses range from 0.6mm to 1.0mm based on zone-specific "
            f"peak pressure ratios. TPU 75A-80A yield strength is ~{MATERIAL_PROPS['yield_strength_mpa']} MPa. "
            f"Thickness scaled upward in high-pressure zones (metatarsal, heel) "
            f"to maintain minimum safety factor of 2.0. Gyroid lattice cell size "
            f"held constant at 6.0mm for printability."
        ),
        "safety_factor_logic": (
            f"Safety factor = yield_strength_mpa / max_stress_mpa. "
            f"Target minimum SF = 2.0. Current minimum SF across all zones "
            f"and phases is {round(min_sf_all, 2) if min_sf_all != float('inf') else '>100'} "
            f"at zone={critical_zone}, phase={critical_phase}. "
            f"SF < 2.0 requires wall thickness increase or FEA re-validation."
        ),
        "simulation_dependency": (
            "All stress values are simplified thin-plate approximations. "
            "FEA simulation (solid mechanics solver with contact modeling) is "
            "required before any production print decision. The thin-plate model "
            "does not capture lattice strut buckling, anisotropic TPU behavior, "
            "or dynamic loading transients."
        ),
        "wall_thickness_map_mm": {z: round(v, 2) for z, v in wall_thickness_map.items()},
        "sources": [
            "TPU 75A-80A manufacturer datasheets — material property reference",
            "Roark's Formulas for Stress and Strain — thin plate equations",
            "Gyroid lattice mechanical property literature — relative density scaling",
        ],
        "assumptions": [
            "Thin-plate bending model for individual lattice cell walls",
            "Linear elastic material response within yield range",
            "Printed part achieves nominal material properties (no voids, full fusion)",
            "Static load approximation — dynamic effects not captured",
            "Z-Bio pressure estimates are within reasonable engineering tolerance",
        ],
        "risks": [
            "Thin-plate model may underpredict stress at lattice node junctions",
            "TPU material properties vary significantly with print orientation",
            "Dynamic heel-strike impact may exceed static load estimates by 2-3x",
            "Lattice strut buckling not modeled — requires FEA",
        ],
        "decision": decision,
        "next_required_validation": "Z-Printability feasibility check on wall thickness map and lattice density",
        "approved_for_use": approved,
        "skills_used": [
            "Knowledge Structuring",
            "Workflow Automation Agent",
            "Source Validation",
            "SCQA Writing Framework",
        ],
    }


def main(argv: list[str] | None = None) -> dict:
    parser = argparse.ArgumentParser(description="Z-Physics Agent — mechanical load and stress analysis")
    parser.add_argument("--bio-input", type=Path, default=None, help="Path to Z-Bio JSON output file")
    parser.add_argument("--weight-kg", type=float, default=75.0, help="Body weight in kg")
    parser.add_argument("--foot-length-mm", type=float, default=265.0, help="Foot length in mm")
    parser.add_argument("--activity", type=str, default="walking")
    parser.add_argument("--pronation", type=str, default="mild_over")
    parser.add_argument("--out", type=Path, default=None, help="Write JSON output to file")
    args = parser.parse_args(argv)

    bio_output = None
    if args.bio_input and args.bio_input.exists():
        bio_output = json.loads(args.bio_input.read_text(encoding="utf-8"))

    output = perform_load_case_analysis(
        bio_output=bio_output,
        foot_length_mm=args.foot_length_mm,
        weight_kg=args.weight_kg,
        activity=args.activity,
        pronation=args.pronation,
    )

    if args.out:
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(json.dumps(output, indent=2), encoding="utf-8")

    print(json.dumps(output, indent=2))
    return output


if __name__ == "__main__":
    main()

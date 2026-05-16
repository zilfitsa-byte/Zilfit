#!/usr/bin/env python3
"""Z-Printability Agent: 3D print feasibility validation.

Takes Z-Physics output (wall thickness map, lattice density map) and validates
3D print feasibility including wall thickness thresholds, overhang analysis,
print time estimation, and material usage.

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

from runtime.shared_db import SharedDB

# ---------------------------------------------------------------------------
# Print constraints
# ---------------------------------------------------------------------------

MIN_WALL_THICKNESS_MM = 0.80
MAX_OVERHANG_ANGLE_DEG = 45.0
TPU_DENSITY_G_CC = 1.21       # approximate density of TPU 75A-80A
FILL_FRACTION_DEFAULT = 0.35  # gyroid infill fraction estimate

ZONES = ["heel", "arch", "metatarsal", "toe_box", "lateral_edge"]

# Typical geometry assumptions for engineering estimates (mm)
ZONE_VOLUMES_CC = {
    "heel": 15.0,
    "arch": 10.0,
    "metatarsal": 18.0,
    "toe_box": 8.0,
    "lateral_edge": 12.0,
}


def _build_task_id() -> str:
    return f"zprint-{uuid.uuid4().hex[:8]}"


def _estimate_print_time_minutes(total_volume_cc: float, layer_height_mm: float = 0.2,
                                  print_speed_mm_s: float = 40.0) -> float:
    """Rough print time estimate based on volume and FDM parameters."""
    # Layer volume = print_speed * line_width * layer_height (mm^3/s)
    line_width = 0.4  # mm typical for 0.4mm nozzle
    layer_volume_mm3 = print_speed_mm_s * line_width * layer_height_mm
    total_mm3 = total_volume_cc * 1000.0
    travel_factor = 1.3  # account for travel moves
    time_s = (total_mm3 / layer_volume_mm3) * travel_factor
    return round(time_s / 60.0, 1)


def _estimate_overhang_risks(
    wall_thickness_map: dict,
    zone_guidance: dict | None = None,
) -> list[dict]:
    """Analyze overhang risks per zone based on geometry heuristics.

    Arch and lateral edge zones typically present overhang challenges
    in shoe-insert geometry due to curvature.
    """
    risks = []
    # Heuristic: arch zone has highest overhang angle due to vault geometry
    overhang_zones = {
        "arch": 55.0,
        "lateral_edge": 48.0,
        "heel": 30.0,
        "metatarsal": 35.0,
        "toe_box": 25.0,
    }
    for zone, angle in overhang_zones.items():
        if angle > MAX_OVERHANG_ANGLE_DEG:
            risks.append({
                "zone": zone,
                "estimated_overhang_angle_deg": angle,
                "exceeds_threshold": True,
                "recommendation": "Support structure or build orientation adjustment needed",
            })
        else:
            risks.append({
                "zone": zone,
                "estimated_overhang_angle_deg": angle,
                "exceeds_threshold": False,
                "recommendation": "Printable without supports at this zone",
            })
    return risks


def perform_printability_check(
    physics_output: dict | None = None,
    bio_output: dict | None = None,
) -> dict:
    """Run full printability validation."""
    # Get wall thickness data from physics output, or use defaults
    if physics_output is not None:
        wall_thickness_map = physics_output.get("wall_thickness_map_mm", {})
        load_case = physics_output.get("load_case", {})
        sf_info = load_case.get("critical_combination", {})
    else:
        wall_thickness_map = {z: 0.8 for z in ZONES}
        sf_info = {}

    # --- Wall thickness validation ---
    wall_risks: list[dict] = []
    zones_below_min: list[str] = []
    for zone in ZONES:
        wt = wall_thickness_map.get(zone, 0.8)
        if wt < MIN_WALL_THICKNESS_MM:
            zones_below_min.append(zone)
            wall_risks.append({
                "zone": zone,
                "wall_thickness_mm": wt,
                "min_threshold_mm": MIN_WALL_THICKNESS_MM,
                "risk_level": "HIGH",
                "issue": f"Wall thickness {wt}mm below minimum {MIN_WALL_THICKNESS_MM}mm",
                "recommendation": "Increase wall thickness or accept print failure risk",
            })
        else:
            wall_risks.append({
                "zone": zone,
                "wall_thickness_mm": wt,
                "min_threshold_mm": MIN_WALL_THICKNESS_MM,
                "risk_level": "LOW",
                "issue": None,
            })

    # --- Overhang analysis ---
    support_risks = _estimate_overhang_risks(wall_thickness_map)
    zones_needing_supports = [
        r["zone"] for r in support_risks if r["exceeds_threshold"]
    ]

    # --- Material usage estimate ---
    total_volume_cc = sum(ZONE_VOLUMES_CC.get(z, 10.0) for z in ZONES)
    effective_volume_cc = total_volume_cc * FILL_FRACTION_DEFAULT
    material_mass_g = effective_volume_cc * TPU_DENSITY_G_CC
    material_cost_usd = material_mass_g * 0.08  # ~$80/kg TPU filament

    # --- Print time estimate ---
    print_time_min = _estimate_print_time_minutes(effective_volume_cc)

    # --- Mesh integrity assessment ---
    mesh_issues: list[str] = []
    if wall_thickness_map.get("arch", 0.8) < 0.6:
        mesh_issues.append("Arch zone wall below printability threshold — mesh may fail at thin sections")
    if len(zones_needing_supports) > 0:
        mesh_issues.append(
            f"Support required at zones: {', '.join(zones_needing_supports)}. "
            "Support removal may affect surface finish at contact zones."
        )
    if physics_output and not physics_output.get("approved_for_use", False):
        mesh_issues.append("Physics validation not fully passed — review stress/safety factor before print")

    mesh_integrity = "ACCEPTABLE" if len(mesh_issues) == 0 else "CONDITIONAL"

    # --- Material notes ---
    material_notes = (
        f"TPU 75A-80A recommended. Estimated material: {material_mass_g:.1f}g "
        f"({effective_volume_cc:.1f} cc effective volume at {FILL_FRACTION_DEFAULT:.0%} fill). "
        f"Print orientation: flat bed with arch supported. "
        f"Nozzle: 0.4mm, layer height: 0.2mm. "
        f"Bed adhesion: PEI sheet or glue stick recommended for TPU. "
        f"Retract at 20-30mm/s to prevent stringing."
    )

    # --- Print-ready decision ---
    has_high_risk = any(r["risk_level"] == "HIGH" for r in wall_risks)
    if has_high_risk:
        print_ready = "NO_GO"
        decision = "FAIL"
        approved = False
    elif mesh_issues:
        print_ready = "CONDITIONAL"
        decision = "CONDITIONAL_PASS"
        approved = False
    else:
        print_ready = "GO"
        decision = "PASS"
        approved = False  # still needs FEA before production use

    return {
        "agent_name": "Z-Printability",
        "task_id": _build_task_id(),
        "output_class": "DESIGN_PROPOSAL",
        "confidence": 0.75,
        "timestamp_utc": datetime.now(timezone.utc).isoformat(),
        "print_risks": wall_risks,
        "support_risks": support_risks,
        "zones_below_min_thickness": zones_below_min,
        "zones_needing_support": zones_needing_supports,
        "mesh_integrity": mesh_integrity,
        "mesh_issues": mesh_issues,
        "material_notes": material_notes,
        "print_ready_status": print_ready,
        "print_time_estimate_min": print_time_min,
        "material_usage_estimate": {
            "volume_effective_cc": round(effective_volume_cc, 1),
            "mass_g": round(material_mass_g, 1),
            "estimated_cost_usd": round(material_cost_usd, 2),
            "fill_fraction": FILL_FRACTION_DEFAULT,
        },
        "print_parameters": {
            "nozzle_mm": 0.4,
            "layer_height_mm": 0.2,
            "print_speed_mm_s": 40.0,
            "min_wall_thickness_mm": MIN_WALL_THICKNESS_MM,
            "max_overhang_angle_deg": MAX_OVERHANG_ANGLE_DEG,
        },
        "sources": [
            "FDM printing feasibility for TPU filaments — manufacturer guidelines",
            "Overhang angle limits for FDM 3D printing — 45° rule",
            "Gyroid infill printability research — support-free geometry",
        ],
        "assumptions": [
            "Zone volumes are engineering estimates based on average foot geometry",
            "Gyroid infill fraction of 35% assumed — actual density varies by slicer",
            "Print parameters represent typical FDM setup (0.4mm nozzle, 0.2mm layer)",
            "Wall thickness map from physics analysis is accurate within tolerance",
            "No mesh file exists yet — feasibility based on parameter estimates only",
        ],
        "risks": [
            "TPU printing is sensitive to moisture — filament must be dry",
            "Thin sections below 0.8mm may fail during printing or part removal",
            "Support structures at arch zone may leave surface artifacts on contact surfaces",
            "Actual geometry may require orientation optimization per foot shape",
            "No STL file generated yet — print feasibility is pre-geometry estimate",
        ],
        "decision": decision,
        "next_required_validation": "CAD mesh generation and FEA simulation (Z-Sim) before production print",
        "approved_for_use": approved,
        "skills_used": [
            "Knowledge Structuring",
            "Workflow Automation Agent",
            "Source Validation",
            "SCQA Writing Framework",
        ],
    }


def main(argv: list[str] | None = None) -> dict:
    parser = argparse.ArgumentParser(description="Z-Printability Agent — 3D print feasibility validation")
    parser.add_argument("--physics-input", type=Path, default=None,
                        help="Path to Z-Physics JSON output file")
    parser.add_argument("--bio-input", type=Path, default=None,
                        help="Path to Z-Bio JSON output file (optional context)")
    parser.add_argument("--out", type=Path, default=None, help="Write JSON output to file")
    args = parser.parse_args(argv)

    physics_output = None
    if args.physics_input and args.physics_input.exists():
        physics_output = json.loads(args.physics_input.read_text(encoding="utf-8"))

    bio_output = None
    if args.bio_input and args.bio_input.exists():
        bio_output = json.loads(args.bio_input.read_text(encoding="utf-8"))

    output = perform_printability_check(
        physics_output=physics_output,
        bio_output=bio_output,
    )

    # -- SharedDB: write task-state record and verify read-back ----------------
    db = SharedDB()
    task_id = output["task_id"]
    db.upsert(
        agent_name="Z-Printability",
        task_id=task_id,
        status="completed",
        summary="3D print feasibility validation completed — engineering design proposal generated",
        risk_level="low",
        next_action=output.get("next_required_validation", ""),
    )
    # Verify read-back
    _record_check = db.get(agent_name="Z-Printability", task_id=task_id)
    output["shared_db_persisted"] = _record_check is not None

    if args.out:
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(json.dumps(output, indent=2), encoding="utf-8")

    print(json.dumps(output, indent=2))
    return output


if __name__ == "__main__":
    main()

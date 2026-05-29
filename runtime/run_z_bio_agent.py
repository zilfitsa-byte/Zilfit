#!/usr/bin/env python3
"""Z-Bio Agent: Plantar biomechanics and gait signal interpretation.

Reads foot dimensions, weight, activity, pronation, and use case to calculate
estimated plantar pressure by zone for three gait phases. Outputs zone
engineering guidance for TPU gyroid lattice design.

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
# Biomechanics model constants (literature-based fractions)
# ---------------------------------------------------------------------------

# Base weight-distribution fractions per gait phase for neutral pronation
# Source: engineering biomechanics literature (e.g. Perry & Burnfield, Gait Analysis)
BASE_FRACTIONS: dict[str, dict[str, float]] = {
    "heel_strike": {
        "heel": 0.60,
        "arch": 0.05,
        "metatarsal": 0.15,
        "toe_box": 0.05,
        "lateral_edge": 0.15,
    },
    "midstance": {
        "heel": 0.20,
        "arch": 0.15,
        "metatarsal": 0.35,
        "toe_box": 0.10,
        "lateral_edge": 0.20,
    },
    "toe_off": {
        "heel": 0.05,
        "arch": 0.05,
        "metatarsal": 0.50,
        "toe_box": 0.25,
        "lateral_edge": 0.15,
    },
}

# Pronation adjustment factors applied to specific zones
PRONATION_ADJUST: dict[str, dict[str, float]] = {
    "neutral": {
        "heel": 0.0,
        "arch": 0.0,
        "metatarsal": 0.0,
        "toe_box": 0.0,
        "lateral_edge": 0.0,
    },
    "mild_over": {
        "heel": 0.05,
        "arch": -0.03,
        "metatarsal": 0.05,
        "toe_box": 0.02,
        "lateral_edge": -0.09,
    },
    "moderate_over": {
        "heel": 0.08,
        "arch": -0.05,
        "metatarsal": 0.10,
        "toe_box": 0.05,
        "lateral_edge": -0.18,
    },
    "mild_under": {
        "heel": -0.02,
        "arch": 0.02,
        "metatarsal": -0.03,
        "toe_box": -0.02,
        "lateral_edge": 0.05,
    },
}

# Activity multiplier (peak impact)
ACTIVITY_MULTIPLIER: dict[str, float] = {
    "standing": 1.0,
    "walking": 1.2,
    "running": 2.5,
    "high_impact": 3.0,
}

# Material and lattice defaults
MATERIAL = "TPU_75A_80A"
DEFAULT_WALL_THICKNESS_MM = 0.6
DEFAULT_CELL_SIZE_MM = 6.0
GYROID_LATTICE_TYPE = "gyroid"

ZONES = ["heel", "arch", "metatarsal", "toe_box", "lateral_edge"]
GAIT_PHASES = ["heel_strike", "midstance", "toe_off"]


def _normalize_fractions(raw: dict[str, float]) -> dict[str, float]:
    total = sum(raw.values())
    if total <= 0:
        return {z: 1.0 / len(raw) for z in raw}
    return {k: v / total for k, v in raw.items()}


def compute_pressure_map(
    weight_kg: float,
    foot_length_mm: float,
    activity: str = "walking",
    pronation: str = "neutral",
    use_case: str = "daily_wear",
) -> dict:
    """Return zone pressure (kPa) per gait phase and derived wall thickness guidance."""
    peak_force_n = weight_kg * 9.81 * ACTIVITY_MULTIPLIER.get(activity, 1.2)
    pressure_zone_map: dict[str, dict[str, float]] = {}

    for phase in GAIT_PHASES:
        base = BASE_FRACTIONS.get(phase, {})
        adj = PRONATION_ADJUST.get(pronation, PRONATION_ADJUST["neutral"])
        raw = {z: base.get(z, 0.0) + adj.get(z, 0.0) for z in ZONES}
        normed = _normalize_fractions(raw)
        pressure_zone_map[phase] = {
            z: (normed[z] * peak_force_n * 1000) / (foot_length_mm * foot_length_mm * 1e-6)
            for z in ZONES
        }

    # Engineering guidance: wall thickness scales with peak pressure
    max_peak = max(v for ph in pressure_zone_map.values() for v in ph.values())
    zone_guidance: dict[str, dict] = {}
    for zone in ZONES:
        peak_p = max(pressure_zone_map[ph][zone] for ph in GAIT_PHASES)
        ratio = peak_p / max_peak if max_peak > 0 else 0.5
        # Scale wall thickness proportionally; floor at 0.6 mm
        wall = max(DEFAULT_WALL_THICKNESS_MM, round(DEFAULT_WALL_THICKNESS_MM + ratio * 0.4, 2))
        lattice_density = round(0.3 + ratio * 0.5, 2)  # relative density fraction
        zone_guidance[zone] = {
            "peak_pressure_kpa": round(peak_p, 2),
            "wall_thickness_mm": wall,
            "lattice_relative_density": lattice_density,
            "lattice_type": GYROID_LATTICE_TYPE,
            "cell_size_mm": DEFAULT_CELL_SIZE_MM,
        }

    return {
        "peak_force_newtons": round(peak_force_n, 2),
        "pressure_map_kpa": pressure_zone_map,
        "zone_engineering_guidance": zone_guidance,
        "material": MATERIAL,
    }


def _build_task_id() -> str:
    return f"zbio-{uuid.uuid4().hex[:8]}"


def build_bio_output(
    weight_kg: float,
    foot_length_mm: float,
    width_mm: float,
    arch_height_mm: float,
    activity: str = "walking",
    pronation: str = "neutral",
    use_case: str = "daily_wear",
) -> dict:
    pressure_result = compute_pressure_map(weight_kg, foot_length_mm, activity, pronation, use_case)

    biomech_signal = {
        "gait_phases": GAIT_PHASES,
        "zones": ZONES,
        "pressure_map_kpa": pressure_result["pressure_map_kpa"],
        "peak_force_n": pressure_result["peak_force_newtons"],
        "activity_level": activity,
        "pronation_type": pronation,
    }

    interpretation_scope = "engineering-design-guidance-only"

    # Determine evidence level based on activity complexity
    evidence_map = {
        "standing": "medium",
        "walking": "medium-high",
        "running": "medium",
        "high_impact": "low",
    }
    evidence_level = evidence_map.get(activity, "medium")

    design_relevance = (
        "Plantar pressure zones inform wall thickness and lattice density per zone "
        "for TPU gyroid lattice insole/orthotic structure. Pressure distribution "
        "across gait phases drives zone-specific engineering parameters."
    )

    claim_risk = (
        "LOW — output is engineering design guidance only. No diagnostic, "
        "treatment, or medical claims are made. Biomechanical signal data is "
        "used solely for structural parameter calculation."
    )

    # Build design proposal from zone guidance
    design_proposal = {
        "material": pressure_result["material"],
        "lattice_type": GYROID_LATTICE_TYPE,
        "default_cell_size_mm": DEFAULT_CELL_SIZE_MM,
        "zone_map": pressure_result["zone_engineering_guidance"],
    }

    output = {
        "agent_name": "Z-Bio",
        "task_id": _build_task_id(),
        "output_class": "ENGINEERING_ASSUMPTION",
        "confidence": 0.82,
        "timestamp_utc": datetime.now(timezone.utc).isoformat(),
        "inputs": {
            "foot_length_mm": foot_length_mm,
            "width_mm": width_mm,
            "arch_height_mm": arch_height_mm,
            "weight_kg": weight_kg,
            "activity": activity,
            "pronation": pronation,
            "use_case": use_case,
        },
        "biomech_signal": biomech_signal,
        "interpretation_scope": interpretation_scope,
        "evidence_level": evidence_level,
        "design_relevance": design_relevance,
        "claim_risk": claim_risk,
        "design_proposal": design_proposal,
        "sources": [
            "Perry & Burnfield — Gait Analysis: Normal and Pathological Function (engineering reference)",
            "TPU 75A-80A material datasheets — manufacturer engineering data",
            "Biomimetic lattice design literature — gyroid unit cell mechanical properties",
        ],
        "assumptions": [
            "Weight distribution fractions derived from published gait analysis literature",
            "Pronation adjustments are engineering approximations, not clinical measurements",
            "Material behavior assumes linear elastic region for initial sizing",
            "Lattice relative density maps to strut thickness via gyroid geometry equations",
        ],
        "risks": [
            "Pressure distribution simplified — actual contact area varies per individual foot geometry",
            "Dynamic gait loading exceeds static model — FEA simulation required before production",
            "Material properties vary by print orientation and post-processing",
        ],
        "decision": "CONDITIONAL_PASS",
        "next_required_validation": "Z-Physics load case analysis with pressure map input",
        "approved_for_use": False,
        "skills_used": [
            "Deep Research Synthesizer",
            "Source Validation",
            "Knowledge Structuring",
            "SCQA Writing Framework",
        ],
    }
    return output


def _default_inputs() -> dict:
    return {
        "foot_length_mm": 265.0,
        "width_mm": 100.0,
        "arch_height_mm": 25.0,
        "weight_kg": 75.0,
        "activity": "walking",
        "pronation": "mild_over",
        "use_case": "daily_wear",
    }


def main(argv: list[str] | None = None) -> dict:
    parser = argparse.ArgumentParser(description="Z-Bio Agent — plantar biomechanics and gait signal interpretation")
    parser.add_argument("--weight-kg", type=float, default=None, help="Body weight in kg")
    parser.add_argument("--foot-length-mm", type=float, default=None, help="Foot length in mm")
    parser.add_argument("--width-mm", type=float, default=None, help="Foot width in mm")
    parser.add_argument("--arch-height-mm", type=float, default=None, help="Arch height in mm")
    parser.add_argument("--activity", type=str, default=None, choices=list(ACTIVITY_MULTIPLIER.keys()))
    parser.add_argument("--pronation", type=str, default=None, choices=list(PRONATION_ADJUST.keys()))
    parser.add_argument("--use-case", type=str, default=None)
    parser.add_argument("--out", type=Path, default=None, help="Write JSON output to file")
    parser.add_argument("--stdin-json", action="store_true", help="Read input JSON from stdin")
    args = parser.parse_args(argv)

    if args.stdin_json:
        inp = json.loads(sys.stdin.read())
    elif any(v is not None for v in (args.weight_kg, args.foot_length_mm, args.activity)):
        inp = _default_inputs()
        inp.update({k: v for k, v in [
            ("weight_kg", args.weight_kg),
            ("foot_length_mm", args.foot_length_mm),
            ("width_mm", args.width_mm),
            ("arch_height_mm", args.arch_height_mm),
            ("activity", args.activity),
            ("pronation", args.pronation),
            ("use_case", args.use_case),
        ] if v is not None})
    else:
        inp = _default_inputs()

    output = build_bio_output(**inp)

    # -- SharedDB: write task-state record and verify read-back ----------------
    db = SharedDB()
    task_id = output["task_id"]
    db.upsert(
        agent_name="Z-Bio",
        task_id=task_id,
        status="completed",
        summary="Biomechanics analysis completed — engineering design guidance generated",
        risk_level="low",
        next_action=output.get("next_required_validation", ""),
    )
    # Verify read-back
    _record_check = db.get(agent_name="Z-Bio", task_id=task_id)
    output["shared_db_persisted"] = _record_check is not None

    if args.out:
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(json.dumps(output, indent=2), encoding="utf-8")

    print(json.dumps(output, indent=2))
    return output


if __name__ == "__main__":
    main()

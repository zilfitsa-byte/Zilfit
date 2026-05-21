"""ZILFIT P01 BALANCE Export Builder.

Produces three manufacturing artifacts from the BALANCE prototype plan:
  1. balance_plan.json          — full engineering plan
  2. balance_mesh_config.json   — nTop mesh configuration
  3. balance_print_sheet.md     — human-readable print briefing

Enforced constraints:
  - density floor >= 0.18
  - density ceiling <= 0.45
  - adjacent delta <= 0.06 (no hard edge transitions)
  - shell_thickness = 0.8 mm
  - manufacturing_process = "MJF"
  - shrinkage_compensation_pct = 1.5
"""

from __future__ import annotations

import json
import math
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

from zilfit_p01_balance_builder import (
    BALANCE_EDITION,
    CELL_SIZE_MM,
    DENSITY_MAX,
    DENSITY_MIN,
    OUTER_SHELL_MM,
    WALL_THICKNESS_BODY_MM,
    SCALE_COMPENSATION_PCT,
    SUPPORTED_FOOT_ZONES,
    PRESSURE_MAX_KPA,
    MAX_ADJACENT_DELTA_LATERAL,
)

# ─── Export constants ─────────────────────────────────────────────────

EXPORT_DENSITY_FLOOR = 0.18
EXPORT_DENSITY_CEILING = 0.45
EXPORT_ADJACENT_DELTA = 0.06
EXPORT_SHELL_THICKNESS = 0.8
EXPORT_MANUFACTURING = "MJF"
EXPORT_SHRINKAGE_PCT = 1.5

PROJ_ROOT = Path(__file__).resolve().parent.parent


def _sigmoid(t: float) -> float:
    return 1.0 / (1.0 + math.exp(-4.0 * t))


def _density_zones() -> Dict[str, float]:
    """BALANCE density distribution — gentle wave."""
    return {
        "heel": 0.30,
        "metatarsal": 0.29,
        "midfoot": 0.32,
        "arch": 0.28,
        "forefoot": 0.31,
        "toes": 0.26,
    }


# ─── Validation gates ─────────────────────────────────────────────────

def validate_density(density_by_zone: Dict[str, float]) -> List[str]:
    errs = []
    for zone, rho in density_by_zone.items():
        if rho < EXPORT_DENSITY_FLOOR:
            errs.append(f"{zone}: density {rho} < floor {EXPORT_DENSITY_FLOOR}")
        if rho > EXPORT_DENSITY_CEILING:
            errs.append(f"{zone}: density {rho} > ceiling {EXPORT_DENSITY_CEILING}")
    return errs


def validate_adjacent_delta(density_by_zone: Dict[str, float]) -> List[str]:
    """Check that adjacent zone deltas do not exceed 0.06."""
    errs = []
    zone_order = list(SUPPORTED_FOOT_ZONES)
    for i in range(len(zone_order) - 1):
        z_a, z_b = zone_order[i], zone_order[i + 1]
        if z_a in density_by_zone and z_b in density_by_zone:
            delta = abs(density_by_zone[z_b] - density_by_zone[z_a])
            if delta > EXPORT_ADJACENT_DELTA:
                errs.append(
                    f"transition {z_a}→{z_b}: delta {delta:.4f} > {EXPORT_ADJACENT_DELTA}"
                )
    return errs


def validate_no_hard_edges(transitions: List[Dict]) -> List[str]:
    """Ensure sigmoid transitions contain no step (instant) changes."""
    errs = []
    for t in transitions:
        pts = t.get("transition_points", [])
        if len(pts) < 2:
            errs.append(f"transition {t.get('zone', '?')}: fewer than 2 points")
            continue
        for j in range(1, len(pts)):
            prev_rho = pts[j - 1]["rho"]
            curr_rho = pts[j]["rho"]
            if abs(curr_rho - prev_rho) > 0.12:
                errs.append(
                    f"hard edge at {t.get('zone', '?')}: "
                    f"rho jump {abs(curr_rho - prev_rho):.4f}"
                )
    return errs


def validate_shell_thickness(thickness: float) -> List[str]:
    if thickness != EXPORT_SHELL_THICKNESS:
        return [f"shell {thickness} != required {EXPORT_SHELL_THICKNESS}"]
    return []


def validate_mjf_compatibility(plan: Dict[str, Any]) -> List[str]:
    errs = []
    if plan.get("manufacturing_plan", {}).get("primary_process") != EXPORT_MANUFACTURING:
        errs.append("manufacturing process is not MJF")
    return errs


# ─── Sigmoid transition builder ──────────────────────────────────────

def build_sigmoid_transitions(
    density_by_zone: Dict[str, float],
) -> List[Dict[str, Any]]:
    order = [z for z in SUPPORTED_FOOT_ZONES if z in density_by_zone]
    transitions: List[Dict[str, Any]] = []
    for i in range(len(order) - 1):
        z_from, z_to = order[i], order[i + 1]
        rho_from = density_by_zone[z_from]
        rho_to = density_by_zone[z_to]
        pts = []
        for k in range(9):
            t = -4.0 + 8.0 * (k / 8.0)
            s = _sigmoid(t)
            rho = round(rho_from + (rho_to - rho_from) * s, 4)
            pts.append({"index": k, "t": round(t, 3), "sigmoid": round(s, 4), "rho": rho})
        transitions.append({
            "zone": f"{z_from}->{z_to}",
            "from_zone": z_from,
            "to_zone": z_to,
            "from_density": rho_from,
            "to_density": rho_to,
            "transition_points": pts,
            "max_gradient": round(max(
                abs(pts[j + 1]["rho"] - pts[j]["rho"]) for j in range(len(pts) - 1)
            ), 4),
        })
    return transitions


# ─── Wall thickness map ───────────────────────────────────────────────

def build_wall_thickness_by_zone() -> Dict[str, Dict[str, float]]:
    return {
        zone: {
            "body_mm": WALL_THICKNESS_BODY_MM,
            "shell_mm": OUTER_SHELL_MM,
        }
        for zone in SUPPORTED_FOOT_ZONES
    }


# ─── Cell size map ────────────────────────────────────────────────────

def build_cell_size_by_zone() -> Dict[str, float]:
    return {zone: CELL_SIZE_MM for zone in SUPPORTED_FOOT_ZONES}


# ─── Main plan builder ────────────────────────────────────────────────

def build_balance_export_plan() -> Dict[str, Any]:
    pid = f"P01-BALANCE-{uuid.uuid4().hex[:8].upper()}"
    ts = datetime.now(timezone.utc).isoformat()
    density_by_zone = _density_zones()
    transitions = build_sigmoid_transitions(density_by_zone)

    all_errors: List[str] = []
    all_errors.extend(validate_density(density_by_zone))
    all_errors.extend(validate_adjacent_delta(density_by_zone))
    all_errors.extend(validate_no_hard_edges(transitions))
    all_errors.extend(validate_shell_thickness(OUTER_SHELL_MM))

    density_ok = len(validate_density(density_by_zone)) == 0
    delta_ok = len(validate_adjacent_delta(density_by_zone)) == 0
    edges_ok = len(validate_no_hard_edges(transitions)) == 0
    shell_ok = len(validate_shell_thickness(OUTER_SHELL_MM)) == 0

    ready_for_print = len(all_errors) == 0
    ready_for_stl = ready_for_print and density_ok and delta_ok and shell_ok

    plan: Dict[str, Any] = {
        "prototype_id": pid,
        "timestamp": ts,
        "edition": BALANCE_EDITION,
        "ready_for_print": ready_for_print,
        "ready_for_stl": ready_for_stl,
        "density_by_zone": density_by_zone,
        "wall_thickness_by_zone": build_wall_thickness_by_zone(),
        "cell_size_by_zone": build_cell_size_by_zone(),
        "sigmoid_transition_rules": {
            "type": "sigmoid_blend",
            "step_transition_allowed": False,
            "max_adjacent_delta": EXPORT_ADJACENT_DELTA,
            "transitions": transitions,
        },
        "shell_thickness_mm": OUTER_SHELL_MM,
        "manufacturing_plan": {
            "primary_process": EXPORT_MANUFACTURING,
            "cell_size_mm": CELL_SIZE_MM,
            "shrinkage_compensation_pct": EXPORT_SHRINKAGE_PCT,
            "wall_thickness_body_mm": WALL_THICKNESS_BODY_MM,
            "wall_thickness_shell_mm": OUTER_SHELL_MM,
        },
        "validation_errors": all_errors,
        "pressure_limit_kpa": PRESSURE_MAX_KPA,
        "density_bounds": {
            "floor": EXPORT_DENSITY_FLOOR,
            "ceiling": EXPORT_DENSITY_CEILING,
        },
    }
    return plan


# ─── Export writers ───────────────────────────────────────────────────

def export_balance_plan(
    plan: Optional[Dict[str, Any]] = None,
    output_dir: Optional[str] = None,
) -> str:
    if plan is None:
        plan = build_balance_export_plan()
    out_dir = Path(output_dir) if output_dir else PROJ_ROOT / "exports"
    out_dir.mkdir(parents=True, exist_ok=True)
    path = out_dir / "balance_plan.json"
    with open(path, "w") as f:
        json.dump(plan, f, indent=2, ensure_ascii=False)
    return str(path)


def export_mesh_config(
    plan: Optional[Dict[str, Any]] = None,
    output_dir: Optional[str] = None,
) -> str:
    if plan is None:
        plan = build_balance_export_plan()
    out_dir = Path(output_dir) if output_dir else PROJ_ROOT / "exports"
    out_dir.mkdir(parents=True, exist_ok=True)

    config = {
        "version": "1.0",
        "prototype_id": plan["prototype_id"],
        "edition": plan["edition"],
        "manufacturing_process": plan["manufacturing_plan"]["primary_process"],
        "shrinkage_compensation_pct": plan["manufacturing_plan"]["shrinkage_compensation_pct"],
        "shell_thickness_mm": plan["shell_thickness_mm"],
        "cell_size_mm": plan["manufacturing_plan"]["cell_size_mm"],
        "density_by_zone": plan["density_by_zone"],
        "wall_thickness_by_zone": plan["wall_thickness_by_zone"],
        "cell_size_by_zone": plan["cell_size_by_zone"],
        "sigmoid_transition_rules": plan["sigmoid_transition_rules"],
        "ready_for_stl": plan["ready_for_stl"],
        "density_floor": EXPORT_DENSITY_FLOOR,
        "density_ceiling": EXPORT_DENSITY_CEILING,
    }

    path = out_dir / "balance_mesh_config.json"
    with open(path, "w") as f:
        json.dump(config, f, indent=2, ensure_ascii=False)
    return str(path)


def export_print_sheet(
    plan: Optional[Dict[str, Any]] = None,
    output_dir: Optional[str] = None,
) -> str:
    if plan is None:
        plan = build_balance_export_plan()
    out_dir = Path(output_dir) if output_dir else PROJ_ROOT / "exports"
    out_dir.mkdir(parents=True, exist_ok=True)

    lines = [
        "# P01 BALANCE — Print Sheet",
        "",
        f"**Prototype ID**: {plan['prototype_id']}",
        f"**Edition**: {plan['edition']}",
        f"**Timestamp**: {plan['timestamp']}",
        "",
        "## Manufacturing",
        f"- Process: {plan['manufacturing_plan']['primary_process']}",
        f"- Cell size: {plan['manufacturing_plan']['cell_size_mm']} mm",
        f"- Shrinkage compensation: {plan['manufacturing_plan']['shrinkage_compensation_pct']}%",
        f"- Shell thickness: {plan['shell_thickness_mm']} mm",
        f"- Body wall thickness: {plan['manufacturing_plan']['wall_thickness_body_mm']} mm",
        "",
        "## Density by Zone",
    ]
    for zone, rho in plan["density_by_zone"].items():
        floor_str = " **FLOOR**" if rho < EXPORT_DENSITY_FLOOR else ""
        ceil_str = " **CEILING**" if rho > EXPORT_DENSITY_CEILING else ""
        lines.append(f"- {zone}: {rho}{floor_str}{ceil_str}")

    lines += [
        "",
        "## Validation",
        f"- ready_for_print: {plan['ready_for_print']}",
        f"- ready_for_stl: {plan['ready_for_stl']}",
    ]
    if plan["validation_errors"]:
        lines.append("")
        lines.append("### Errors")
        for e in plan["validation_errors"]:
            lines.append(f"- {e}")

    lines.append("")
    path = out_dir / "balance_print_sheet.md"
    with open(path, "w") as f:
        f.write("\n".join(lines))
    return str(path)


def export_all(
    output_dir: Optional[str] = None,
) -> Dict[str, str]:
    """Generate all three artifacts. Returns dict of filename -> path."""
    plan = build_balance_export_plan()
    return {
        "balance_plan.json": export_balance_plan(plan, output_dir),
        "balance_mesh_config.json": export_mesh_config(plan, output_dir),
        "balance_print_sheet.md": export_print_sheet(plan, output_dir),
    }

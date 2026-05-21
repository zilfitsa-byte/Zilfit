"""ZILFIT P01 BALANCE Prototype Builder.

Generates a manufacturing-ready BALANCE edition prototype configuration.

Output contract keys:
    prototype_id, edition, density_by_zone, wall_thickness_by_zone,
    transition_rules, manufacturing_plan, validation_results,
    accept_criteria, risk_register, ready_for_print, ready_for_stl
"""

from __future__ import annotations

import json
import math
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

# ─── Engineering constants ────────────────────────────────────────────

BALANCE_EDITION = "BALANCE"
DENSITY_MIN = 0.26
DENSITY_MAX = 0.32
CELL_SIZE_MM = 6.0

WALL_THICKNESS_BODY_MM = 0.65
OUTER_SHELL_MM = 0.80
MIN_WALL_THICKNESS_IMMUTABLE = 0.6  # immutable floor

SCALE_COMPENSATION_PCT = 1.5  # isotropic

MAX_ADJACENT_DELTA_LATERAL = 0.06      # lateral cap
MAX_ADJACENT_DELTA_HEEL_ARCH = 0.08    # heel-arch path cap

PRESSURE_MAX_KPA = 55

MANUFACTURE_PRIMARY = "MJF"
MANUFACTURE_SECONDARY = "SLS"

SUPPORTED_FOOT_ZONES = ("heel", "metatarsal", "midfoot", "arch", "forefoot", "toes")

PROJ_ROOT = Path(__file__).resolve().parent.parent


# ─── Sigmoid engine ───────────────────────────────────────────────────

def _sigmoid(t: float) -> float:
    return 1.0 / (1.0 + math.exp(-3.0 * t))


def generate_sigmoid_transition(
    from_density: float,
    to_density: float,
    zone_name: str = "",
    n_points: int = 8,
) -> Dict[str, Any]:
    pts: List[Dict[str, Any]] = []
    violations: List[str] = []
    gradients: List[float] = []
    prev: Optional[float] = None

    for i in range(n_points):
        t = -4.0 + 8.0 * (i / max(n_points - 1, 1))
        s = _sigmoid(t)
        rho = round(from_density + (to_density - from_density) * s, 4)
        pts.append({"index": i, "t": round(t, 3), "sigmoid_s": round(s, 4), "rho": rho})
        if prev is not None:
            d = abs(rho - prev); gradients.append(d)
            if d > MAX_ADJACENT_DELTA_LATERAL:
                violations.append(
                    f"Point {i}: delta={d:.4f} > {MAX_ADJACENT_DELTA_LATERAL}")
        prev = rho

    return {
        "zone": zone_name,
        "from_density": from_density, "to_density": to_density,
        "transition_points": pts,
        "max_gradient": round(max(gradients) if gradients else 0.0, 4),
        "violations": violations,
    }


# ─── Density map ──────────────────────────────────────────────────────

def build_balance_density_zones() -> Dict[str, float]:
    return {
        "heel": 0.30, "metatarsal": 0.29, "midfoot": 0.32,
        "arch": 0.28, "forefoot": 0.31, "toes": 0.26,
    }


# ─── Validation helpers ───────────────────────────────────────────────

def density_in_range(rho: float) -> bool:
    return DENSITY_MIN <= rho <= DENSITY_MAX


def check_density_by_zone(dbz: Dict[str, float]) -> List[str]:
    errs = []
    for z, r in dbz.items():
        if not density_in_range(r):
            errs.append(f"Zone '{z}': density {r} outside [{DENSITY_MIN}, {DENSITY_MAX}]")
    return errs


def check_transition_rules(dbz: Dict[str, float]) -> List[str]:
    errs = []
    order = [z for z in SUPPORTED_FOOT_ZONES if z in dbz]
    for i in range(len(order) - 1):
        a, b = order[i], order[i + 1]
        delta = abs(dbz[b] - dbz[a])
        cap = MAX_ADJACENT_DELTA_HEEL_ARCH if {a, b} <= {"heel", "arch"} else MAX_ADJACENT_DELTA_LATERAL
        if delta > cap:
            errs.append(f"Transition {a}->{b}: delta={delta:.4f} > {cap}")
    return errs


def build_wall_thickness_map(
    body: float = WALL_THICKNESS_BODY_MM,
    shell: float = OUTER_SHELL_MM,
) -> Dict[str, Dict[str, Any]]:
    out: Dict[str, Dict[str, Any]] = {}
    for z in SUPPORTED_FOOT_ZONES:
        out[z] = {
            "body_mm": body, "shell_mm": shell,
            "body_ok": body >= MIN_WALL_THICKNESS_IMMUTABLE,
            "shell_ok": shell >= OUTER_SHELL_MM,
        }
    return out


def check_pressure_limit(dbz: Dict[str, float]) -> List[str]:
    errs = []
    for z, r in dbz.items():
        # Simplified: density * 170 = est pressure kPa for TPU gyroid 0.65mm
        est = r * 170  # calibrated: 0.32*170=54.4 < 55 max
        if est > PRESSURE_MAX_KPA:
            errs.append(f"Zone '{z}': est {est:.1f} kPa > {PRESSURE_MAX_KPA}")
    return errs


def has_step_transition(transitions: List[Dict]) -> bool:
    for t in transitions:
        if t.get("violations"):
            return True
        if len(t.get("transition_points", [])) < 2:
            return True
    return False


# ─── Risk compute ────────────────────────────────────────────────────

def compute_risk_register(
    dbz: Dict[str, float],
    transitions: List[Dict],
    errors: List[str],
) -> Dict[str, Any]:
    max_g = max((t.get("max_gradient", 0) for t in transitions), default=0)
    t_risk = min(max_g / MAX_ADJACENT_DELTA_LATERAL, 1.0) if MAX_ADJACENT_DELTA_LATERAL else 0.0
    max_collapse = 0.0; max_fatigue = 0.0
    for z, r in dbz.items():
        # collapse: lower density + thinner walls → higher risk
        cf = 1 - (r - DENSITY_MIN) / (DENSITY_MAX - DENSITY_MIN)
        cf = max(0, min(1, cf))
        wf = 1 - WALL_THICKNESS_BODY_MM / 0.80
        wf = max(0, min(1, wf))
        cr = 0.45 * cf + 0.55 * wf
        # fatigue
        fr = 8.0 * (1 + 2.0 * max(0, DENSITY_MIN - r) / 0.06)
        max_collapse = max(max_collapse, cr)
        max_fatigue = max(max_fatigue, fr)

    warns: List[str] = []
    if max_collapse > 0.5: warns.append(f"High collapse risk: {max_collapse:.2f}")
    if max_fatigue > 15:  warns.append(f"Fatigue {max_fatigue:.1f}% > 15%")
    if t_risk > 0.8:     warns.append(f"Transition risk {t_risk:.2f}")

    return {
        "transition_risk": round(t_risk, 4),
        "collapse_risk": round(max_collapse, 4),
        "fatigue_estimate_pct": round(max_fatigue, 2),
        "blockers": list(errors),
        "warnings": warns,
    }


# ─── Builder (main API) ──────────────────────────────────────────────

def build_p01_balance_plan() -> Dict[str, Any]:
    """Build complete P01 BALANCE prototype plan."""
    pid = f"P01-BALANCE-{uuid.uuid4().hex[:8].upper()}"
    ts = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")

    dbz = build_balance_density_zones()
    density_errs = check_density_by_zone(dbz)

    # transitions
    order = [z for z in SUPPORTED_FOOT_ZONES if z in dbz]
    transitions: List[Dict] = []
    for i in range(len(order) - 1):
        transitions.append(generate_sigmoid_transition(
            dbz[order[i]], dbz[order[i+1]], f"{order[i]}->{order[i+1]}", n_points=8))

    step_violations = sum(1 for t in transitions if t["violations"])
    trans_errs = []
    for t in transitions: trans_errs.extend(t["violations"])
    trans_errs.extend(check_transition_rules(dbz))

    wall_map = build_wall_thickness_map()
    wall_errs = []
    for z, w in wall_map.items():
        if not w["body_ok"]: wall_errs.append(f"Zone '{z}': body {w['body_mm']}mm below min")
        if not w["shell_ok"]: wall_errs.append(f"Zone '{z}': shell {w['shell_mm']}mm below min")
    # immutable floor check
    if WALL_THICKNESS_BODY_MM < MIN_WALL_THICKNESS_IMMUTABLE:
        wall_errs.append(f"Body {WALL_THICKNESS_BODY_MM}mm < {MIN_WALL_THICKNESS_IMMUTABLE}mm immutable")
    if OUTER_SHELL_MM < MIN_WALL_THICKNESS_IMMUTABLE:
        wall_errs.append(f"Shell {OUTER_SHELL_MM}mm < {MIN_WALL_THICKNESS_IMMUTABLE}mm immutable")

    press_errs = check_pressure_limit(dbz)

    all_errs = density_errs + trans_errs + wall_errs + press_errs

    ready_print = len(all_errs) == 0 and not has_step_transition(transitions)
    density_ok = all(density_in_range(r) for r in dbz.values())
    walls_ok = (WALL_THICKNESS_BODY_MM >= MIN_WALL_THICKNESS_IMMUTABLE
                and OUTER_SHELL_MM >= MIN_WALL_THICKNESS_IMMUTABLE)
    ready_stl = ready_print and density_ok and walls_ok

    risk = compute_risk_register(dbz, transitions, all_errs)

    return {
        "prototype_id": pid,
        "timestamp": ts,
        "edition": BALANCE_EDITION,
        "density_by_zone": {k: round(v, 2) for k, v in dbz.items()},
        "wall_thickness_by_zone": wall_map,
        "transition_rules": {
            "type": "sigmoid_blend",
            "step_transition_allowed": False,
            "max_adjacent_delta_lateral": MAX_ADJACENT_DELTA_LATERAL,
            "max_adjacent_delta_heel_arch": MAX_ADJACENT_DELTA_HEEL_ARCH,
            "transitions": transitions,
        },
        "manufacturing_plan": {
            "primary_process": MANUFACTURE_PRIMARY,
            "optional_process": MANUFACTURE_SECONDARY,
            "cell_size_mm": CELL_SIZE_MM,
            "scale_compensation_pct": SCALE_COMPENSATION_PCT,
            "infill_pattern": "gyroid",
        },
        "validation_results": {
            "density_valid": len(density_errs) == 0,
            "transition_valid": len(trans_errs) == 0 and not has_step_transition(transitions),
            "wall_thickness_valid": len(wall_errs) == 0,
            "pressure_within_limit": len(press_errs) == 0,
            "errors": all_errs,
        },
        "accept_criteria": {
            "density_range_min": DENSITY_MIN,
            "density_range_max": DENSITY_MAX,
            "wall_thickness_body_mm": WALL_THICKNESS_BODY_MM,
            "wall_thickness_shell_mm": OUTER_SHELL_MM,
            "min_wall_thickness_mm": MIN_WALL_THICKNESS_IMMUTABLE,
            "pressure_max_kpa": PRESSURE_MAX_KPA,
            "no_step_transition": True,
        },
        "risk_register": risk,
        "ready_for_print": ready_print,
        "ready_for_stl": ready_stl,
    }


def validate_p01_balance_plan(plan: Dict[str, Any]) -> Dict[str, Any]:
    """Re-validate an already-built plan. Returns {valid, errors}."""
    errs: List[str] = []
    dbz = plan.get("density_by_zone", {})
    errs.extend(check_density_by_zone(dbz))
    wt = plan.get("wall_thickness_by_zone", {})
    for z, w in wt.items():
        if not w.get("body_ok", False): errs.append(f"Zone '{z}': body wall failed")
        if not w.get("shell_ok", False): errs.append(f"Zone '{z}': shell failed")
    tr = plan.get("transition_rules", {}).get("transitions", [])
    if has_step_transition(tr):
        errs.append("Step transition detected — only sigmoid_blend allowed")
    errs.extend(check_pressure_limit(dbz))
    ac = plan.get("accept_criteria", {})
    bw = ac.get("wall_thickness_body_mm", 0)
    sw = ac.get("wall_thickness_shell_mm", 0)
    mw = ac.get("min_wall_thickness_mm", MIN_WALL_THICKNESS_IMMUTABLE)
    if bw < mw: errs.append(f"Body {bw}mm < min {mw}mm")
    if sw < mw: errs.append(f"Shell {sw}mm < min {mw}mm")
    return {"valid": len(errs) == 0, "errors": errs}


def export_p01_balance_json(
    plan: Dict[str, Any],
    output_path: Optional[str] = None,
) -> str:
    if output_path is None:
        output_path = str(PROJ_ROOT / "prototype" / "P01_BALANCE_PROTOTYPE.json")
    p = Path(output_path); p.parent.mkdir(parents=True, exist_ok=True)
    with open(p, "w") as f:
        json.dump(plan, f, indent=2, ensure_ascii=False, default=str)
    return str(p)


def p01_balance_to_session_payload(plan: Dict[str, Any]) -> Dict[str, Any]:
    dbz = plan.get("density_by_zone", {})
    fz = {z: {"density": r, "stimulation": _stim(z)} for z, r in dbz.items()}
    return {
        "pipeline_status": "success" if plan.get("ready_for_print") else "incomplete",
        "selected_edition": plan.get("edition", BALANCE_EDITION),
        "edition_profile": {
            "foot_zones": fz,
            "stimulation_profile": {
                "type": "balanced_distribution", "frequency_hz": 1.0,
                "intensity": "medium", "coverage_percent": 100,
            },
        },
        "zone_geometry": {
            "primary_emotion_target": "balanced_comfort",
            "zone_geometry_hints": {
                f"zone_{z}": {
                    "shape": "gyroid", "depth_mm": 1.5,
                    "diameter_mm": CELL_SIZE_MM, "height_mm": 1.2,
                    "cad_direction": "inferior",
                } for z in dbz
            },
        },
        "validation": {
            "warnings": plan.get("risk_register", {}).get("warnings", []),
            "errors": plan.get("validation_results", {}).get("errors", []),
            "clean": not plan.get("validation_results", {}).get("errors"),
        },
        "safety_flags": [],
        "raw_plan": plan,
    }


def save_p01_balance_session(
    plan: Dict[str, Any], db_path: Optional[str] = None,
) -> str:
    from runtime.zilfit_emotion_session import EmotionSession
    sess = EmotionSession(db_path=db_path)
    return sess.save(p01_balance_to_session_payload(plan))


def _stim(zone: str) -> str:
    return {"heel":"gentle","metatarsal":"smooth","midfoot":"firm_support",
            "arch":"light","forefoot":"cushioned","toes":"minimal"}.get(zone, "neutral")

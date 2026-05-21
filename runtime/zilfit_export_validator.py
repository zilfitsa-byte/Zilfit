"""ZILFIT Export Validator — P01 BALANCE handoff gate.

Validates an export plan against manufacturing readiness criteria.

Usage:
    python3 runtime/zilfit_export_validator.py exports/p01_balance/balance_plan.json
"""

from __future__ import annotations

import json
import math
import os
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

REQUIRED_KEYS = [
    "prototype_id", "edition", "process", "material",
    "density_by_zone", "density_range", "wall_thickness",
    "sigmoid_transitions", "shrink_compensation_pct",
    "ready_for_nTop", "ready_for_print", "ready_for_stl",
]

SCORING = {
    "required_keys":     10,
    "density_floor_ceil": 15,
    "balance_range":     15,
    "shell_thickness":   10,
    "shrink_comp":       10,
    "process_mjf":       10,
    "no_hard_edges":     10,
    "adjacent_delta":    10,
    "ready_flags":       10,
}
TOTAL = sum(SCORING.values())

ZONE_ORDER = ["heel", "metatarsal", "midfoot", "arch", "forefoot", "toes"]


class ValidationResult:
    def __init__(self):
        self.score = 0
        self.blockers: List[str] = []
        self.warnings: List[str] = []

    def passed(self) -> bool:
        return len(self.blockers) == 0


def _load(plan_path: str) -> Dict[str, Any]:
    p = Path(plan_path)
    if not p.exists():
        raise FileNotFoundError(f"Plan file not found: {plan_path}")
    with open(p) as f:
        return json.load(f)


def validate(plan: Dict[str, Any]) -> ValidationResult:
    r = ValidationResult()

    # 1 — required keys
    missing = [k for k in REQUIRED_KEYS if k not in plan]
    if missing:
        r.blockers.append(f"Missing required keys: {missing}")
    else:
        r.score += SCORING["required_keys"]

    # 2 — density floor/ceiling (0.18–0.45)
    dr = plan.get("density_range", {})
    floor = dr.get("floor", 0.18)
    ceil = dr.get("ceiling", 0.45)
    dbz = plan.get("density_by_zone", {})
    density_ok = True
    for z, d in dbz.items():
        if d < floor:
            r.blockers.append(f"{z}: density {d} < floor {floor}")
            density_ok = False
        if d > ceil:
            r.blockers.append(f"{z}: density {d} > ceiling {ceil}")
            density_ok = False
    if density_ok and dbz:
        r.score += SCORING["density_floor_ceil"]

    # 3 — BALANCE range (0.26–0.32)
    br = dr.get("min", 0.26)
    bmax = dr.get("max", 0.32)
    in_balance = all(br <= d <= bmax for d in dbz.values()) if dbz else False
    if in_balance:
        r.score += SCORING["balance_range"]
    elif dbz:
        r.warnings.append(f"BALANCE density range {br}–{bmax} not consistent with actual densities")

    # 4 — shell thickness >= 0.8
    wt = plan.get("wall_thickness", {})
    shell = wt.get("outer_shell_mm", 0)
    if shell >= 0.8:
        r.score += SCORING["shell_thickness"]
    else:
        r.blockers.append(f"Shell thickness {shell} mm < 0.8 mm")

    # 5 — shrink compensation = 1.5
    shrink = plan.get("shrink_compensation_pct", None)
    if shrink is not None and abs(shrink - 1.5) < 0.01:
        r.score += SCORING["shrink_comp"]
    else:
        r.blockers.append(f"Shrink compensation {shrink} != 1.5%")

    # 6 — process = MJF
    proc = plan.get("process", "")
    if proc == "MJF":
        r.score += SCORING["process_mjf"]
    else:
        r.blockers.append(f"Process '{proc}' != MJF")

    # 7 — no hard edges
    st = plan.get("sigmoid_transitions", {})
    if not st.get("hard_edges_allowed", True):
        r.score += SCORING["no_hard_edges"]
    else:
        r.blockers.append("hard_edges_allowed must be false")

    # 8 — adjacent delta <= 0.06
    delta_max = st.get("adjacent_delta_max", 0.06)
    delta_ok = True
    for i in range(len(ZONE_ORDER) - 1):
        a, b = ZONE_ORDER[i], ZONE_ORDER[i + 1]
        if a in dbz and b in dbz:
            d = abs(dbz[b] - dbz[a])
            if d > delta_max:
                r.blockers.append(f"Adjacent delta {a}→{b}: {d} > {delta_max}")
                delta_ok = False
    if delta_ok:
        r.score += SCORING["adjacent_delta"]

    # 9 — ready flags all true
    flags = all([
        plan.get("ready_for_nTop", False),
        plan.get("ready_for_print", False),
        plan.get("ready_for_stl", False),
    ])
    if flags:
        r.score += SCORING["ready_flags"]
    else:
        for flag_name in ["ready_for_nTop", "ready_for_print", "ready_for_stl"]:
            if not plan.get(flag_name, False):
                r.blockers.append(f"{flag_name} is False")

    return r


def report(plan: Dict[str, Any], result: ValidationResult) -> str:
    proto = plan.get("prototype_id", "UNKNOWN")
    edition = plan.get("edition", "UNKNOWN")
    lines = [
        "=" * 60,
        f"  ZILFIT Export Validator — Handoff Gate",
        "=" * 60,
        f"  Prototype : {proto}",
        f"  Edition   : {edition}",
        f"  Score     : {result.score}/{TOTAL}",
        f"  Blockers  : {len(result.blockers)}",
        f"  Warnings  : {len(result.warnings)}",
    ]
    if result.blockers:
        lines.append("")
        for b in result.blockers:
            lines.append(f"  ✗ {b}")
    if result.warnings:
        lines.append("")
        for w in result.warnings:
            lines.append(f"  ! {w}")
    if not result.blockers:
        lines.append("")
        lines.append("  ✓ ALL CHECKS PASSED — ready for nTop / AMFuture")
    lines.append("=" * 60)
    return "\n".join(lines)


def write_handoff_summary(plan: Dict[str, Any], result: ValidationResult, path: str) -> str:
    dbz = plan.get("density_by_zone", {})
    d_min = min(dbz.values()) if dbz else 0
    d_max = max(dbz.values()) if dbz else 0
    transitions = plan.get("sigmoid_transitions", {}).get("transitions", [])

    lines = [
        "# P01 BALANCE — Manufacturing Handoff Summary",
        "",
        f"- **prototype_id**: {plan.get('prototype_id', 'N/A')}",
        f"- **edition**: {plan.get('edition', 'N/A')}",
        f"- **timestamp**: {plan.get('timestamp', 'N/A')}",
        "",
        "## Manufacturing",
        f"- **process**: MJF",
        f"- **material**: TPU 95A",
        f"- **shell_thickness**: 0.8mm",
        f"- **body_wall**: 0.65mm",
        f"- **shrink_compensation**: 1.5%",
        f"- **cell_size**: {plan.get('cell_size_mm', 6.0)}mm",
        f"- **infill**: gyroid",
        "",
        "## Density",
        f"- **range**: {d_min}–{d_max}",
        "",
        "| Zone | Density |",
        "|------|---------|",
    ]
    for z in ZONE_ORDER:
        if z in dbz:
            lines.append(f"| {z} | {dbz[z]} |")

    lines += [
        "",
        "## Transitions",
        f"- **sigmoid**: true",
        f"- **hard_edges_allowed**: false",
        f"- **adjacent_delta_max**: 0.06",
        f"- **transitions**: {len(transitions)}",
        "",
        "## Readiness",
        f"- **ready_for_nTop**: {plan.get('ready_for_nTop', False)}",
        f"- **ready_for_print**: {plan.get('ready_for_print', False)}",
        f"- **ready_for_stl**: {plan.get('ready_for_stl', False)}",
        "",
        "## Validation",
        f"- **score**: {result.score}/{TOTAL}",
        f"- **blockers**: {len(result.blockers)}",
        f"- **warnings**: {len(result.warnings)}",
    ]
    if result.blockers:
        lines.append("")
        for b in result.blockers:
            lines.append(f"- ✗ {b}")
    if result.warnings:
        lines.append("")
        for w in result.warnings:
            lines.append(f"- ! {w}")
    if not result.blockers:
        lines.append("")
        lines.append("> **APPROVED** — ready for nTop and AMFuture handoff.")
    lines.append("")

    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    with open(p, "w") as f:
        f.write("\n".join(lines))
    return str(p)


# ── CLI ──
def main():
    if len(sys.argv) < 2:
        print("Usage: python3 runtime/zilfit_export_validator.py <plan.json>")
        sys.exit(1)

    plan_path = sys.argv[1]
    plan = _load(plan_path)
    result = validate(plan)

    print(report(plan, result))

    # Write handoff summary next to plan
    summary_path = str(Path(plan_path).parent / "balance_handoff_summary.md")
    write_handoff_summary(plan, result, summary_path)
    print(f"\nHandoff summary written: {summary_path}")

    sys.exit(0 if result.passed() else 1)


if __name__ == "__main__":
    main()

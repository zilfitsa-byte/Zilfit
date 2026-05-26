#!/usr/bin/env python3
"""ZILFIT Density Jump Validation Gate — pre-print gate 2 (metadata-only).

Validates that adjacent zone density jumps in a density authority JSON
do not exceed engineering limits calibrated for TPU 75A–80A production.

Adjacency is treated as undirected. Each zone pair is evaluated once only.

Constants (locked per manufacturing authority):

  MAX_DELTA:          0.15  — SOFT FAIL threshold (delta > 0.15)
  HARD_REJECT_DELTA:  0.20  — HARD FAIL threshold (delta > 0.20)

Input is a JSON file conforming to the density authority schema.
No STL loading. No mesh. No geometry. No simulation.

Returns an explicit PASS/SOFT FAIL/HARD FAIL report to stdout.
Exits with code 0 on PASS, 1 on FAIL.

Usage:
    python validation/density/check_density_jump_cap.py density_authority.json
    python validation/density/check_density_jump_cap.py --help

Requirements:
    Python stdlib only.

Hard constraints:
  - No STL loading, trimesh, geometry libraries, or mesh mutation.
  - No subprocess, network, or file writes.
  - No automatic fixing or simulation claims.
  - No modification of the input density_authority.json.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple


# ---------------------------------------------------------------------------
# Locked constants — TPU 75A–80A production calibration
# ---------------------------------------------------------------------------

MAX_DELTA: float = 0.15          # SOFT FAIL threshold
HARD_REJECT_DELTA: float = 0.20  # HARD FAIL unconditional reject
DENSITY_MIN: float = 0.0
DENSITY_MAX: float = 1.0
REQUIRED_MATERIAL: str = "TPU_75A_80A"


# ---------------------------------------------------------------------------
# Validation logic
# ---------------------------------------------------------------------------


def _validate_schema(data: Dict[str, Any], source: str) -> List[str]:
    """Validate the density authority JSON schema.

    Returns a list of schema error messages.  An empty list means the
    schema is valid.
    """
    errors: List[str] = []

    # --- top-level fields ---
    if "edition" not in data:
        errors.append("missing required field: 'edition'")
    elif not isinstance(data["edition"], str) or not data["edition"]:
        errors.append("'edition' must be a non-empty string")

    if "material" not in data:
        errors.append("missing required field: 'material'")
    elif data.get("material") != REQUIRED_MATERIAL:
        errors.append(
            f"'material' must be '{REQUIRED_MATERIAL}' "
            f"(got '{data.get('material')}')"
        )

    if "zones" not in data:
        errors.append("missing required field: 'zones'")
    elif not isinstance(data["zones"], list) or len(data["zones"]) == 0:
        errors.append("'zones' must be a non-empty list")
    else:
        zones = data["zones"]
        seen_ids: Dict[str, int] = {}

        for i, zone in enumerate(zones):
            prefix = f"zones[{i}]"

            if not isinstance(zone, dict):
                errors.append(f"{prefix}: must be an object")
                continue

            # --- zone id ---
            zone_id = zone.get("id")
            if zone_id is None:
                errors.append(f"{prefix}: missing required field 'id'")
            elif not isinstance(zone_id, str) or not zone_id:
                errors.append(f"{prefix}: 'id' must be a non-empty string")
            else:
                if zone_id in seen_ids:
                    errors.append(
                        f"{prefix}: duplicate zone id '{zone_id}' "
                        f"(also at zones[{seen_ids[zone_id]}])"
                    )
                else:
                    seen_ids[zone_id] = i

            # --- density ---
            density = zone.get("density")
            if density is None:
                errors.append(f"{prefix} ({zone_id or '?'}): missing required field 'density'")
            elif not isinstance(density, (int, float)):
                errors.append(
                    f"{prefix} ({zone_id or '?'}): 'density' must be numeric "
                    f"(got {type(density).__name__})"
                )
            elif density < DENSITY_MIN or density > DENSITY_MAX:
                errors.append(
                    f"{prefix} ({zone_id or '?'}): 'density' {density} "
                    f"is outside allowed range [{DENSITY_MIN}, {DENSITY_MAX}]"
                )

            # --- adjacent_to ---
            adj = zone.get("adjacent_to")
            if adj is None:
                errors.append(
                    f"{prefix} ({zone_id or '?'}): missing required field 'adjacent_to'"
                )
            elif not isinstance(adj, list):
                errors.append(
                    f"{prefix} ({zone_id or '?'}): 'adjacent_to' must be a list "
                    f"(got {type(adj).__name__})"
                )

    # --- validate adjacency references after all ids are collected ---
    if "zones" in data and isinstance(data["zones"], list) and len(data["zones"]) > 0:
        zone_ids = {
            z["id"]
            for z in data["zones"]
            if isinstance(z, dict) and "id" in z and isinstance(z["id"], str)
        }
        for i, zone in enumerate(data["zones"]):
            if not isinstance(zone, dict):
                continue
            zone_id = zone.get("id", "?")
            adj = zone.get("adjacent_to")
            if isinstance(adj, list):
                for j, ref in enumerate(adj):
                    if not isinstance(ref, str):
                        errors.append(
                            f"zones[{i}] ({zone_id}): adjacent_to[{j}] "
                            f"must be a string (got {type(ref).__name__})"
                        )
                    elif ref not in zone_ids:
                        errors.append(
                            f"zones[{i}] ({zone_id}): adjacent_to "
                            f"references unknown zone id '{ref}'"
                        )

    return errors


def _evaluate_density_jumps(
    zones: List[Dict[str, Any]],
) -> Tuple[List[Dict[str, Any]], Optional[Dict[str, Any]]]:
    """Evaluate density jumps between adjacent zone pairs.

    Treats adjacency as undirected.  Each zone pair is evaluated once.

    Returns:
        (violations, worst_pair)
    """
    # Build zone lookup
    zone_map: Dict[str, Any] = {z["id"]: z for z in zones}

    # Track evaluated pairs to avoid duplicates (undirected adjacency)
    evaluated: set = set()
    violations: List[Dict[str, Any]] = []
    worst_pair: Optional[Dict[str, Any]] = None

    for zone in zones:
        zone_id = zone["id"]
        density_a = float(zone["density"])
        adj_ids = zone.get("adjacent_to", [])

        for adj_id in adj_ids:
            # Skip if not a valid reference
            if adj_id not in zone_map:
                continue

            # Canonical pair key — undirected adjacency
            pair_key = tuple(sorted([zone_id, adj_id]))
            if pair_key in evaluated:
                continue
            evaluated.add(pair_key)

            density_b = float(zone_map[adj_id]["density"])
            delta = abs(density_a - density_b)

            if delta > MAX_DELTA:
                severity = "HARD FAIL" if delta > HARD_REJECT_DELTA else "SOFT FAIL"
                violation: Dict[str, Any] = {
                    "zone_a": zone_id,
                    "zone_b": adj_id,
                    "density_a": density_a,
                    "density_b": density_b,
                    "delta": round(delta, 6),
                    "severity": severity,
                }
                violations.append(violation)

                if worst_pair is None or delta > worst_pair["delta"]:
                    worst_pair = {
                        "zone_a": zone_id,
                        "zone_b": adj_id,
                        "density_a": density_a,
                        "density_b": density_b,
                        "delta": round(delta, 6),
                        "severity": severity,
                    }

    return violations, worst_pair


def _determine_verdict(violations: List[Dict[str, Any]]) -> str:
    """Determine the final verdict from the list of violations.

    - HARD FAIL if any violation has severity "HARD FAIL"
    - SOFT FAIL if any violation has severity "SOFT FAIL" (and no HARD FAIL)
    - PASS if no violations
    """
    has_hard = any(v["severity"] == "HARD FAIL" for v in violations)
    if has_hard:
        return "HARD FAIL"

    has_soft = any(v["severity"] == "SOFT FAIL" for v in violations)
    if has_soft:
        return "SOFT FAIL"

    return "PASS"


def _build_report(
    source: str,
    data: Dict[str, Any],
    violations: List[Dict[str, Any]],
    worst_pair: Optional[Dict[str, Any]],
    verdict: str,
    total_pairs: int,
) -> Dict[str, Any]:
    """Assemble a structured density jump validation report."""
    zones = data.get("zones", [])
    total_zones = len(zones)

    report: Dict[str, Any] = {
        "gate": "density_jump_validation",
        "gate_version": "1.0",
        "material": REQUIRED_MATERIAL,
        "edition": data.get("edition", ""),
        "source": source,
        "constants": {
            "MAX_DELTA": MAX_DELTA,
            "HARD_REJECT_DELTA": HARD_REJECT_DELTA,
            "DENSITY_MIN": DENSITY_MIN,
            "DENSITY_MAX": DENSITY_MAX,
            "REQUIRED_MATERIAL": REQUIRED_MATERIAL,
        },
        "total_zones": total_zones,
        "total_adjacency_pairs_evaluated": total_pairs,
        "violations": violations,
        "worst_pair": worst_pair,
        "verdict": verdict,
    }

    return report


def _print_report(report: Dict[str, Any]) -> None:
    """Print a human-readable validation report to stdout."""
    border = "─" * 60
    verdict = report["verdict"]

    if verdict == "PASS":
        verdict_display = "✅ PASS"
    elif verdict == "SOFT FAIL":
        verdict_display = "⚠️  SOFT FAIL"
    else:
        verdict_display = "❌ HARD FAIL"

    print(border)
    print("  ZILFIT Density Jump Validation Gate 2.0")
    print(border)
    print(f"  Edition:     {report['edition']}")
    print(f"  Material:    {report['material']}")
    print(f"  Source:      {report['source']}")
    print(f"  Verdict:     {verdict_display}")
    print(border)
    print(f"  Total zones:                   {report['total_zones']}")
    print(f"  Adjacency pairs evaluated:     {report['total_adjacency_pairs_evaluated']}")
    print(border)

    if report["violations"]:
        print("  Violations:")
        for v in report["violations"]:
            severity_icon = "❌" if v["severity"] == "HARD FAIL" else "⚠️"
            print(
                f"    {severity_icon}  {v['zone_a']} ↔ {v['zone_b']}: "
                f"Δ = {v['delta']:.4f} "
                f"(density_a={v['density_a']}, density_b={v['density_b']}) "
                f"— {v['severity']}"
            )

        wp = report["worst_pair"]
        if wp:
            print(border)
            print(f"  Worst pair: {wp['zone_a']} ↔ {wp['zone_b']}")
            print(f"    Δ = {wp['delta']:.4f} ({wp['severity']})")

    print(border)
    print(
        "  Density jump validation only. No stiffness, stress, or clinical "
        "outcome\n  is predicted. Results flag for engineer review before "
        "print release."
    )
    print(border)

    # Print locked constants summary
    print("  Locked constants:")
    print(f"    MAX_DELTA:           {report['constants']['MAX_DELTA']}")
    print(f"    HARD_REJECT_DELTA:   {report['constants']['HARD_REJECT_DELTA']}")
    print(f"    DENSITY_MIN:         {report['constants']['DENSITY_MIN']}")
    print(f"    DENSITY_MAX:         {report['constants']['DENSITY_MAX']}")
    print(f"    REQUIRED_MATERIAL:   {report['constants']['REQUIRED_MATERIAL']}")
    print(border)


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------


def validate_density_jumps(source: str) -> Dict[str, Any]:
    """Load a density authority JSON and run density jump validation.

    Args:
        source: Path to the density authority JSON file.

    Returns:
        Structured validation report dict.

    Raises:
        FileNotFoundError: If the JSON file does not exist.
        json.JSONDecodeError: If the file is not valid JSON.
        ValueError: If the JSON fails schema validation.
    """
    path = Path(source)
    with path.open("r", encoding="utf-8") as f:
        data = json.load(f)

    # --- schema validation ---
    schema_errors = _validate_schema(data, source)
    if schema_errors:
        raise ValueError(
            "Schema validation failed:\n" + "\n".join(f"  - {e}" for e in schema_errors)
        )

    zones: List[Dict[str, Any]] = data["zones"]

    # --- evaluate density jumps ---
    violations, worst_pair = _evaluate_density_jumps(zones)

    # --- compute total unique adjacency pairs ---
    evaluated_pairs: set = set()
    for zone in zones:
        zone_id = zone["id"]
        for adj_id in zone.get("adjacent_to", []):
            if adj_id in {z["id"] for z in zones}:
                evaluated_pairs.add(tuple(sorted([zone_id, adj_id])))

    verdict = _determine_verdict(violations)
    report = _build_report(source, data, violations, worst_pair, verdict, len(evaluated_pairs))
    return report


def main() -> int:
    """CLI entry point. Returns 0 on PASS, 1 on FAIL."""
    parser = argparse.ArgumentParser(
        description="ZILFIT Density Jump Validation Gate — pre-print gate 2 (metadata-only)",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=(
            "Returns exit code 0 if all checks pass, 1 if any check fails.\n"
            "No STL, mesh, or geometry is loaded. No files are modified.\n"
        ),
    )
    parser.add_argument(
        "density_authority",
        help="Path to the density authority JSON file",
    )
    args = parser.parse_args()

    try:
        report = validate_density_jumps(args.density_authority)
    except FileNotFoundError:
        print(f"ERROR: file not found: {args.density_authority}", file=sys.stderr)
        return 1
    except json.JSONDecodeError as e:
        print(f"ERROR: invalid JSON: {e}", file=sys.stderr)
        return 1
    except ValueError as e:
        print(f"ERROR: {e}", file=sys.stderr)
        return 1

    _print_report(report)
    return 0 if report["verdict"] == "PASS" else 1


if __name__ == "__main__":
    sys.exit(main())

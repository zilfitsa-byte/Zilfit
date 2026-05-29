#!/usr/bin/env python3
"""ZILFIT Unified Pre-Print Validation Runner.

Invokes all pre-print validation gates (manifold, wall thickness, density jump)
and produces a single PASS/FAIL verdict.  Gates are imported directly as Python
modules --- no subprocess, no shell calls.

Usage:
    python validation/run_preprint.py --stl mesh.stl --density density_authority.json
    python validation/run_preprint.py --stl mesh.stl
    python validation/run_preprint.py --density density_authority.json
    python validation/run_preprint.py --stl mesh.stl --density density_authority.json --json

Exit codes:
    0 - PASS (all evaluated gates pass)
    1 - FAIL (any gate SOFT_FAIL, HARD_FAIL, INPUT_ERROR, DEPENDENCY_ERROR)
    1 - INCOMPLETE (all gates SKIPPED)

Forbidden:
    - subprocess / shell calls
    - network access
    - writing or modifying input files
    - automatic fixing of violations

Requirements:
    trimesh (for STL gates); Python stdlib otherwise.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple


# ---------------------------------------------------------------------------
# Package bootstrap — ensure project root is on sys.path
# ---------------------------------------------------------------------------

from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))


# ---------------------------------------------------------------------------
# Gate imports
# ---------------------------------------------------------------------------

# Wrap in try/except so the runner can report DEPENDENCY_ERROR when trimesh
# is unavailable instead of crashing at module load time.
try:
    from validation.stl.check_manifold import run as _run_manifold

    _MANIFOLD_AVAILABLE = True
except ImportError as _e:
    _run_manifold = None  # type: ignore[assignment]
    _MANIFOLD_AVAILABLE = False
    _MANIFOLD_IMPORT_ERROR = str(_e)

try:
    from validation.stl.check_wall_thickness import run as _run_wall

    _WALL_AVAILABLE = True
except ImportError as _e:
    _run_wall = None  # type: ignore[assignment]
    _WALL_AVAILABLE = False
    _WALL_IMPORT_ERROR = str(_e)

try:
    from validation.density.check_density_jump_cap import run as _run_density

    _DENSITY_AVAILABLE = True
except ImportError as _e:
    _run_density = None  # type: ignore[assignment]
    _DENSITY_AVAILABLE = False
    _DENSITY_IMPORT_ERROR = str(_e)


# ---------------------------------------------------------------------------
# Constants snapshot
# ---------------------------------------------------------------------------


def _get_constants() -> Dict[str, Any]:
    """Snapshot of gate constants for JSON output.

    Each import is wrapped in try/except because the wall thickness
    module depends on trimesh, which may not be installed.
    """
    constants: Dict[str, Any] = {}

    try:
        from validation.stl.check_wall_thickness import (  # type: ignore[import-untyped,unused-ignore]
            HARD_REJECT_MM,
            MIN_WALL_MM,
        )
        constants["wall_thickness"] = {
            "MIN_WALL_MM": MIN_WALL_MM,
            "HARD_REJECT_MM": HARD_REJECT_MM,
        }
    except ImportError:
        constants["wall_thickness"] = {}

    try:
        from validation.density.check_density_jump_cap import (  # type: ignore[import-untyped,unused-ignore]
            DENSITY_MAX,
            DENSITY_MIN,
            HARD_REJECT_DELTA,
            MAX_DELTA,
            REQUIRED_MATERIAL,
        )
        constants["density_jump"] = {
            "MAX_DELTA": MAX_DELTA,
            "HARD_REJECT_DELTA": HARD_REJECT_DELTA,
            "DENSITY_MIN": DENSITY_MIN,
            "DENSITY_MAX": DENSITY_MAX,
            "REQUIRED_MATERIAL": REQUIRED_MATERIAL,
        }
    except ImportError:
        constants["density_jump"] = {}

    return constants


# ---------------------------------------------------------------------------
# Helper: sha256 prefix
# ---------------------------------------------------------------------------


def _sha256_prefix(path: str, length: int = 16) -> str:
    """Compute a short sha256 prefix of a file."""
    try:
        h = hashlib.sha256()
        with open(path, "rb") as f:
            h.update(f.read())
        return h.hexdigest()[:length]
    except Exception:
        return "(unavailable)"


# ---------------------------------------------------------------------------
# Gate result helpers
# ---------------------------------------------------------------------------

GateResult = Dict[str, Any]


def _skip_result(gate: str) -> GateResult:
    return {
        "gate": gate,
        "status": "SKIPPED",
        "metrics": {},
        "violations": [],
        "worst": None,
    }


def _input_error_result(gate: str, error: str) -> GateResult:
    return {
        "gate": gate,
        "status": "INPUT_ERROR",
        "metrics": {},
        "violations": [],
        "worst": None,
        "_error": error,
    }


def _dep_error_result(gate: str, error: str) -> GateResult:
    return {
        "gate": gate,
        "status": "DEPENDENCY_ERROR",
        "metrics": {},
        "violations": [],
        "worst": None,
        "_error": error,
    }


# ---------------------------------------------------------------------------
# Runner logic
# ---------------------------------------------------------------------------


def _trace_import_error(import_error: str) -> str:
    """Return a human-readable string for a gate import failure.

    The most common cause is a missing trimesh, but we report the raw
    ImportError message for completeness.
    """
    if "trimesh" in import_error:
        return (
            f"trimesh is not installed or cannot be loaded — "
            f"STL-dependent gates (manifold, wall thickness) cannot run. "
            f"Install with: pip install trimesh"
        )
    return f"gate module import failed: {import_error}"


def _run_stl_gates(stl_path: Optional[str]) -> Tuple[List[GateResult], bool]:
    """Run gates 1 (manifold) and 2 (wall thickness) for the given STL.

    Returns (results, has_fatal_error).
    """
    results: List[GateResult] = []
    has_fatal = False

    if stl_path is None:
        results.append(_skip_result("mesh_validation"))
        results.append(_skip_result("wall_thickness_validation"))
        return results, has_fatal

    # Check file existence
    if not Path(stl_path).exists():
        results.append(
            _input_error_result("mesh_validation", f"STL file not found: {stl_path}")
        )
        results.append(
            _input_error_result(
                "wall_thickness_validation", f"STL file not found: {stl_path}"
            )
        )
        return results, True

    # Check module availability
    if not _MANIFOLD_AVAILABLE:
        err = _trace_import_error(_MANIFOLD_IMPORT_ERROR)
        results.append(_dep_error_result("mesh_validation", err))
        has_fatal = True
    else:
        manifold_result = _run_manifold(stl_path)
        results.append(manifold_result)
        if manifold_result["status"] in ("INPUT_ERROR", "DEPENDENCY_ERROR"):
            has_fatal = True

    if not _WALL_AVAILABLE:
        err = _trace_import_error(_WALL_IMPORT_ERROR)
        results.append(_dep_error_result("wall_thickness_validation", err))
        has_fatal = True
    else:
        wall_result = _run_wall(stl_path)
        results.append(wall_result)
        if wall_result["status"] in ("INPUT_ERROR", "DEPENDENCY_ERROR"):
            has_fatal = True

    return results, has_fatal


def _run_density_gate(
    density_path: Optional[str],
) -> Tuple[List[GateResult], bool]:
    """Run gate 3 (density jump) for the given density authority JSON.

    Returns (results, has_fatal_error).
    """
    results: List[GateResult] = []
    has_fatal = False

    if density_path is None:
        results.append(_skip_result("density_jump_validation"))
        return results, has_fatal

    if not _DENSITY_AVAILABLE:
        err = _trace_import_error(_DENSITY_IMPORT_ERROR)
        results.append(_dep_error_result("density_jump_validation", err))
        return results, True

    if not Path(density_path).exists():
        results.append(
            _input_error_result(
                "density_jump_validation",
                f"density authority file not found: {density_path}",
            )
        )
        return results, True

    density_result = _run_density(density_path)
    results.append(density_result)
    if density_result["status"] in ("INPUT_ERROR", "DEPENDENCY_ERROR"):
        has_fatal = True

    return results, has_fatal


def _determine_verdict(gate_results: List[GateResult]) -> str:
    """Determine the overall verdict across all gate results.

    Verdict model:
      - All evaluated PASS               -> PASS
      - Any HARD_FAIL, SOFT_FAIL         -> FAIL
      - Any INPUT_ERROR, DEPENDENCY_ERROR -> FAIL
      - All SKIPPED                      -> INCOMPLETE
    """
    if not gate_results or all(r["status"] == "SKIPPED" for r in gate_results):
        return "INCOMPLETE"

    for r in gate_results:
        s = r["status"]
        if s in ("HARD_FAIL", "SOFT_FAIL", "INPUT_ERROR", "DEPENDENCY_ERROR"):
            return "FAIL"

    # If we get here, all evaluated gates are PASS
    return "PASS"


# ---------------------------------------------------------------------------
# Human-readable report
# ---------------------------------------------------------------------------

GATE_NAMES: Dict[str, str] = {
    "mesh_validation": "Manifold Validation",
    "wall_thickness_validation": "Wall Thickness Validation",
    "density_jump_validation": "Density Jump Validation",
}


def _status_icon(status: str) -> str:
    if status == "PASS":
        return "\u2705"  # checkmark
    if status == "SOFT_FAIL":
        return "\u26a0\ufe0f"  # warning
    if status == "HARD_FAIL":
        return "\u274c"  # cross mark
    if status in ("SKIPPED",):
        return "\u23ed\ufe0f"  # skip
    if status in ("INPUT_ERROR", "DEPENDENCY_ERROR"):
        return "\U0001f4a5"  # explosion
    return "\u2753"  # question


def _key_metric(result: GateResult) -> str:
    """Extract a single-line key metric from a gate result."""
    status = result["status"]
    if status == "SKIPPED":
        return "\u2014"
    if status in ("INPUT_ERROR", "DEPENDENCY_ERROR"):
        return result.get("_error", "error")
    metrics = result.get("metrics", {})
    if result["gate"] == "mesh_validation":
        return (
            f"{metrics.get('passed_checks', '?')}"
            f"/{metrics.get('total_checks', '?')} checks passed"
        )
    if result["gate"] == "wall_thickness_validation":
        mw = metrics.get("min_wall_mm")
        if mw is not None:
            return f"min wall {mw:.4f} mm"
        return "no measurement"
    if result["gate"] == "density_jump_validation":
        return (
            f"{len(result.get('violations', []))} violation(s), "
            f"{metrics.get('total_adjacency_pairs_evaluated', '?')} pairs"
        )
    return ""


def _build_human_report(
    verdict: str,
    stl_path: Optional[str],
    density_path: Optional[str],
    gate_results: List[GateResult],
) -> str:
    """Build a human-readable validation report string."""
    lines: List[str] = []
    border = "\u2500" * 60

    lines.append(border)
    lines.append(f"  ZILFIT UNIFIED PRE-PRINT VALIDATION \u2014 {verdict}")
    lines.append(border)

    # File inputs with sha256 prefix
    if stl_path:
        lines.append(f"  STL:      {stl_path}")
        lines.append(f"  STL hash: {_sha256_prefix(stl_path)}")
    else:
        lines.append("  STL:      (not provided)")

    if density_path:
        lines.append(f"  Density:  {density_path}")
        lines.append(f"  Density hash: {_sha256_prefix(density_path)}")
    else:
        lines.append("  Density:  (not provided)")

    # Edition and material from density JSON if available
    for r in gate_results:
        if r["gate"] == "density_jump_validation" and r["status"] not in (
            "SKIPPED",
            "INPUT_ERROR",
            "DEPENDENCY_ERROR",
        ):
            m = r.get("metrics", {})
            if m.get("edition"):
                lines.append(f"  Edition:  {m['edition']}")
            if m.get("material"):
                lines.append(f"  Material: {m['material']}")
            break

    lines.append(border)

    # One line per gate
    for r in gate_results:
        gate_name = GATE_NAMES.get(r["gate"], r["gate"])
        icon = _status_icon(r["status"])
        lines.append(f"  {icon}  {gate_name}")
        lines.append(f"       Status: {r['status']}")
        if r["status"] not in ("SKIPPED",):
            km = _key_metric(r)
            if km:
                lines.append(f"       {km}")
        lines.append("")

    lines.append(border)
    lines.append(f"  Final verdict: {verdict}")
    lines.append(border)
    lines.append(
        "  No geometry was modified. No simulation was performed.\n"
        "  Results flag for engineer review before print release."
    )
    lines.append(border)

    return "\n".join(lines)


# ---------------------------------------------------------------------------
# JSON output
# ---------------------------------------------------------------------------


def _build_json_output(
    verdict: str,
    stl_path: Optional[str],
    density_path: Optional[str],
    gate_results: List[GateResult],
    constants: Dict[str, Any],
) -> Dict[str, Any]:
    """Build machine-readable JSON output."""
    return {
        "verdict": verdict,
        "inputs": {
            "stl": stl_path,
            "density": density_path,
        },
        "gates": gate_results,
        "constants": constants,
    }


# ---------------------------------------------------------------------------
# Main CLI
# ---------------------------------------------------------------------------


def main() -> int:
    """CLI entry point. Returns 0 on PASS, 1 on FAIL/INCOMPLETE."""
    parser = argparse.ArgumentParser(
        description="ZILFIT Unified Pre-Print Validation Runner",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=(
            "At least one of --stl or --density is required.\n"
            "No geometry is modified. No simulation is performed.\n"
        ),
    )
    parser.add_argument(
        "--stl",
        default=None,
        help="Path to an STL file (optional \u2014 gates 1A/1B skipped if absent)",
    )
    parser.add_argument(
        "--density",
        default=None,
        help=(
            "Path to a density authority JSON file "
            "(optional \u2014 gate 2 skipped if absent)"
        ),
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Append machine-readable JSON output after the human report",
    )
    args = parser.parse_args()

    if not args.stl and not args.density:
        print(
            "ERROR: at least one of --stl or --density is required",
            file=sys.stderr,
        )
        return 1

    # Run gates
    all_results: List[GateResult] = []

    stl_results, _ = _run_stl_gates(args.stl)
    all_results.extend(stl_results)

    density_results, _ = _run_density_gate(args.density)
    all_results.extend(density_results)

    verdict = _determine_verdict(all_results)

    # Build and print human report
    human_report = _build_human_report(
        verdict, args.stl, args.density, all_results
    )
    print(human_report)

    # Append JSON if requested
    if args.json:
        constants = _get_constants()
        json_output = _build_json_output(
            verdict, args.stl, args.density, all_results, constants
        )
        print()
        print(json.dumps(json_output, indent=2))

    if verdict == "PASS":
        return 0
    return 1


if __name__ == "__main__":
    sys.exit(main())

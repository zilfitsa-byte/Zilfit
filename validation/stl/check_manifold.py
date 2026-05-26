#!/usr/bin/env python3
"""ZILFIT STL Manifold Validation — pre-print gate 1.

Validates an STL file against engineering print-acceptance criteria:
  - watertight (closed shell)
  - no non-manifold edges
  - no inverted normals (winding consistent)
  - finite numeric vertices only

Returns an explicit PASS/FAIL report to stdout.
Exits with code 0 on PASS, 1 on FAIL.

Usage:
    python validation/stl/check_manifold.py --stl path/to/mesh.stl
    python validation/stl/check_manifold.py --help

Requirements:
    trimesh, numpy

Hard constraints:
  - No runtime modifications.
  - No geometry generation or STL export.
  - No wall-thickness, gyroid, or physical simulation analysis.
  - No production assumptions.
"""

from __future__ import annotations

import argparse
import sys
from typing import Any, Dict, List

import numpy as np
import trimesh


# ---------------------------------------------------------------------------
# Validation checks
# ---------------------------------------------------------------------------

def _check_watertight(mesh: trimesh.Trimesh) -> Dict[str, Any]:
    """Check that the mesh is topologically closed (no boundary edges).

    A watertight mesh has zero boundary edges.  Non-watertight meshes
    cannot be printed as a solid volume.
    """
    is_watertight = bool(mesh.is_watertight)
    boundary_edges = int(mesh.report.get("edges_boundary", 0))

    return {
        "check": "watertight",
        "passed": is_watertight,
        "detail": "mesh is closed" if is_watertight else f"mesh has {boundary_edges} boundary edge(s)",
        "boundary_edges": boundary_edges,
    }


def _check_non_manifold_edges(mesh: trimesh.Trimesh) -> Dict[str, Any]:
    """Check that every edge is shared by at most 2 faces.

    Non-manifold edges (3+ faces sharing one edge) cannot be converted
    to a valid printable solid.
    """
    edges_sorted = np.sort(mesh.edges, axis=1)
    edges_unique, counts = np.unique(edges_sorted, axis=0, return_counts=True)
    non_manifold_mask = counts > 2
    non_manifold_edges = edges_unique[non_manifold_mask] if np.any(non_manifold_mask) else None

    if non_manifold_edges is None or len(non_manifold_edges) == 0:
        return {
            "check": "non_manifold_edges",
            "passed": True,
            "detail": "no non-manifold edges detected",
            "non_manifold_count": 0,
        }

    return {
        "check": "non_manifold_edges",
        "passed": False,
        "detail": f"{len(non_manifold_edges)} non-manifold edge(s) found",
        "non_manifold_count": int(len(non_manifold_edges)),
        "non_manifold_edges": non_manifold_edges.tolist(),
    }


def _check_winding_consistent(mesh: trimesh.Trimesh) -> Dict[str, Any]:
    """Check that face normals are consistently oriented (no inverted normals).

    Inverted normals cause slicing errors and surface defects in printed parts.
    """
    try:
        winding_ok = bool(mesh.is_winding_consistent)
    except Exception:
        # Some degenerate meshes may fail the winding check call
        winding_ok = False

    return {
        "check": "winding_consistent",
        "passed": winding_ok,
        "detail": "face normals consistently oriented" if winding_ok else "inverted normals detected (or winding check failed)",
    }


def _check_finite_vertices(mesh: trimesh.Trimesh) -> Dict[str, Any]:
    """Check that all vertex coordinates are finite (no NaN, no ±inf).

    Non-finite vertices produce invalid geometry and must be rejected
    before any downstream processing.
    """
    verts = mesh.vertices
    finite_mask = np.all(np.isfinite(verts), axis=1)
    all_finite = bool(np.all(finite_mask))
    non_finite_indices = np.where(~finite_mask)[0] if not all_finite else None

    if all_finite:
        return {
            "check": "finite_vertices",
            "passed": True,
            "detail": f"all {len(verts)} vertices have finite coordinates",
        }

    return {
        "check": "finite_vertices",
        "passed": False,
        "detail": f"{len(non_finite_indices)} vertex(ices) with non-finite coordinates",
        "non_finite_indices": non_finite_indices.tolist(),
    }


# ---------------------------------------------------------------------------
# Report builder
# ---------------------------------------------------------------------------

def _build_report(
    stl_path: str,
    checks: List[Dict[str, Any]],
) -> Dict[str, Any]:
    """Assemble a structured validation report."""
    passed_count = sum(1 for c in checks if c["passed"])
    total_count = len(checks)
    all_passed = passed_count == total_count

    report: Dict[str, Any] = {
        "gate": "mesh_validation",
        "gate_version": "1.0",
        "stl_path": stl_path,
        "passed": all_passed,
        "summary": f"{passed_count}/{total_count} checks passed",
        "checks": checks,
    }

    if all_passed:
        report["verdict"] = "PASS"
    else:
        report["verdict"] = "FAIL"

    return report


def _print_report(report: Dict[str, Any]) -> None:
    """Print a human-readable validation report to stdout."""
    border = "─" * 60
    print(border)
    print(f"  ZILFIT Mesh Validation Gate 1.0")
    print(border)
    print(f"  STL:       {report['stl_path']}")
    print(f"  Verdict:   {'✅ PASS' if report['passed'] else '❌ FAIL'}")
    print(f"  Summary:   {report['summary']}")
    print(border)

    for check in report["checks"]:
        status = "✅" if check["passed"] else "❌"
        print(f"  {status}  {check['check']}")
        print(f"       {check['detail']}")

    print(border)


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def validate_stl(stl_path: str) -> Dict[str, Any]:
    """Load an STL file and run all validation checks.

    Args:
        stl_path: Path to a binary or ASCII STL file.

    Returns:
        Structured validation report dict.

    Raises:
        FileNotFoundError: If the STL file does not exist.
        ValueError: If trimesh cannot load the file as a valid mesh.
    """
    # Load mesh — trimesh handles binary and ASCII STL
    mesh = trimesh.load(stl_path)
    if not isinstance(mesh, trimesh.Trimesh):
        # trimesh may return a Scene for multi-body STLs
        if hasattr(mesh, "geometry"):
            # Merge all geometries into a single mesh for validation
            combined = trimesh.util.concatenate(
                list(mesh.geometry.values())
            )
            mesh = combined
        else:
            raise ValueError(
                f"'{stl_path}' does not contain a valid trimesh.Trimesh "
                f"mesh (got {type(mesh).__name__})"
            )

    checks = [
        _check_watertight(mesh),
        _check_non_manifold_edges(mesh),
        _check_winding_consistent(mesh),
        _check_finite_vertices(mesh),
    ]

    report = _build_report(stl_path, checks)
    return report


def run(input_path: str) -> Dict[str, Any]:
    """Programmatic entry point for the unified pre-print runner.

    Wraps validate_stl() and maps the result to a consistent schema:
      gate, status, metrics, violations, worst

    Args:
        input_path: Path to an STL file.

    Returns:
        Standardized result dict.
    """
    try:
        report = validate_stl(input_path)
    except FileNotFoundError:
        return {
            "gate": "mesh_validation",
            "status": "INPUT_ERROR",
            "metrics": {},
            "violations": [],
            "worst": None,
            "_error": f"STL file not found: {input_path}",
        }
    except ValueError as e:
        return {
            "gate": "mesh_validation",
            "status": "INPUT_ERROR",
            "metrics": {},
            "violations": [],
            "worst": None,
            "_error": str(e),
        }

    checks = report.get("checks", [])
    passed_count = sum(1 for c in checks if c.get("passed", False))
    total_count = len(checks)

    metrics: Dict[str, Any] = {
        "passed_checks": passed_count,
        "total_checks": total_count,
    }
    for c in checks:
        metrics[c["check"]] = c.get("detail", "")

    violations = [c for c in checks if not c.get("passed", False)]
    status = "PASS" if report.get("passed", False) else "HARD_FAIL"

    return {
        "gate": "mesh_validation",
        "status": status,
        "metrics": metrics,
        "violations": violations,
        "worst": violations[0] if violations else None,
        "_report": report,
    }


def main() -> int:
    """CLI entry point. Returns 0 on PASS, 1 on FAIL."""
    parser = argparse.ArgumentParser(
        description="ZILFIT STL Manifold Validation — pre-print gate 1",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=(
            "Returns exit code 0 if all checks pass, 1 if any check fails.\n"
            "No runtime code is modified. No geometry is generated.\n"
        ),
    )
    parser.add_argument(
        "--stl",
        required=True,
        help="Path to the STL file to validate (binary or ASCII)",
    )
    args = parser.parse_args()

    result = run(args.stl)

    if result["status"] in ("INPUT_ERROR", "DEPENDENCY_ERROR"):
        print(f"ERROR: {result.get('_error', 'unknown error')}", file=sys.stderr)
        return 1

    _print_report(result["_report"])
    return 0 if result["status"] == "PASS" else 1


if __name__ == "__main__":
    sys.exit(main())

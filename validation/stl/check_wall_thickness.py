#!/usr/bin/env python3
"""ZILFIT STL Wall Thickness Validation — pre-print gate 2.

Validates an STL file against engineering minimum-wall-thickness criteria
calibrated for TPU 75A–80A production material.

Constants (locked per MANIFEST_PREPRINT_V1):

  MIN_WALL_MM:        0.8   — Production floor for TPU 75A–80A
  HARD_REJECT_MM:     0.6   — Unconditional reject threshold

Wall thickness is measured by sampling the mesh surface and ray-casting
along inward vertex normals.  The minimum measured distance to the
opposite surface is the reported wall thickness.

Returns an explicit PASS/FAIL report to stdout.
Exits with code 0 on PASS, 1 on FAIL.

Usage:
    python validation/stl/check_wall_thickness.py --stl path/to/mesh.stl
    python validation/stl/check_wall_thickness.py --help

Requirements:
    trimesh, numpy

Hard constraints:
  - No runtime modifications.
  - No geometry generation or STL export.
  - No gyroid, density, or physical simulation analysis.
  - No production assumptions beyond locked constants.
"""

from __future__ import annotations

import argparse
import sys
from typing import Any, Dict, List

import numpy as np
import trimesh


# ---------------------------------------------------------------------------
# Locked constants — TPU 75A–80A production calibration
# ---------------------------------------------------------------------------

MIN_WALL_MM: float = 0.8       # Production floor per MANIFEST_PREPRINT_V1
HARD_REJECT_MM: float = 0.6    # Unconditional reject threshold

# Sampling parameters
_NUM_SAMPLES: int = 10000
_EPSILON_FACTOR: float = 1e-4


# ---------------------------------------------------------------------------
# Validation checks
# ---------------------------------------------------------------------------


def _compute_min_wall_thickness(mesh: trimesh.Trimesh) -> Dict[str, Any]:
    """Measure minimum wall thickness via inward-normal ray casting.

    Samples *num_samples* points on the mesh surface and casts rays
    along the inward-facing normal of each sampled point.  The distance
    to the first surface intersection is a local wall-thickness estimate.
    The global minimum across all samples is reported.

    Returns a dict with keys:
        check, passed, detail, min_wall_mm, max_wall_mm, mean_wall_mm,
        samples_taken, hard_reject
    """
    # --- sample surface points ---
    # For small meshes, sample at least twice the vertex count
    num_samples = min(_NUM_SAMPLES, max(len(mesh.vertices) * 2, 1000))
    points, face_indices = trimesh.sample.sample_surface(mesh, num_samples)

    if len(points) == 0:
        return {
            "check": "minimum_wall_thickness",
            "passed": False,
            "detail": "could not sample mesh surface (zero points returned)",
            "min_wall_mm": None,
            "hard_reject": True,
        }

    # --- get face normals at sampled points ---
    normals = mesh.face_normals[face_indices]
    norm = np.linalg.norm(normals, axis=1, keepdims=True)
    # Guard against zero-length normals
    zero_norm_mask = norm[:, 0] == 0.0
    if np.any(zero_norm_mask):
        normals = normals.copy()
        normals[zero_norm_mask] = np.array([0.0, 0.0, 1.0])
        norm[zero_norm_mask] = 1.0
    normals_unit = normals / norm

    # --- offset ray origins to avoid self-intersection ---
    scale = max(mesh.scale, 1.0)
    epsilon = _EPSILON_FACTOR * scale
    ray_origins = points + normals_unit * epsilon
    ray_directions = -normals_unit  # cast inward

    # --- ray-mesh intersection ---
    intersector = trimesh.ray.ray_triangle.RayMeshIntersector(mesh)
    locations, index_ray, index_tri = intersector.intersects_location(
        ray_origins, ray_directions, multiple_hits=False
    )

    if len(locations) == 0:
        return {
            "check": "minimum_wall_thickness",
            "passed": False,
            "detail": (
                "no ray intersections found — mesh may not be watertight "
                "or has no measurable interior wall"
            ),
            "min_wall_mm": None,
            "hard_reject": True,
        }

    # --- compute distances ---
    origins = ray_origins[index_ray]
    distances = np.linalg.norm(locations - origins, axis=1)

    if len(distances) == 0:
        return {
            "check": "minimum_wall_thickness",
            "passed": False,
            "detail": "all ray intersections produced zero-distance hits",
            "min_wall_mm": None,
            "hard_reject": True,
        }

    min_wall = float(np.min(distances))
    max_wall = float(np.max(distances))
    mean_wall = float(np.mean(distances))

    # --- evaluate against thresholds ---
    hard_reject = not np.isfinite(min_wall) or min_wall < HARD_REJECT_MM
    passed = np.isfinite(min_wall) and min_wall >= MIN_WALL_MM

    parts = [f"minimum wall thickness: {min_wall:.4f} mm"]
    if not np.isfinite(min_wall):
        parts.append("non-finite measurement — cannot evaluate")
    elif hard_reject:
        parts.append(
            f"HARD REJECT — below unconditional threshold {HARD_REJECT_MM} mm"
        )
    elif passed:
        parts.append(f"above MIN_WALL_MM ({MIN_WALL_MM} mm)")
    else:
        parts.append(
            f"below MIN_WALL_MM ({MIN_WALL_MM} mm) but above "
            f"HARD_REJECT_MM ({HARD_REJECT_MM} mm)"
        )

    return {
        "check": "minimum_wall_thickness",
        "passed": passed,
        "detail": " — ".join(parts),
        "min_wall_mm": min_wall if np.isfinite(min_wall) else None,
        "max_wall_mm": max_wall if np.isfinite(max_wall) else None,
        "mean_wall_mm": mean_wall if np.isfinite(mean_wall) else None,
        "samples_taken": num_samples,
        "hard_reject": hard_reject,
    }


# ---------------------------------------------------------------------------
# Report builder
# ---------------------------------------------------------------------------


def _build_report(
    stl_path: str,
    checks: List[Dict[str, Any]],
) -> Dict[str, Any]:
    """Assemble a structured wall-thickness validation report."""
    passed_count = sum(1 for c in checks if c.get("passed", False))
    total_count = len(checks)
    all_passed = passed_count == total_count

    report: Dict[str, Any] = {
        "gate": "wall_thickness_validation",
        "gate_version": "1.0",
        "material_profile": "TPU 75A–80A",
        "min_wall_mm": MIN_WALL_MM,
        "hard_reject_mm": HARD_REJECT_MM,
        "stl_path": stl_path,
        "passed": all_passed,
        "summary": f"{passed_count}/{total_count} checks passed",
        "checks": checks,
    }

    report["verdict"] = "PASS" if all_passed else "FAIL"
    return report


def _print_report(report: Dict[str, Any]) -> None:
    """Print a human-readable validation report to stdout."""
    border = "─" * 60
    print(border)
    print("  ZILFIT Wall Thickness Validation Gate 2.0")
    print(border)
    print(f"  STL:            {report['stl_path']}")
    print(f"  Material:       {report['material_profile']}")
    print(f"  MIN_WALL_MM:    {report['min_wall_mm']}")
    print(f"  HARD_REJECT_MM: {report['hard_reject_mm']}")
    print(f"  Verdict:        {'✅ PASS' if report['passed'] else '❌ FAIL'}")
    print(f"  Summary:        {report['summary']}")
    print(border)

    for check in report["checks"]:
        status = "✅" if check.get("passed", False) else "❌"
        print(f"  {status}  {check['check']}")
        print(f"       {check['detail']}")
        min_w = check.get("min_wall_mm")
        if min_w is not None:
            print(f"       min: {min_w:.4f} mm")
        avg_w = check.get("mean_wall_mm")
        if avg_w is not None:
            print(f"       mean: {avg_w:.4f} mm")
        max_w = check.get("max_wall_mm")
        if max_w is not None:
            print(f"       max: {max_w:.4f} mm")

    if not report["passed"]:
        # Check if any hard_reject was triggered
        hard_rejects = [c for c in report["checks"] if c.get("hard_reject", False)]
        if hard_rejects:
            print("  ⚠  HARD REJECT TRIGGERED — STL cannot proceed to print")
    print(border)


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------


def validate_wall_thickness(stl_path: str) -> Dict[str, Any]:
    """Load an STL file and run wall-thickness validation.

    Args:
        stl_path: Path to a binary or ASCII STL file.

    Returns:
        Structured validation report dict.

    Raises:
        FileNotFoundError: If the STL file does not exist.
        ValueError: If trimesh cannot load the file as a valid mesh.
    """
    mesh = trimesh.load(stl_path)
    if not isinstance(mesh, trimesh.Trimesh):
        if hasattr(mesh, "geometry"):
            combined = trimesh.util.concatenate(
                list(mesh.geometry.values())
            )
            mesh = combined
        else:
            raise ValueError(
                f"'{stl_path}' does not contain a valid trimesh.Trimesh "
                f"mesh (got {type(mesh).__name__})"
            )

    # First, ensure the mesh is watertight — non-watertight meshes
    # produce unreliable ray-casting results
    if not mesh.is_watertight:
        raise ValueError(
            f"Mesh is not watertight — wall thickness measurement via "
            f"ray casting is unreliable on non-watertight meshes. "
            f"Run validation/stl/check_manifold.py first."
        )

    checks: List[Dict[str, Any]] = [
        _compute_min_wall_thickness(mesh),
    ]

    report = _build_report(stl_path, checks)
    return report


def run(input_path: str) -> Dict[str, Any]:
    """Programmatic entry point for the unified pre-print runner.

    Wraps validate_wall_thickness() and maps the result to a consistent schema:
      gate, status, metrics, violations, worst

    Args:
        input_path: Path to an STL file.

    Returns:
        Standardized result dict.
    """
    try:
        report = validate_wall_thickness(input_path)
    except FileNotFoundError:
        return {
            "gate": "wall_thickness_validation",
            "status": "INPUT_ERROR",
            "metrics": {},
            "violations": [],
            "worst": None,
            "_error": f"STL file not found: {input_path}",
        }
    except ValueError as e:
        return {
            "gate": "wall_thickness_validation",
            "status": "INPUT_ERROR",
            "metrics": {},
            "violations": [],
            "worst": None,
            "_error": str(e),
        }

    checks = report.get("checks", [])
    passed_count = sum(1 for c in checks if c.get("passed", False))
    total_count = len(checks)

    check = checks[0] if checks else {}
    metrics: Dict[str, Any] = {
        "passed_checks": passed_count,
        "total_checks": total_count,
        "min_wall_mm": check.get("min_wall_mm"),
        "mean_wall_mm": check.get("mean_wall_mm"),
        "max_wall_mm": check.get("max_wall_mm"),
        "samples_taken": check.get("samples_taken"),
        "hard_reject": check.get("hard_reject", False),
    }

    violations = [c for c in checks if not c.get("passed", False)]
    has_hard_reject = any(c.get("hard_reject", False) for c in checks)

    if report.get("passed", False):
        status = "PASS"
    elif has_hard_reject:
        status = "HARD_FAIL"
    else:
        status = "SOFT_FAIL"

    return {
        "gate": "wall_thickness_validation",
        "status": status,
        "metrics": metrics,
        "violations": violations,
        "worst": violations[0] if violations else None,
        "_report": report,
    }


def main() -> int:
    """CLI entry point. Returns 0 on PASS, 1 on FAIL."""
    parser = argparse.ArgumentParser(
        description="ZILFIT STL Wall Thickness Validation — pre-print gate 2",
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

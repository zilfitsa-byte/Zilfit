"""ZILFIT STL Fingerprint — deterministic mesh hashing.

Rules:
- No pickle, no random ordering, no set iteration without sorting.
- All floating-point values rounded to 6 decimal places.
- Vertices: sorted lexicographically after canonicalization.
- Triangles: smallest vertex index first, then sorted lexicographically.
- Fingerprint: SHA-256 hex digest of canonical JSON payload.
"""

from __future__ import annotations

import hashlib
import json
from typing import Any, Dict, List, Sequence, Tuple


# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------
DEFAULT_PRECISION = 6
PRECISION_MULTIPLIER = 10 ** DEFAULT_PRECISION


# ---------------------------------------------------------------------------
# Vertex canonicalization
# ---------------------------------------------------------------------------
def _round_coord(v: float, precision: int = DEFAULT_PRECISION) -> float:
    """Round a float to the given precision, removing negative zero."""
    r = round(v, precision)
    # Remove negative zero: -0.0 == 0.0 but str(-0.0) == '-0.0'
    if r == 0.0:
        return 0.0
    return r


def _canonical_vertex(
    vertex: Tuple[float, float, float],
    precision: int = DEFAULT_PRECISION,
) -> Tuple[float, float, float]:
    """Round vertex coordinates, removing negative zero."""
    return (
        _round_coord(vertex[0], precision),
        _round_coord(vertex[1], precision),
        _round_coord(vertex[2], precision),
    )


def canonicalize_vertices(
    vertices: Sequence[Tuple[float, float, float]],
    precision: int = DEFAULT_PRECISION,
) -> List[Tuple[float, float, float]]:
    """Canonicalize a vertex list:

    - Round each coordinate to *precision* decimal places.
    - Replace -0.0 with 0.0.
    - Sort lexicographically (x, y, z) for stable ordering.

    Returns a new list; the input is not modified.
    """
    canonical = tuple(_canonical_vertex(v, precision) for v in vertices)
    return sorted(canonical)


# ---------------------------------------------------------------------------
# Triangle canonicalization
# ---------------------------------------------------------------------------
def _rotate_to_smallest_first(
    triangle: Tuple[int, int, int],
) -> Tuple[int, int, int]:
    """Rotate a triangle tuple so that the smallest vertex index comes first.

    Preserves cyclic order (orientation):
    - (0, 1, 2) → (0, 1, 2) — already smallest first
    - (1, 2, 0) → (0, 1, 2) — rotate left once
    - (2, 0, 1) → (0, 1, 2) — rotate left twice
    """
    a, b, c = triangle
    min_idx = min(a, b, c)

    if a == min_idx:
        return (a, b, c)
    elif b == min_idx:
        return (b, c, a)
    else:
        return (c, a, b)


def canonicalize_triangles(
    triangles: Sequence[Tuple[int, int, int]],
) -> List[Tuple[int, int, int]]:
    """Canonicalize a triangle list:

    - Rotate each triangle so the smallest vertex index comes first.
    - Sort triangles lexicographically.

    Returns a new list; the input is not modified.
    """
    canonical = list(_rotate_to_smallest_first(t) for t in triangles)
    return sorted(canonical)


# ---------------------------------------------------------------------------
# Mesh fingerprint
# ---------------------------------------------------------------------------
def compute_mesh_fingerprint(
    mesh_dict: Dict[str, Any],
    precision: int = DEFAULT_PRECISION,
) -> str:
    """Compute a deterministic SHA-256 fingerprint for a mesh.

    The fingerprint is computed from a canonical JSON payload containing:
    - vertices (rounded and sorted)
    - triangles (canonicalized and sorted)
    - bounds (rounded)
    - manifold_flags (sorted keys)

    Args:
        mesh_dict: Dictionary with keys:
            - 'vertices': list of (x, y, z) tuples
            - 'triangles': list of (v0, v1, v2) integer tuples
            - 'bounds': {'min': [x, y, z], 'max': [x, y, z]}
            - 'manifold_flags': arbitrary dict with integrity booleans

    Returns:
        SHA-256 hex digest string (64 characters).
    """
    # Step 1: Canonicalize vertices
    vertices = mesh_dict.get("vertices", [])
    canonical_verts = canonicalize_vertices(vertices, precision)

    # Step 2: Build a mapping from old vertex indices → new canonical indices
    # After sorting, we need to re-map triangle references.
    # Vertices may have duplicates — we deduplicate here.
    seen: Dict[Tuple[float, float, float], int] = {}
    unique_verts: List[Tuple[float, float, float]] = []
    old_to_new: Dict[int, int] = {}

    # We need to map original vertices → canonical positions → deduped indices
    # First, canonicalize the original vertices individually
    canonical_orig = list(
        _canonical_vertex(v, precision) for v in vertices
    )

    # Now deduplicate canonical_orig, preserving canonical sorted order
    # Build set of unique vertices
    unique_set: List[Tuple[float, float, float]] = []
    for v in canonical_verts:
        if v not in seen:
            seen[v] = len(unique_set)
            unique_set.append(v)

    # Map each original vertex to its deduped canonical index
    for i, cv in enumerate(canonical_orig):
        old_to_new[i] = seen[cv]

    # Step 3: Remap triangle indices
    triangles = mesh_dict.get("triangles", [])
    remapped = list(
        (old_to_new[a], old_to_new[b], old_to_new[c])
        for (a, b, c) in triangles
    )
    canonical_tris = canonicalize_triangles(remapped)

    # Step 4: Canonicalize bounds
    bounds = mesh_dict.get("bounds", {})
    canonical_bounds = {
        "max": list(_round_coord(v, precision) for v in bounds.get("max", [0.0, 0.0, 0.0])),
        "min": list(_round_coord(v, precision) for v in bounds.get("min", [0.0, 0.0, 0.0])),
    }

    # Step 5: Canonicalize manifold_flags (sorted keys)
    manifold = mesh_dict.get("manifold_flags", {})
    canonical_manifold = dict(sorted(manifold.items()))

    # Step 6: Build canonical payload
    payload = {
        "manifold_flags": canonical_manifold,
        "bounds": {
            "max": canonical_bounds["max"],
            "min": canonical_bounds["min"],
        },
        "triangles": canonical_tris,
        "vertices": unique_verts,
    }

    # Step 7: Serialize to JSON (sorted keys, no floating point ambiguity)
    json_bytes = json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=True).encode("utf-8")

    # Step 8: SHA-256
    return hashlib.sha256(json_bytes).hexdigest()

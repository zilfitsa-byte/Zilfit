"""ZILFIT Fingerprint Contract — versioned + cross-platform STL fingerprinting.

Rules:
- No pickle, no random ordering, no set iteration without sorting.
- Integer scaling replaces round(float, 6).
- strict mode preserves winding; geometric mode ignores winding differences.
- created_at excluded from core hash for determinism.

Compatibility: zilfit_stl_fingerprint.py uses float-rounding. This module uses
integer scaling. Both produce deterministic results. The old module remains
unchanged; this is the v1 contract upgrade path.
"""

from __future__ import annotations

import hashlib
import json
import math
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Sequence, Tuple


# ---------------------------------------------------------------------------
# Schema constants
# ---------------------------------------------------------------------------
FINGERPRINT_SCHEMA_VERSION = "zilfit-mesh-v1"
FINGERPRINT_CONTRACT_VERSION = "1.0"  # compatibility alias
DEFAULT_PRECISION = 6
DEFAULT_SCALE = 1_000_000  # 10^6 = 6 decimal places as integers

REQUIRED_FINGERPRINT_KEYS = (
    "vertices",
    "triangles",
    "bounds",
    "manifold_flags",
)


# ---------------------------------------------------------------------------
# Integer-scaled float canonicalization
# ---------------------------------------------------------------------------
def canonicalize_float_to_int(
    value: float,
    scale: int = DEFAULT_SCALE,
) -> int:
    """Convert a float to a canonical integer via rounding + scaling.

    Example: 0.123456789 → round(0.123456789 * 1_000_000) = 123457
    This eliminates floating-point noise within ~5e-7.
    """
    return int(round(value * scale))


def canonicalize_vertices_scaled(
    vertices: Sequence[Tuple[float, float, float]],
    scale: int = DEFAULT_SCALE,
) -> List[Tuple[int, int, int]]:
    """Canonicalize vertices using integer scaling.

    - Convert each coordinate to a scaled integer.
    - Sort lexicographically (x, y, z) for stable ordering.
    - Remove negative zero implicitly (integer has no sign for zero).

    Returns sorted list of (int, int, int) tuples.
    """
    canonical = tuple(
        (
            canonicalize_float_to_int(v[0], scale),
            canonicalize_float_to_int(v[1], scale),
            canonicalize_float_to_int(v[2], scale),
        )
        for v in vertices
    )
    return list(sorted(canonical))


# ---------------------------------------------------------------------------
# Triangle canonicalization
# ---------------------------------------------------------------------------
def canonicalize_triangles_strict(
    triangles: Sequence[Tuple[int, int, int]],
) -> List[Tuple[int, int, int]]:
    """Canonicalize triangles in strict mode.

    - Rotate each triangle so the smallest vertex index comes first.
    - Preserve cyclic order (winding).
    - Sort triangles lexicographically.
    """
    result: List[Tuple[int, int, int]] = []
    for a, b, c in triangles:
        # Rotate to put smallest index first, preserving cyclic order
        if a <= b and a <= c:
            canonical = (a, b, c)
        elif b <= a and b <= c:
            canonical = (b, c, a)
        else:
            canonical = (c, a, b)
        result.append(canonical)
    return sorted(result)


def canonicalize_triangles_geometric(
    triangles: Sequence[Tuple[int, int, int]],
) -> List[Tuple[int, int, int]]:
    """Canonicalize triangles in geometric mode.

    - For each triangle: put smallest index first, then sort remaining two.
      This ignores winding (e.g., (0,1,2) == (0,2,1)).
    - Sort triangles lexicographically.
    """
    result: List[Tuple[int, int, int]] = []
    for a, b, c in triangles:
        a, b, c = sorted([a, b, c])
        result.append((a, b, c))
    return sorted(result)


# ---------------------------------------------------------------------------
# Strict input type validation
# ---------------------------------------------------------------------------
def _validate_3d_vertex(v):
    """Check that *v* has exactly 3 numeric coordinates."""
    if len(v) != 3:
        raise TypeError(
            f"vertex must have exactly 3 coordinates, got {len(v)}: {v}"
        )


def _validate_topology(vertices, triangles):
    """Reject invalid mesh topology before canonicalization or hashing.

    This runs strictly BEFORE geometry processing.  Raises immediately on
    the first defect — no partial hashing, no silent skip.
    """
    n_verts = len(vertices)

    for idx, tri in enumerate(triangles):
        if len(tri) != 3:
            raise TypeError(
                f"triangle {idx} must have exactly 3 indices, got {len(tri)}"
            )
        a, b, c = tri
        # Negative index → reject (Python lists accept negative but meshes
        # should not)
        for label, val in zip(("a", "b", "c"), (a, b, c)):
            if val < 0:
                raise ValueError(
                    f"triangle {idx} has negative index ({label}={val}): "
                    "triangle indices must be non-negative"
                )
        # Duplicate indices → degenerate triangle
        if a == b or b == c or a == c:
            raise ValueError(
                f"triangle {idx} has duplicate indices {tri}: "
                "degenerate triangles are rejected"
            )
        # Out-of-range → no mesh reference can resolve
        for label, val in zip(("a", "b", "c"), (a, b, c)):
            if val >= n_verts:
                raise IndexError(
                    f"triangle {idx} index {label}={val} is out of range "
                    f"(vertices count = {n_verts})"
                )

    # Validate every vertex is 3D
    for i, v in enumerate(vertices):
        _validate_3d_vertex(v)


def _validate_mesh_types(mesh_dict: Dict[str, Any]) -> None:
    """Validate input types before any canonicalization or hashing.

    Raises TypeError with clear messages for structural mismatches.
    Fails fast — before canonicalization or hash generation.
    """

    # ── vertices: sequence[sequence[number]] ────────────────────────
    verts = mesh_dict.get("vertices")
    if not isinstance(verts, (list, tuple)):
        raise TypeError(
            f"vertices must be a sequence (list/tuple), got {type(verts).__name__}"
        )
    for idx, v in enumerate(verts):
        if not isinstance(v, (list, tuple)):
            raise TypeError(
                f"vertices[{idx}] must be a sequence (list/tuple), got {type(v).__name__}"
            )
        if len(v) != 3:
            raise TypeError(
                f"vertices[{idx}] must have exactly 3 components, got {len(v)}"
            )
        for ci, coord in enumerate(v):
            # bool is subclass of int in Python — reject explicitly
            if isinstance(coord, bool):
                raise TypeError(
                    f"vertices[{idx}][{ci}] must be int/float, got bool"
                )
            if not isinstance(coord, (int, float)):
                raise TypeError(
                    f"vertices[{idx}][{ci}] must be int/float, got {type(coord).__name__}"
                )

    # ── triangles: sequence[sequence[int]] ──────────────────────────
    tris = mesh_dict.get("triangles")
    if not isinstance(tris, (list, tuple)):
        raise TypeError(
            f"triangles must be a sequence (list/tuple), got {type(tris).__name__}"
        )
    for idx, t in enumerate(tris):
        if not isinstance(t, (list, tuple)):
            raise TypeError(
                f"triangles[{idx}] must be a sequence (list/tuple), got {type(t).__name__}"
            )
        if len(t) != 3:
            raise TypeError(
                f"triangles[{idx}] must have exactly 3 vertex indices, got {len(t)}"
            )
        for ci, val in enumerate(t):
            if isinstance(val, bool):
                raise TypeError(
                    f"triangles[{idx}][{ci}] must be int, got bool"
                )
            if not isinstance(val, int):
                raise TypeError(
                    f"triangles[{idx}][{ci}] must be int, got {type(val).__name__}"
                )

    # ── bounds: min/max arrays with numeric values ──────────────────
    bounds = mesh_dict.get("bounds")
    if bounds is not None:
        if not isinstance(bounds, dict):
            raise TypeError(
                f"bounds must be a dict, got {type(bounds).__name__}"
            )
        for key in ("min", "max"):
            if key not in bounds:
                continue
            arr = bounds[key]
            if not isinstance(arr, (list, tuple)):
                raise TypeError(
                    f"bounds['{key}'] must be a list/tuple, got {type(arr).__name__}"
                )
            for ci, v in enumerate(arr):
                if isinstance(v, bool):
                    raise TypeError(
                        f"bounds['{key}'][{ci}] must be int/float, got bool"
                    )
                if not isinstance(v, (int, float)):
                    raise TypeError(
                        f"bounds['{key}'][{ci}] must be int/float, got {type(v).__name__}"
                    )

    # ── manifold_flags: bool/int only ───────────────────────────────
    mf = mesh_dict.get("manifold_flags")
    if mf is not None:
        if not isinstance(mf, dict):
            raise TypeError(
                f"manifold_flags must be a dict, got {type(mf).__name__}"
            )
        for key, val in mf.items():
            if isinstance(val, bool):
                continue  # bool is fine here
            if not isinstance(val, int):
                raise TypeError(
                    f"manifold_flags['{key}'] must be bool/int, got {type(val).__name__}"
                )


# ---------------------------------------------------------------------------
# Finite-number validation
# ---------------------------------------------------------------------------
def _validate_finite(value: Any, label: str = "value") -> None:
    """Raise ValueError if a numeric value is NaN or ±inf."""
    if isinstance(value, float) and not math.isfinite(value):
        raise ValueError(
            f"non-finite numeric value in {label}: {value!r}"
        )


def _validate_vertices_finite(vertices: Sequence) -> None:
    """Validate all vertex coordinates are finite numbers."""
    for idx, vertex in enumerate(vertices):
        if isinstance(vertex, (list, tuple)) and len(vertex) == 3:
            for coord_i, coord in enumerate(vertex):
                _validate_finite(coord, f"vertices[{idx}][{coord_i}]")


def _validate_bounds_finite(bounds: Dict[str, Any]) -> None:
    """Validate bounds min/max arrays contain only finite numbers."""
    for direction in ("min", "max"):
        if direction in bounds:
            arr = bounds[direction]
            if isinstance(arr, (list, tuple)):
                for coord_i, val in enumerate(arr):
                    _validate_finite(val, f"bounds.{direction}[{coord_i}]")

def _assert_finite_numeric(value: Any, context: str = "value") -> None:
    """Centralized finite numeric validation that raises TypeError/ValueError on non-finite values."""
    if isinstance(value, float) and not math.isfinite(value):
        raise ValueError(f"non-finite numeric value in {context}: {value!r}")
    elif isinstance(value, (int, float)) and math.isnan(value):
        raise ValueError(f"NaN value in {context}: {value!r}")


# ---------------------------------------------------------------------------
# Float representation stability
# ---------------------------------------------------------------------------
def _stable_float_repr(value: float) -> str:
    """Normalize float representation for cross-platform stability.

    - -0.0 -> "0.0"
    - Regular floats -> normalized via :.12g
    - Handles edge cases like subnormals deterministically
    """
    if value == 0.0:  # catches -0.0
        return "0.0"
    return f"{value:.12g}"


# ---------------------------------------------------------------------------
# Geometry validation — degenerate triangles, non-manifold edges
# ---------------------------------------------------------------------------
def _validate_no_non_manifold_edges(
    triangles: Sequence[Tuple[int, int, int]],
) -> None:
    """Reject any edge shared by 3+ triangles (non-manifold).

    Raises ValueError if a non-manifold edge is detected.
    """
    edge_count: Dict[Tuple[int, int], int] = {}
    for tri in triangles:
        a, b, c = tri
        for edge_key in [(min(a, b), max(a, b)), (min(b, c), max(b, c)), (min(a, c), max(a, c))]:
            # Skip self-edges (a == b) — these arise from degenerate tris
            if edge_key[0] == edge_key[1]:
                continue
            edge_count[edge_key] = edge_count.get(edge_key, 0) + 1
    for edge, count in edge_count.items():
        if count > 2:
            raise ValueError(
                f"non-manifold edge {edge}: shared by {count} triangles (max 2 allowed)"
            )


def _validate_no_degenerate_triangles(
    unique_verts: List[Tuple[int, int, int]],
    canonical_tris: List[Tuple[int, int, int]],
) -> None:
    """Check for zero-area triangles (same-vertex or collinear).

    Raises ValueError if a degenerate triangle is detected.
    """
    for tri in canonical_tris:
        a, b, c = tri
        if a == b or b == c or a == c:
            raise ValueError(
                f"degenerate triangle {tri}: duplicate indices after dedup"
            )
        v0 = unique_verts[a]
        v1 = unique_verts[b]
        v2 = unique_verts[c]
        # Cross product (b-a) x (c-a) for collinearity detection
        ux, uy, uz = v1[0] - v0[0], v1[1] - v0[1], v1[2] - v0[2]
        vx, vy, vz = v2[0] - v0[0], v2[1] - v0[1], v2[2] - v0[2]
        cross_x = uy * vz - uz * vy
        cross_y = uz * vx - ux * vz
        cross_z = ux * vy - uy * vx
        if cross_x == 0 and cross_y == 0 and cross_z == 0:
            raise ValueError(
                f"degenerate/collinear triangle {tri}: zero-area triangle (collinear vertices)"
            )


def _validate_no_duplicate_triangles(
    canonical_tris: List[Tuple[int, int, int]],
) -> None:
    """Check for duplicate triangles after canonicalization.

    Raises ValueError if a duplicate canonical triangle is found.
    """
    seen: set = set()
    for tri in canonical_tris:
        if tri in seen:
            raise ValueError(f"duplicate triangle found: {tri}")
        seen.add(tri)


# ---------------------------------------------------------------------------
# Orientation signature — detects inverted triangles
# ---------------------------------------------------------------------------
ORIENTATION_INVERSION_THRESHOLD = 0.20  # 20% inverted → warning


def _triangle_normal_i(
    vertices_scaled: List[Tuple[int, int, int]],
    tri: Tuple[int, int, int],
) -> Tuple[int, int, int]:
    """Compute cross-product normal for a triangle using scaled integer coords."""
    a = vertices_scaled[tri[0]]
    b = vertices_scaled[tri[1]]
    c = vertices_scaled[tri[2]]
    # (b - a) x (c - a), scaled × 2 to avoid overflow issues
    ux, uy, uz = b[0] - a[0], b[1] - a[1], b[2] - a[2]
    vx, vy, vz = c[0] - a[0], c[1] - a[1], c[2] - a[2]
    return (
        uy * vz - uz * vy,
        uz * vx - ux * vz,
        ux * vy - uy * vx,
    )


def _edge_key(v0: int, v1: int) -> Tuple[int, int]:
    """Canonicalize edge: smaller index first."""
    return (v0, v1) if v0 < v1 else (v1, v0)


def compute_orientation_signature(
    mesh_dict: Dict[str, Any],
    scale: int = DEFAULT_SCALE,
) -> Dict[str, Any]:
    """Detect orientation inconsistency across mesh triangles.

    Builds an edge-to-triangles adjacency map, then for each shared edge
    checks whether the two incident triangles use the edge in opposite
    direction (consistent) or same direction (one is inverted).

    Does NOT affect the core fingerprint hash.

    Returns:
        {
            "total_triangles": int,
            "inverted_count": int,
            "inverted_ratio": float,
            "orientation_warning": bool,
        }
    """
    vertices = mesh_dict.get("vertices", [])
    triangles = mesh_dict.get("triangles", [])
    if not triangles:
        return {
            "total_triangles": 0,
            "inverted_count": 0,
            "inverted_ratio": 0.0,
            "orientation_warning": False,
        }

    # Build edge → list of (triangle_index, edge_order)
    # edge_order = +1 if edge goes (small→big), -1 if (big→small)
    edge_adj: Dict[Tuple[int, int], List[Tuple[int, int]]] = {}
    for ti, (a, b, c) in enumerate(triangles):
        edges = [(a, b), (b, c), (c, a)]
        for v0, v1 in edges:
            ek = (min(v0, v1), max(v0, v1))
            order = 1 if v0 < v1 else -1
            edge_adj.setdefault(ek, []).append((ti, order))

    # Count triangles with inconsistent edge orientations
    inverted_set: set = set()
    for ek, usages in edge_adj.items():
        if len(usages) == 1:
            # Boundary edge — no consistency check possible
            continue
        if len(usages) > 2:
            # Non-manifold: more than 2 triangles share this edge
            for ti, _ in usages:
                inverted_set.add(ti)
            continue
        # Exactly 2 triangles share this edge
        # Consistent manifold → opposite directions (+1 and -1)
        if usages[0][1] == usages[1][1]:
            # Same direction = one triangle is inverted
            inverted_set.add(usages[0][0])
            inverted_set.add(usages[1][0])

    total = len(triangles)
    inverted_count = len(inverted_set)
    ratio = inverted_count / total if total else 0.0

    return {
        "total_triangles": total,
        "inverted_count": inverted_count,
        "inverted_ratio": round(ratio, 6),
        "orientation_warning": ratio > ORIENTATION_INVERSION_THRESHOLD,
    }


# ---------------------------------------------------------------------------
# Core fingerprint
# ---------------------------------------------------------------------------
def _compute_fingerprint_core(
    mesh_dict: Dict[str, Any],
    mode: str = "strict",
    scale: int = DEFAULT_SCALE,
    strict_topology: bool = False,
) -> Tuple[List[Tuple[int, int, int]], List[Tuple[int, int, int]], Dict[str, Any]]:
    """Internal: canonicalize mesh components and return deduped data.

    Returns: (unique_vertices_scaled, canonical_triangles, bounds_scaled)
    """
    vertices = mesh_dict.get("vertices", [])
    triangles = mesh_dict.get("triangles", [])

    # ── Empty-input guards (must run before topology validation) ────────
    if not vertices:
        raise ValueError("vertices list is empty — no geometry to hash")
    if not triangles:
        raise ValueError("triangles list is empty — no surface to hash")

    # ── Topology validation ───────────────────────────────────────────
    _validate_topology(vertices, triangles)

    # ── Finite-number guard ──────────────────────────────────────────
    _validate_vertices_finite(vertices)
    bounds_raw = mesh_dict.get("bounds")
    if bounds_raw:
        _validate_bounds_finite(bounds_raw)

    # Canonicalize vertices with integer scaling
    canonical_verts = canonicalize_vertices_scaled(vertices, scale)
    # Validate that canonical vertices are finite (should be ints, but check)
    for v_idx, vertex in enumerate(canonical_verts):
        for coord_i, coord in enumerate(vertex):
            _assert_finite_numeric(coord, f"canonical_verts[{v_idx}][{coord_i}]")

    # Deduplicate vertices and build index mapping
    seen: Dict[Tuple[int, int, int], int] = {}
    unique_verts: List[Tuple[int, int, int]] = []
    old_to_new: Dict[int, int] = {}

    # Map each original vertex to its scaled integer form
    scaled_orig = tuple(
        (
            canonicalize_float_to_int(v[0], scale),
            canonicalize_float_to_int(v[1], scale),
            canonicalize_float_to_int(v[2], scale),
        )
        for v in vertices
    )

    # Build unique set from the sorted canonical list
    for v in canonical_verts:
        if v not in seen:
            seen[v] = len(unique_verts)
            unique_verts.append(v)

    # Map each original vertex's scaled form to its deduped index
    for i, sv in enumerate(scaled_orig):
        old_to_new[i] = seen[sv]

    # ── Unreferenced vertex check (optional strict topology) ──────────
    if strict_topology:
        referenced = {i for tri in triangles for i in tri}
        all_vertex_indices = set(range(len(vertices)))
        unreferenced = all_vertex_indices - referenced
        if unreferenced:
            raise ValueError(
                f"{len(unreferenced)} unreferenced vertex index(es): "
                f"{sorted(unreferenced)} (enable strict_topology=False "
                "to allow unused vertices)"
            )

    # Remap triangle indices (safe — empty triangles already rejected above)
    try:
        remapped = list(
            (old_to_new[a], old_to_new[b], old_to_new[c])
            for (a, b, c) in triangles
        )
    except KeyError as e:
        raise IndexError(
            f"triangle vertex index out of range: {e}"
        ) from e

    # Canonicalize triangles based on mode
    if mode == "geometric":
        canonical_tris = canonicalize_triangles_geometric(remapped)
    else:  # strict (default)
        canonical_tris = canonicalize_triangles_strict(remapped)

    # Compute bounds from canonical vertices
    if unique_verts:
        bounds = {
            "max": [max(v[i] for v in unique_verts) for i in range(3)],
            "min": [min(v[i] for v in unique_verts) for i in range(3)],
        }
    else:
        bounds = {"max": [0, 0, 0], "min": [0, 0, 0]}

    return unique_verts, canonical_tris, bounds


def compute_mesh_fingerprint(
    mesh_dict: Dict[str, Any],
    mode: str = "strict",
    strict_topology: bool = True,
    allow_degenerate: bool = False,
) -> str:
    """Compute a deterministic SHA-256 fingerprint for a mesh.

    Uses integer scaling (not float rounding) for cross-platform consistency.

    Args:
        mesh_dict: Must contain 'vertices', 'triangles', optionally
                   'bounds' and 'manifold_flags' (bounds recomputed).
        mode: 'strict' (preserve winding) or 'geometric' (ignore winding).
        strict_topology: True (default) rejects unreferenced vertices (degenerate
                         meshes). Set to False to tolerate unused vertices.
        allow_degenerate: If True, skip degenerate/duplicate triangle checks.
                          Non-manifold edges are always rejected.

    Returns:
        SHA-256 hex digest string (64 characters).
    """
    if mode not in ("strict", "geometric"):
        raise ValueError(f"mode must be 'strict' or 'geometric', got '{mode}'")

    # Validate required keys — extra keys are silently ignored
    missing_keys = [k for k in REQUIRED_FINGERPRINT_KEYS if k not in mesh_dict]
    if missing_keys:
        raise ValueError(
            f"mesh_dict missing required key(s): {', '.join(sorted(missing_keys))}"
        )

    # ── Strict input type validation ──────────────────────────────────
    _validate_mesh_types(mesh_dict)

    unique_verts, canonical_tris, bounds = _compute_fingerprint_core(
        mesh_dict, mode=mode, strict_topology=strict_topology
    )

    # ── Degenerate geometry rejection (unless allow_degenerate) ──────
    if not allow_degenerate:
        _validate_no_degenerate_triangles(unique_verts, canonical_tris)
        _validate_no_duplicate_triangles(canonical_tris)

    # ── Non-manifold edge rejection (always on) ──────────────────────
    _validate_no_non_manifold_edges(canonical_tris)

    # Canonicalize manifold_flags
    manifold = mesh_dict.get("manifold_flags", {})
    canonical_manifold = dict(sorted(manifold.items()))

    # Build canonical payload (sort_keys for determinism)
    payload = {
        "bounds": {
            "max": bounds["max"],
            "min": bounds["min"],
        },
        "manifold_flags": canonical_manifold,
        "triangles": [list(t) for t in canonical_tris],
        "vertices": [list(v) for v in unique_verts],
    }

    # Compact JSON with sorted keys
    json_bytes = json.dumps(
        payload, sort_keys=True, separators=(",", ":"), ensure_ascii=True
    ).encode("utf-8")

    return hashlib.sha256(json_bytes).hexdigest()


# ---------------------------------------------------------------------------
# Extended payload (includes provenance, excludes created_at from hash)
# ---------------------------------------------------------------------------
def compute_extended_fingerprint_payload(
    mesh_dict: Dict[str, Any],
    provenance: Optional[Dict[str, Any]] = None,
    mode: str = "strict",
) -> Dict[str, Any]:
    """Compute an extended payload with provenance metadata.

    The core hash (fingerprint) does NOT include created_at, so repeated
    calls on the same mesh produce the same hash regardless of when
    they are called.

    Returns:
        Full extended payload dict with fingerprint + provenance.
    """
    # Core fingerprint (does not include created_at)
    fp = compute_mesh_fingerprint(mesh_dict, mode=mode)

    # Orientation detection (does not affect core hash)
    orientation = compute_orientation_signature(mesh_dict)

    # Provenance defaults
    prov = dict(provenance) if provenance else {}
    prov.setdefault("generator", "zilfit_fingerprint_contract")
    prov.setdefault("precision", DEFAULT_PRECISION)
    prov.setdefault("scale", DEFAULT_SCALE)
    prov.setdefault("mode", mode)

    # created_at is included in payload but excluded from core hash computation
    # The core hash is computed above without it.
    now_iso = datetime.now(timezone.utc).isoformat()

    payload = {
        "fingerprint": fp,
        "fingerprint_contract_version": FINGERPRINT_CONTRACT_VERSION,
        "schema_version": FINGERPRINT_SCHEMA_VERSION,
        "mode": mode,
        "precision": DEFAULT_PRECISION,
        "scale": DEFAULT_SCALE,
        "created_at": now_iso,
        "orientation": {
            "warning": orientation["orientation_warning"],
            "ratio": orientation["inverted_ratio"],
            "inverted_count": orientation["inverted_count"],
            "total_triangles": orientation["total_triangles"],
        },
        "provenance": prov,
    }

    return payload


# ---------------------------------------------------------------------------
# Compatibility wrapper for zlfit_stl_fingerprint.py
# ---------------------------------------------------------------------------
def compute_mesh_fingerprint_compat(
    mesh_dict: Dict[str, Any],
    precision: int = DEFAULT_PRECISION,
) -> str:
    """Compatibility wrapper matching zilfit_stl_fingerprint.compute_mesh_fingerprint.

    Delegates to the integer-scaled contract. The float-rounding version
    may produce different hashes for the same mesh if there is floating-point
    noise, but both are deterministic.
    """
    return compute_mesh_fingerprint(mesh_dict, mode="strict")

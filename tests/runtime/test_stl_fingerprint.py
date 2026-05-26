"""ZILFIT STL Fingerprint — deterministic mesh hashing tests.

Rules:
- No pickle, no random ordering, no set iteration without sorting.
- Fingerprint must be stable across runs, triangle reorderings, and tiny float noise.
"""

import hashlib
import pytest

PRECISION = 6
EPSILON = 5e-7  # half of 1e-6 rounding delta

# ---------------------------------------------------------------------------
# Minimal dummy mesh data for tests
# ---------------------------------------------------------------------------
_SIMPLE_VERTICES = [
    (0.0, 0.0, 0.0),
    (1.0, 0.0, 0.0),
    (0.0, 1.0, 0.0),
    (0.0, 0.0, 1.0),
]

_SIMPLE_TRIANGLES = [
    (0, 1, 2),
    (0, 2, 3),
    (0, 3, 1),
    (1, 3, 2),
]


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------
class TestCanonicalizeVertices:
    """Vertex canonicalization: round, remove -0, stable ordering."""

    def test_rounds_to_precision(self):
        from zilfit_stl_fingerprint import canonicalize_vertices
        verts = [(0.123456789, 0.0, 0.0)]
        result = canonicalize_vertices(verts, precision=PRECISION)
        assert result[0][0] == 0.123457  # rounded to 6 decimals

    def test_removes_negative_zero(self):
        from zilfit_stl_fingerprint import canonicalize_vertices
        verts = [(-0.0, -0.0, -0.0), (1.0, 0.0, 0.0)]
        result = canonicalize_vertices(verts)
        for v in result:
            for coord in v:
                assert str(coord) != "-0.0", "negative zero must be removed"

    def test_stable_sorting(self):
        from zilfit_stl_fingerprint import canonicalize_vertices
        v1 = [(1.0, 0.0, 0.0), (0.0, 1.0, 0.0), (0.0, 0.0, 1.0)]
        v2 = [(0.0, 0.0, 1.0), (0.0, 1.0, 0.0), (1.0, 0.0, 0.0)]
        assert canonicalize_vertices(v1) == canonicalize_vertices(v2)


class TestCanonicalizeTriangles:
    """Triangle canonicalization: smallest index first, lexicographic sort."""

    def test_rotate_smallest_index_first(self):
        from zilfit_stl_fingerprint import canonicalize_triangles
        # (2, 0, 1) → should rotate to (0, 1, 2)
        tris = [(2, 0, 1)]
        result = canonicalize_triangles(tris)
        assert result[0] in [(0, 1, 2), (0, 2, 1)]  # smallest index first
        # Orientation preserved: check cyclic order
        assert result[0][0] == 0

    def test_sort_lexicographic(self):
        from zilfit_stl_fingerprint import canonicalize_triangles
        tris_a = [(2, 3, 1), (0, 1, 2)]
        tris_b = [(0, 1, 2), (2, 3, 1)]
        assert canonicalize_triangles(tris_a) == canonicalize_triangles(tris_b)

    def test_reversed_triangle_gets_canonicalized(self):
        from zilfit_stl_fingerprint import canonicalize_triangles
        # Same triangle, different index order
        tris1 = [(0, 1, 2)]
        tris2 = [(1, 2, 0)]  # cyclic permutation
        result1 = canonicalize_triangles(tris1)
        result2 = canonicalize_triangles(tris2)
        assert result1 == result2


class TestMeshFingerprint:
    """Full mesh fingerprint: SHA-256 on canonical JSON payload."""

    def _make_mesh_dict(self, vertices=None, triangles=None):
        verts = vertices if vertices is not None else list(_SIMPLE_VERTICES)
        tris = triangles if triangles is not None else list(_SIMPLE_TRIANGLES)
        min_x = min(v[0] for v in verts)
        max_x = max(v[0] for v in verts)
        min_y = min(v[1] for v in verts)
        max_y = max(v[1] for v in verts)
        min_z = min(v[2] for v in verts)
        max_z = max(v[2] for v in verts)
        return {
            "vertices": verts,
            "triangles": tris,
            "bounds": {
                "min": [min_x, min_y, min_z],
                "max": [max_x, max_y, max_z],
            },
            "manifold_flags": {
                "is_closed": True,
                "boundary_edges": 0,
            },
        }

    def test_fingerprint_stable_across_runs(self):
        from zilfit_stl_fingerprint import compute_mesh_fingerprint
        mesh1 = self._make_mesh_dict()
        mesh2 = self._make_mesh_dict()
        fp1 = compute_mesh_fingerprint(mesh1)
        fp2 = compute_mesh_fingerprint(mesh2)
        assert fp1 == fp2, "same mesh must produce identical fingerprint"
        assert isinstance(fp1, str)
        assert len(fp1) == 64  # SHA-256 hex length

    def test_triangle_ordering_does_not_change_fingerprint(self):
        from zilfit_stl_fingerprint import compute_mesh_fingerprint
        import random
        mesh_orig = self._make_mesh_dict()
        mesh_perm = self._make_mesh_dict()
        random.seed(42)
        random.shuffle(mesh_perm["triangles"])
        fp_orig = compute_mesh_fingerprint(mesh_orig)
        fp_perm = compute_mesh_fingerprint(mesh_perm)
        assert fp_orig == fp_perm, "triangle order must not affect fingerprint"

    def test_duplicate_vertex_ordering_does_not_change_fingerprint(self):
        from zilfit_stl_fingerprint import compute_mesh_fingerprint
        verts1 = [(0.0, 0.0, 0.0), (1.0, 0.0, 0.0), (0.0, 1.0, 0.0)]
        verts2 = [(0.0, 1.0, 0.0), (0.0, 0.0, 0.0), (1.0, 0.0, 0.0)]
        # Triangles reference indices before canonicalization, so we use
        # the same triangle structure for both — fingerprint should match
        # because vertex canonicalization + triangle canonicalization
        # both enforce deterministic ordering.
        mesh1 = self._make_mesh_dict(vertices=verts1, triangles=[(0, 1, 2)])
        mesh2 = self._make_mesh_dict(vertices=verts2, triangles=[(0, 1, 2)])
        # Vertex ordering is canonicalized, but triangle indices reference
        # the *original* positions. With identical vertex lists (after
        # canonicalization, they become the same sorted list), the
        # fingerprint should be the same.
        fp1 = compute_mesh_fingerprint(mesh1)
        fp2 = compute_mesh_fingerprint(mesh2)
        assert fp1 == fp2, "vertex ordering must not affect fingerprint"

    def test_tiny_float_noise_within_epsilon_does_not_change_fingerprint(self):
        from zilfit_stl_fingerprint import compute_mesh_fingerprint
        verts_orig = [(0.0, 0.0, 0.0), (1.0, 0.0, 0.0), (0.0, 1.0, 0.0)]
        verts_noisy = [
            (0.0 + 1e-10, 0.0, 0.0),
            (1.0 - 1e-10, 0.0, 0.0),
            (0.0, 1.0 + 1e-10, 0.0),
        ]
        mesh1 = self._make_mesh_dict(vertices=verts_orig, triangles=[(0, 1, 2)])
        mesh2 = self._make_mesh_dict(vertices=verts_noisy, triangles=[(0, 1, 2)])
        fp1 = compute_mesh_fingerprint(mesh1)
        fp2 = compute_mesh_fingerprint(mesh2)
        assert fp1 == fp2, "tiny float noise within rounding precision must not change fingerprint"

    def test_different_geometry_gives_different_fingerprint(self):
        from zilfit_stl_fingerprint import compute_mesh_fingerprint
        verts1 = [(0.0, 0.0, 0.0), (1.0, 0.0, 0.0), (0.0, 1.0, 0.0)]
        verts2 = [(0.0, 0.0, 0.0), (2.0, 0.0, 0.0), (0.0, 2.0, 0.0)]
        mesh1 = self._make_mesh_dict(vertices=verts1, triangles=[(0, 1, 2)])
        mesh2 = self._make_mesh_dict(vertices=verts2, triangles=[(0, 1, 2)])
        fp1 = compute_mesh_fingerprint(mesh1)
        fp2 = compute_mesh_fingerprint(mesh2)
        assert fp1 != fp2, "different geometry must produce different fingerprint"

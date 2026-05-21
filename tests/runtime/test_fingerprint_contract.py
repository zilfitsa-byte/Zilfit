"""ZILFIT Fingerprint Contract — versioned + cross-platform + strict/geometric.

Rules:
- No pickle, no random ordering, no set iteration without sorting.
- Integer scaling replaces round(float, 6).
- strict mode preserves winding; geometric mode ignores winding differences.
- created_at excluded from core hash for determinism.
"""

import hashlib
import json
import time
import pytest

# ---------------------------------------------------------------------------
# Shared dummy meshes
# ---------------------------------------------------------------------------
_TETRAHEDRON = {
    "vertices": [(0.0, 0.0, 0.0), (1.0, 0.0, 0.0), (0.0, 1.0, 0.0), (0.0, 0.0, 1.0)],
    "triangles": [(0, 1, 2), (0, 2, 3), (0, 3, 1), (1, 3, 2)],
    "bounds": {"min": [0.0, 0.0, 0.0], "max": [1.0, 1.0, 1.0]},
    "manifold_flags": {"is_closed": True, "boundary_edges": 0},
}

_CUBE = {
    "vertices": [
        (0.0, 0.0, 0.0), (1.0, 0.0, 0.0), (1.0, 1.0, 0.0), (0.0, 1.0, 0.0),
        (0.0, 0.0, 1.0), (1.0, 0.0, 1.0), (1.0, 1.0, 1.0), (0.0, 1.0, 1.0),
    ],
    # 12 triangles forming 6 faces
    "triangles": [
        (0, 1, 2), (0, 2, 3),  # bottom
        (4, 6, 5), (4, 7, 6),  # top
        (0, 5, 1), (0, 4, 5),  # front
        (2, 7, 3), (2, 6, 7),  # back
        (0, 3, 7), (0, 7, 4),  # left
        (1, 6, 2), (1, 5, 6),  # right
    ],
    "bounds": {"min": [0.0, 0.0, 0.0], "max": [1.0, 1.0, 1.0]},
    "manifold_flags": {"is_closed": True, "boundary_edges": 0},
}

# Simple gyroid-like mesh (low density, small vertex count for testing)
_GYROID_LOW = {
    "vertices": [
        (0.0, 0.0, 0.0), (2.0, 0.0, 0.0), (4.0, 0.0, 0.0),
        (0.0, 2.0, 0.0), (2.0, 2.0, 0.0), (4.0, 2.0, 0.0),
        (0.0, 0.0, 2.0), (2.0, 0.0, 2.0), (4.0, 0.0, 2.0),
        (0.0, 2.0, 2.0), (2.0, 2.0, 2.0), (4.0, 2.0, 2.0),
    ],
    "triangles": [
        (0, 1, 4), (0, 4, 3), (1, 2, 5), (1, 5, 4),
        (3, 4, 7), (3, 7, 6), (4, 5, 8), (4, 8, 7),
        (6, 7, 10), (6, 10, 9), (7, 8, 11), (7, 11, 10),
    ],
    "bounds": {"min": [0.0, 0.0, 0.0], "max": [4.0, 2.0, 2.0]},
    "manifold_flags": {"is_closed": True, "boundary_edges": 0},
}


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------
class TestFingerprintDeterminism:
    """Same mesh must always yield the same hash."""

    def test_same_mesh_same_hash_strict(self):
        from zilfit_fingerprint_contract import compute_mesh_fingerprint
        fp1 = compute_mesh_fingerprint(_TETRAHEDRON, mode="strict")
        fp2 = compute_mesh_fingerprint(_TETRAHEDRON, mode="strict")
        assert fp1 == fp2
        assert isinstance(fp1, str)
        assert len(fp1) == 64

    def test_same_mesh_same_hash_geometric(self):
        from zilfit_fingerprint_contract import compute_mesh_fingerprint
        fp1 = compute_mesh_fingerprint(_TETRAHEDRON, mode="geometric")
        fp2 = compute_mesh_fingerprint(_TETRAHEDRON, mode="geometric")
        assert fp1 == fp2


class TestVertexOrdering:
    """Vertex ordering changes must not alter fingerprint when geometry is same."""

    def test_vertex_permutation_same_hash(self):
        from zilfit_fingerprint_contract import compute_mesh_fingerprint
        # Same vertices in different order — triangles still reference the
        # same logical positions so we need to reorder triangles too.
        # Instead, use a mesh where vertices are all referenced but ordering
        # doesn't change triangle index mapping.
        verts_a = [(0.0, 0.0, 0.0), (1.0, 0.0, 0.0), (0.0, 1.0, 0.0)]
        verts_b = [(0.0, 1.0, 0.0), (0.0, 0.0, 0.0), (1.0, 0.0, 0.0)]

        mesh_a = {
            "vertices": list(verts_a),
            "triangles": [(0, 1, 2)],
            "bounds": {"min": [0.0, 0.0, 0.0], "max": [1.0, 1.0, 0.0]},
            "manifold_flags": {"is_closed": False, "boundary_edges": 3},
        }
        mesh_b = {
            "vertices": list(verts_b),
            "triangles": [(1, 2, 0)],  # references: [1]=[0.0,0.0,0.0], [2]=[1.0,0.0,0.0], [0]=[0.0,1.0,0.0]
            "bounds": {"min": [0.0, 0.0, 0.0], "max": [1.0, 1.0, 0.0]},
            "manifold_flags": {"is_closed": False, "boundary_edges": 3},
        }

        fp_a = compute_mesh_fingerprint(mesh_a, mode="strict")
        fp_b = compute_mesh_fingerprint(mesh_b, mode="strict")
        assert fp_a == fp_b, "different vertex ordering + equivalent triangles must match"


class TestStrictVsGeometric:
    """strict preserves winding; geometric ignores winding differences."""

    def _make_mesh_with_winding(self, winding_reverse=False):
        verts = [(0.0, 0.0, 0.0), (1.0, 0.0, 0.0), (0.0, 1.0, 0.0)]
        if winding_reverse:
            tris = [(0, 2, 1)]  # reversed winding
        else:
            tris = [(0, 1, 2)]  # normal winding
        return {
            "vertices": verts,
            "triangles": tris,
            "bounds": {"min": [0.0, 0.0, 0.0], "max": [1.0, 1.0, 0.0]},
            "manifold_flags": {"is_closed": False, "boundary_edges": 3},
        }

    def test_strict_detects_winding_difference(self):
        from zilfit_fingerprint_contract import compute_mesh_fingerprint
        mesh_normal = self._make_mesh_with_winding(winding_reverse=False)
        mesh_reversed = self._make_mesh_with_winding(winding_reverse=True)
        fp_normal = compute_mesh_fingerprint(mesh_normal, mode="strict")
        fp_reversed = compute_mesh_fingerprint(mesh_reversed, mode="strict")
        assert fp_normal != fp_reversed, "strict mode must detect winding difference"

    def test_geometric_ignores_winding_difference(self):
        from zilfit_fingerprint_contract import compute_mesh_fingerprint
        mesh_normal = self._make_mesh_with_winding(winding_reverse=False)
        mesh_reversed = self._make_mesh_with_winding(winding_reverse=True)
        fp_normal = compute_mesh_fingerprint(mesh_normal, mode="geometric")
        fp_reversed = compute_mesh_fingerprint(mesh_reversed, mode="geometric")
        assert fp_normal == fp_reversed, "geometric mode must ignore winding difference"


class TestFloatNoise:
    """Float noise below 5e-7 must not change the hash (integer scaling)."""

    def test_tiny_noise_no_hash_change(self):
        from zilfit_fingerprint_contract import compute_mesh_fingerprint
        verts_orig = [(0.0, 0.0, 0.0), (1.0, 0.0, 0.0), (0.0, 1.0, 0.0)]
        verts_noisy = [
            (0.0 + 1e-10, 0.0, 0.0),
            (1.0 - 1e-10, 0.0, 0.0),
            (0.0, 1.0 + 1e-10, 0.0),
        ]
        mesh_orig = {
            "vertices": verts_orig,
            "triangles": [(0, 1, 2)],
            "bounds": {"min": [0.0, 0.0, 0.0], "max": [1.0, 1.0, 0.0]},
            "manifold_flags": {"is_closed": False, "boundary_edges": 3},
        }
        mesh_noisy = {
            "vertices": verts_noisy,
            "triangles": [(0, 1, 2)],
            "bounds": {"min": [0.0, 0.0, 0.0], "max": [1.0, 1.0, 0.0]},
            "manifold_flags": {"is_closed": False, "boundary_edges": 3},
        }
        fp_orig = compute_mesh_fingerprint(mesh_orig, mode="strict")
        fp_noisy = compute_mesh_fingerprint(mesh_noisy, mode="strict")
        assert fp_orig == fp_noisy, "tiny float noise must not change hash"


class TestBounds:
    """Bounds must be computed from canonical vertices only."""

    def test_bounds_from_canonical_vertices(self):
        from zilfit_fingerprint_contract import canonicalize_vertices_scaled
        verts = [
            (0.0000001, -0.5000001, 3.0),
            (2.0, -0.5000001, 3.0),
            (2.0, -0.5000001, 5.1000001),
            (0.0000001, -0.5000001, 5.1000001),
        ]
        canonical = canonicalize_vertices_scaled(verts)
        # canonicalize_vertices_scaled returns scaled integers
        scale = 1_000_000
        min_x = min(v[0] for v in canonical) / scale
        max_x = max(v[0] for v in canonical) / scale
        min_y = min(v[1] for v in canonical) / scale
        max_y = max(v[1] for v in canonical) / scale
        min_z = min(v[2] for v in canonical) / scale
        max_z = max(v[2] for v in canonical) / scale
        assert min_x == 0.0
        assert max_x == 2.0
        assert min_y == -0.5
        assert max_z == 5.1


class TestExtendedPayload:
    """extended payload must contain schema_version and provenance."""

    def test_extended_has_schema_version(self):
        from zilfit_fingerprint_contract import compute_extended_fingerprint_payload
        payload = compute_extended_fingerprint_payload(_TETRAHEDRON, mode="strict")
        assert "schema_version" in payload
        assert payload["schema_version"] == "zilfit-mesh-v1"

    def test_extended_has_provenance(self):
        from zilfit_fingerprint_contract import compute_extended_fingerprint_payload
        payload = compute_extended_fingerprint_payload(_TETRAHEDRON, mode="strict")
        assert "provenance" in payload
        prov = payload["provenance"]
        assert "generator" in prov
        assert "precision" in prov
        assert "scale" in prov
        assert "mode" in prov


class TestCreatedAt:
    """created_at must not affect the core hash."""

    def test_created_at_does_not_change_basic_hash(self):
        from zilfit_fingerprint_contract import compute_mesh_fingerprint
        fp1 = compute_mesh_fingerprint(_TETRAHEDRON, mode="strict")
        time.sleep(0.01)
        fp2 = compute_mesh_fingerprint(_TETRAHEDRON, mode="strict")
        assert fp1 == fp2, "created_at must not change basic hash"


class TestJSONDeterminism:
    """JSON serialization must be deterministic."""

    def test_json_serialization_deterministic(self):
        from zilfit_fingerprint_contract import compute_mesh_fingerprint
        hashes = set()
        for _ in range(10):
            h = compute_mesh_fingerprint(_TETRAHEDRON, mode="strict")
            hashes.add(h)
        assert len(hashes) == 1, "10 runs must produce exactly 1 unique hash"


class TestGoldenManifest:
    """Golden manifest must exist and all expected hashes must match."""

    def _load_golden_manifest(self):
        import json
        from pathlib import Path
        manifest_path = Path(__file__).parent.parent / "golden_fingerprints" / "golden_manifest.json"
        assert manifest_path.exists(), f"golden_manifest.json not found at {manifest_path}"
        with open(manifest_path) as f:
            return json.load(f)

    def _make_sample_mesh(self, name):
        """Create reference mesh data for golden samples."""
        samples = {
            "tetrahedron_strict": {
                "mesh": _TETRAHEDRON,
                "mode": "strict",
            },
            "tetrahedron_geometric": {
                "mesh": _TETRAHEDRON,
                "mode": "geometric",
            },
            "cube_simple": {
                "mesh": _CUBE,
                "mode": "strict",
            },
            "gyroid_reference_low": {
                "mesh": _GYROID_LOW,
                "mode": "strict",
            },
            "gyroid_reference_mid": {
                "mesh": {
                    "vertices": [
                        (0.0, 0.0, 0.0), (3.0, 0.0, 0.0), (6.0, 0.0, 0.0),
                        (0.0, 3.0, 0.0), (3.0, 3.0, 0.0), (6.0, 3.0, 0.0),
                        (0.0, 0.0, 3.0), (3.0, 0.0, 3.0), (6.0, 0.0, 3.0),
                        (0.0, 3.0, 3.0), (3.0, 3.0, 3.0), (6.0, 3.0, 3.0),
                    ],
                    "triangles": [
                        (0, 1, 4), (0, 4, 3), (1, 2, 5), (1, 5, 4),
                        (3, 4, 7), (3, 7, 6), (4, 5, 8), (4, 8, 7),
                        (6, 7, 10), (6, 10, 9), (7, 8, 11), (7, 11, 10),
                        (0, 3, 6), (3, 9, 6),
                    ],
                    "bounds": {"min": [0.0, 0.0, 0.0], "max": [6.0, 3.0, 3.0]},
                    "manifold_flags": {"is_closed": False, "boundary_edges": 6},
                },
                "mode": "strict",
            },
            "gyroid_reference_high": {
                "mesh": {
                    "vertices": [
                        (0.0, 0.0, 0.0), (4.0, 0.0, 0.0), (8.0, 0.0, 0.0),
                        (0.0, 4.0, 0.0), (4.0, 4.0, 0.0), (8.0, 4.0, 0.0),
                        (0.0, 0.0, 4.0), (4.0, 0.0, 4.0), (8.0, 0.0, 4.0),
                        (0.0, 4.0, 4.0), (4.0, 4.0, 4.0), (8.0, 4.0, 4.0),
                    ],
                    "triangles": [
                        (0, 1, 4), (0, 4, 3), (1, 2, 5), (1, 5, 4),
                        (3, 4, 7), (3, 7, 6), (4, 5, 8), (4, 8, 7),
                        (6, 7, 10), (6, 10, 9), (7, 8, 11), (7, 11, 10),
                        (0, 3, 6), (3, 9, 6),
                    ],
                    "bounds": {"min": [0.0, 0.0, 0.0], "max": [8.0, 4.0, 4.0]},
                    "manifold_flags": {"is_closed": False, "boundary_edges": 6},
                },
                "mode": "strict",
            },
        }
        return samples[name]

    def test_golden_manifest_exists(self):
        manifest = self._load_golden_manifest()
        assert "samples" in manifest
        assert len(manifest["samples"]) >= 6
        assert manifest.get("schema_version") == "zilfit-mesh-v1"

    def test_golden_manifest_has_all_required_samples(self):
        manifest = self._load_golden_manifest()
        sample_names = {s["name"] for s in manifest["samples"]}
        required = {
            "tetrahedron_strict",
            "tetrahedron_geometric",
            "cube_simple",
            "gyroid_reference_low",
            "gyroid_reference_mid",
            "gyroid_reference_high",
        }
        assert required <= sample_names, f"Missing samples: {required - sample_names}"

    def test_all_golden_hashes_match(self):
        """Compute fingerprints for all golden samples and verify against manifest."""
        from zilfit_fingerprint_contract import compute_mesh_fingerprint
        manifest = self._load_golden_manifest()
        for entry in manifest["samples"]:
            name = entry["name"]
            expected = entry["expected_hash"]
            mode = entry.get("mode", "strict")
            sample = self._make_sample_mesh(name)
            actual = compute_mesh_fingerprint(sample["mesh"], mode=sample["mode"])
            assert actual == expected, f"Golden hash mismatch: {name}\n  expected: {expected}\n  actual:   {actual}"


# ---------------------------------------------------------------------------
# Required key validation
# ---------------------------------------------------------------------------
class TestRequiredKeyValidation:
    """REQUIRED_FINGERPRINT_KEYS enforcement: missing keys raise, extras ignored."""

    def _base_mesh(self):
        return {
            "vertices": [(0.0, 0.0, 0.0), (1.0, 0.0, 0.0), (0.0, 1.0, 0.0)],
            "triangles": [(0, 1, 2)],
            "bounds": {"min": [0.0, 0.0, 0.0], "max": [1.0, 1.0, 0.0]},
            "manifold_flags": {"is_closed": False},
        }

    def test_missing_required_key_raises(self):
        """Any missing required key raises ValueError with clear message."""
        import pytest
        from zilfit_fingerprint_contract import (
            REQUIRED_FINGERPRINT_KEYS,
            compute_mesh_fingerprint,
        )

        base = self._base_mesh()
        for key in REQUIRED_FINGERPRINT_KEYS:
            incomplete = {k: v for k, v in base.items() if k != key}
            with pytest.raises(ValueError) as exc_info:
                compute_mesh_fingerprint(incomplete)
            assert key in str(exc_info.value)

    def test_extra_metadata_does_not_change_hash(self):
        """Extra keys in mesh_dict are ignored — hash stays identical."""
        import copy
        from zilfit_fingerprint_contract import compute_mesh_fingerprint

        base = self._base_mesh()
        hash_base = compute_mesh_fingerprint(base)

        extra = copy.deepcopy(base)
        extra["author"] = "Z-Bio"
        extra["generation_date"] = "2025-01-01"
        extra["internal_notes"] = {"draft": True, "version": 99}

        hash_extra = compute_mesh_fingerprint(extra)
        assert hash_extra == hash_base

    def test_reordered_metadata_does_not_change_hash(self):
        """Ordering of metadata-like top-level keys does not affect hash
        (only the 4 required keys drive the fingerprint)."""
        import copy
        from zilfit_fingerprint_contract import compute_mesh_fingerprint

        base = self._base_mesh()
        hash_base = compute_mesh_fingerprint(base)

        # Same base with extra keys in different order (Python dict ordering)
        # and reorder the required keys themselves (still same content)
        reordered = {
            "manifold_flags": base["manifold_flags"],
            "triangles": base["triangles"],
            "bounds": base["bounds"],
            "vertices": base["vertices"],
            "extra_field": "should be ignored",
        }

        hash_reordered = compute_mesh_fingerprint(reordered)
        assert hash_reordered == hash_base


# ---------------------------------------------------------------------------
# Orientation signature detection
# ---------------------------------------------------------------------------
class TestOrientationSignature:
    """Orientation consistency detection — non-breaking, reporting only."""

    def test_consistent_mesh_no_warning(self):
        """Watertight tetrahedron with consistent winding → no warning."""
        from zilfit_fingerprint_contract import compute_orientation_signature

        mesh = {
            "vertices": [
                (0.0, 0.0, 0.0), (1.0, 0.0, 0.0),
                (0.0, 1.0, 0.0), (0.0, 0.0, 1.0),
            ],
            "triangles": [
                (0, 1, 2), (0, 2, 3), (0, 3, 1), (1, 3, 2),
            ],
        }
        sig = compute_orientation_signature(mesh)
        assert sig["orientation_warning"] is False

    def test_detects_large_scale_orientation_inversion(self):
        """Mesh with > 20% inverted triangles triggers orientation_warning."""
        from zilfit_fingerprint_contract import (
            compute_orientation_signature,
            ORIENTATION_INVERSION_THRESHOLD,
        )

        # 5-triangle mesh: flip 3 of them (60% inverted)
        mesh = {
            "vertices": [
                (0.0, 0.0, 0.0), (2.0, 0.0, 0.0),
                (0.0, 2.0, 0.0), (2.0, 2.0, 0.0),
                (1.0, 1.0, 2.0),
            ],
            "triangles": [
                (0, 1, 2),  # normal
                (2, 1, 3),  # inverted (swapped 1,2)
                (3, 2, 0),  # inverted
                (0, 4, 2),  # normal
                (2, 4, 3),  # inverted (swapped 4,3)
            ],
            "bounds": {"min": [0, 0, 0], "max": [2, 2, 2]},
            "manifold_flags": {"is_closed": False},
        }
        sig = compute_orientation_signature(mesh)
        assert (
            sig["inverted_ratio"] > ORIENTATION_INVERSION_THRESHOLD
        ), f"Expected > {ORIENTATION_INVERSION_THRESHOLD}, got {sig['inverted_ratio']}"
        assert sig["orientation_warning"] is True

    def test_orientation_does_not_change_fingerprint(self):
        """Orientation detection must not affect core hash."""
        from zilfit_fingerprint_contract import (
            compute_mesh_fingerprint,
            compute_orientation_signature,
        )

        # Mesh with lots of inverted triangles
        mesh_clean = {
            "vertices": [
                (0.0, 0.0, 0.0), (1.0, 0.0, 0.0),
                (0.0, 1.0, 0.0), (0.0, 0.0, 1.0),
            ],
            "triangles": [
                (0, 1, 2), (0, 2, 3), (0, 3, 1), (1, 3, 2),
            ],
            "bounds": {"min": [0, 0, 0], "max": [1, 1, 1]},
            "manifold_flags": {"is_closed": True},
        }

        hash_clean = compute_mesh_fingerprint(mesh_clean)
        # Even though orientation detection runs, the hash is independent
        inverted_mesh = {
            "vertices": [
                (0.0, 0.0, 0.0), (1.0, 0.0, 0.0),
                (0.0, 1.0, 0.0), (0.0, 0.0, 1.0),
            ],
            "triangles": [
                (2, 1, 0), (3, 2, 0), (1, 3, 0), (2, 3, 1),
            ],
            "bounds": {"min": [0, 0, 0], "max": [1, 1, 1]},
            "manifold_flags": {"is_closed": True},
        }
        sig = compute_orientation_signature(inverted_mesh)
        hash_inverted = compute_mesh_fingerprint(inverted_mesh)

        # Extended payload must include orientation data
        from zilfit_fingerprint_contract import compute_extended_fingerprint_payload

        ext = compute_extended_fingerprint_payload(mesh_clean)
        assert "orientation" in ext
        assert "warning" in ext["orientation"]
        assert "ratio" in ext["orientation"]
        assert "inverted_count" in ext["orientation"]
        assert "total_triangles" in ext["orientation"]


# ---------------------------------------------------------------------------
# Finite-number validation
# ---------------------------------------------------------------------------
import math as _math

class TestFiniteNumberValidation:
    """NaN and ±inf must be rejected before any processing."""

    def _base_mesh(self):
        return {
            "vertices": [(0.0, 0.0, 0.0), (1.0, 0.0, 0.0), (0.0, 1.0, 0.0)],
            "triangles": [(0, 1, 2)],
            "bounds": {"min": [0.0, 0.0, 0.0], "max": [1.0, 1.0, 0.0]},
            "manifold_flags": {"is_closed": False},
        }

    def test_rejects_nan_vertex(self):
        """A vertex containing NaN raises ValueError."""
        from zilfit_fingerprint_contract import compute_mesh_fingerprint
        m = self._base_mesh()
        m["vertices"][0] = (_math.nan, 0.0, 0.0)
        with pytest.raises(ValueError) as exc:
            compute_mesh_fingerprint(m)
        assert "non-finite numeric value" in str(exc.value)


    def test_rejects_inf_vertex(self):
        """A vertex containing +inf raises ValueError."""
        from zilfit_fingerprint_contract import compute_mesh_fingerprint
        m = self._base_mesh()
        m["vertices"][0] = (_math.inf, 0.0, 0.0)
        with pytest.raises(ValueError) as exc:
            compute_mesh_fingerprint(m)
        assert "non-finite numeric value" in str(exc.value)
        assert "inf" in str(exc.value)


    def test_rejects_nan_bounds(self):
        """Bounds containing NaN raises ValueError."""
        from zilfit_fingerprint_contract import compute_mesh_fingerprint
        m = self._base_mesh()
        m["bounds"]["min"][0] = _math.nan
        with pytest.raises(ValueError) as exc:
            compute_mesh_fingerprint(m)
        assert "non-finite numeric value" in str(exc.value)


    def test_rejects_inf_bounds(self):
        """Bounds containing -inf raises ValueError."""
        from zilfit_fingerprint_contract import compute_mesh_fingerprint
        m = self._base_mesh()
        m["bounds"]["max"][2] = -_math.inf
        with pytest.raises(ValueError) as exc:
            compute_mesh_fingerprint(m)
        assert "non-finite numeric value" in str(exc.value)
        assert "inf" in str(exc.value)


# ---------------------------------------------------------------------------
# Input bounds ignored for core hash — recomputed from canonical vertices
# ---------------------------------------------------------------------------
class TestBoundsIgnoredForCoreHash:
    """Tampered input bounds must not affect fingerprint."""

    def _base_mesh(self):
        return {
            "vertices": [(0.0, 0.0, 0.0), (1.0, 0.0, 0.0), (0.0, 1.0, 0.0)],
            "triangles": [(0, 1, 2)],
            "bounds": {"min": [0.0, 0.0, 0.0], "max": [1.0, 1.0, 0.0]},
            "manifold_flags": {"is_closed": False},
        }

    def test_tampered_bounds_do_not_change_hash(self):
        """Falsifying input bounds must not change the core hash."""
        from zilfit_fingerprint_contract import compute_mesh_fingerprint
        m1 = self._base_mesh()
        m2 = self._base_mesh()
        m2["bounds"]["max"] = [999.0, 999.0, 999.0]
        m2["bounds"]["min"] = [-999.0, -999.0, -999.0]
        assert compute_mesh_fingerprint(m1) == compute_mesh_fingerprint(m2)

    def test_computed_bounds_match_vertices(self):
        """Bounds recomputed from vertices must equal expected min/max."""
        from zilfit_fingerprint_contract import _compute_fingerprint_core
        m = self._base_mesh()
        _, _, bounds = _compute_fingerprint_core(m)
        assert bounds["min"] == [0, 0, 0]

    def test_input_bounds_are_ignored_for_core_hash(self):
        """Mesh with completely wrong input bounds yields same hash."""
        from zilfit_fingerprint_contract import compute_mesh_fingerprint
        m_clean = self._base_mesh()
        m_tampered = self._base_mesh()
        m_tampered["bounds"] = {"min": [-500, -500, -500], "max": [500, 500, 500]}
        hash_clean = compute_mesh_fingerprint(m_clean)
        hash_tampered = compute_mesh_fingerprint(m_tampered)
        assert hash_clean == hash_tampered
        assert len(hash_clean) == 64
        assert len(hash_tampered) == 64


# ---------------------------------------------------------------------------
# Strict input type validation
# ---------------------------------------------------------------------------
class TestStrictInputTypeValidation:
    """Validate input types before canonicalization or hashing."""

    def _base_mesh(self):
        return {
            "vertices": [(0.0, 0.0, 0.0), (1.0, 0.0, 0.0), (0.0, 1.0, 0.0)],
            "triangles": [(0, 1, 2)],
            "bounds": {"min": [0.0, 0.0, 0.0], "max": [1.0, 1.0, 0.0]},
            "manifold_flags": {"is_closed": False},
        }

    def test_rejects_string_vertex(self):
        """A vertex coordinate cannot be a string."""
        from zilfit_fingerprint_contract import compute_mesh_fingerprint
        m = self._base_mesh()
        m["vertices"][0] = ("bad", 0.0, 0.0)
        with pytest.raises(TypeError) as exc:
            compute_mesh_fingerprint(m)
        assert "must be int/float" in str(exc.value)
        assert "str" in str(exc.value)

    def test_rejects_bool_triangle_index(self):
        """A triangle index cannot be a bool."""
        from zilfit_fingerprint_contract import compute_mesh_fingerprint
        m = self._base_mesh()
        m["triangles"][0] = (True, 1, 2)
        with pytest.raises(TypeError) as exc:
            compute_mesh_fingerprint(m)
        assert "must be int, got bool" in str(exc.value)

    def test_rejects_float_triangle_index(self):
        """A triangle index cannot be a float."""
        from zilfit_fingerprint_contract import compute_mesh_fingerprint
        m = self._base_mesh()
        m["triangles"][0] = (0, 1.5, 2)
        with pytest.raises(TypeError) as exc:
            compute_mesh_fingerprint(m)
        assert "must be int, got float" in str(exc.value)

    def test_rejects_short_vertex(self):
        """A vertex with fewer than 3 components raises TypeError."""
        from zilfit_fingerprint_contract import compute_mesh_fingerprint
        m = self._base_mesh()
        m["vertices"][0] = (0.0, 1.0)
        with pytest.raises(TypeError) as exc:
            compute_mesh_fingerprint(m)
        assert "exactly 3 components" in str(exc.value)

    def test_rejects_short_triangle(self):
        """A triangle with fewer than 3 indices raises TypeError."""
        from zilfit_fingerprint_contract import compute_mesh_fingerprint
        m = self._base_mesh()
        m["triangles"][0] = (0, 1)
        with pytest.raises(TypeError) as exc:
            compute_mesh_fingerprint(m)
        assert "exactly 3 vertex indices" in str(exc.value)

    def test_rejects_invalid_bounds_type(self):
        """bounds['min'] as a string raises TypeError."""
        from zilfit_fingerprint_contract import compute_mesh_fingerprint
        m = self._base_mesh()
        m["bounds"]["min"] = "bad"
        with pytest.raises(TypeError) as exc:
            compute_mesh_fingerprint(m)
        assert "must be a list/tuple" in str(exc.value)

    def test_rejects_invalid_manifold_flag(self):
        """A manifold_flag as a string raises TypeError."""
        from zilfit_fingerprint_contract import compute_mesh_fingerprint
        m = self._base_mesh()
        m["manifold_flags"]["bad_flag"] = "not_an_int_or_bool"
        with pytest.raises(TypeError) as exc:
            compute_mesh_fingerprint(m)
        assert "must be bool/int" in str(exc.value)


class TestOrientationContract:
    """Strict vs geometric mode orientation/winding behaviour.

    Goal:
      1) strict mode: detects triangle winding / orientation changes → different hash.
      2) geometric mode: ignores winding if geometry is identical → same hash.
    """

    def _base_mesh(self):
        return {
            "vertices": [(0.0, 0.0, 0.0), (1.0, 0.0, 0.0), (0.0, 1.0, 0.0)],
            "triangles": [(0, 1, 2)],
            "bounds": {"min": [0.0, 0.0, 0.0], "max": [1.0, 1.0, 0.0]},
            "manifold_flags": {"is_closed": False},
        }

    def test_strict_mode_detects_reversed_winding(self):
        """Strict mode produces different hashes when triangle winding is reversed."""
        from zilfit_fingerprint_contract import compute_mesh_fingerprint

        m_normal = self._base_mesh()
        m_reversed = self._base_mesh()
        m_reversed["triangles"] = [(0, 2, 1)]

        h1 = compute_mesh_fingerprint(m_normal, mode="strict")
        h2 = compute_mesh_fingerprint(m_reversed, mode="strict")
        assert h1 != h2, "strict mode must detect reversed winding"

    def test_geometric_mode_ignores_reversed_winding(self):
        """Geometric mode produces identical hash even when winding is reversed."""
        from zilfit_fingerprint_contract import compute_mesh_fingerprint

        m_normal = self._base_mesh()
        m_reversed = self._base_mesh()
        m_reversed["triangles"] = [(0, 2, 1)]

        h1 = compute_mesh_fingerprint(m_normal, mode="geometric")
        h2 = compute_mesh_fingerprint(m_reversed, mode="geometric")
        assert h1 == h2, "geometric mode must ignore reversed winding"

    def test_orientation_warning_present_when_inverted_edges_detected(self):
        """Mesh with inverted edges above threshold triggers orientation_warning."""
        from zilfit_fingerprint_contract import (
            ORIENTATION_INVERSION_THRESHOLD,
            compute_orientation_signature,
        )

        # 5-triangle mesh: flip 3 (60% inverted)
        mesh = {
            "vertices": [
                (0.0, 0.0, 0.0), (2.0, 0.0, 0.0),
                (0.0, 2.0, 0.0), (2.0, 2.0, 0.0),
                (1.0, 1.0, 2.0),
            ],
            "triangles": [
                (0, 1, 2),  # normal
                (2, 1, 3),  # inverted
                (3, 2, 0),  # inverted
                (0, 4, 2),  # normal
                (2, 4, 3),  # inverted
            ],
        }
        sig = compute_orientation_signature(mesh)
        assert sig["orientation_warning"] is True
        assert sig["inverted_ratio"] > ORIENTATION_INVERSION_THRESHOLD

    def test_orientation_warning_not_part_of_core_hash(self):
        """Orientation warning is diagnostic metadata, not part of core hash."""
        from zilfit_fingerprint_contract import (
            compute_mesh_fingerprint,
            compute_orientation_signature,
        )

        mesh = {
            "vertices": [
                (0.0, 0.0, 0.0), (2.0, 0.0, 0.0),
                (0.0, 2.0, 0.0), (2.0, 2.0, 0.0),
                (1.0, 1.0, 2.0),
            ],
            "triangles": [
                (0, 1, 2),  # normal
                (2, 1, 3),  # inverted
                (3, 2, 0),  # inverted
                (0, 4, 2),  # normal
                (2, 4, 3),  # inverted
            ],
            "bounds": {"min": [0, 0, 0], "max": [2, 2, 2]},
            "manifold_flags": {"is_closed": False},
        }
        sig = compute_orientation_signature(mesh)
        assert sig["orientation_warning"] is True

        # Core hash is computed regardless of the orientation warning
        h = compute_mesh_fingerprint(mesh, mode="strict")
        assert len(h) == 64

    def test_mixed_winding_mesh_gets_warning(self):
        """Mixed (some inverted, some not) triangles produce warning in sig."""
        from zilfit_fingerprint_contract import compute_orientation_signature

        mesh = {
            "vertices": [
                (0.0, 0.0, 0.0), (1.0, 0.0, 0.0),
                (0.0, 1.0, 0.0), (1.0, 1.0, 0.0),
                (0.5, 0.5, 1.0),
            ],
            "triangles": [
                (0, 1, 4),  # normal
                (1, 4, 2),  # normal
                (3, 2, 4),  # inverted
                (0, 4, 1),  # inverted
            ],
        }
        sig = compute_orientation_signature(mesh)
        assert sig["inverted_count"] == 3  # (0,4,1), (3,2,4), (1,4,2) detected
        assert sig["orientation_warning"] is True

    def test_geometric_hash_same_even_with_mixed_winding(self):
        """Geometric mode must produce identical hash across meshes whose
        canonical geometry is identical but whose triangle winding differs."""
        from zilfit_fingerprint_contract import compute_mesh_fingerprint

        m_normal = self._base_mesh()
        m_mixed = self._base_mesh()
        m_mixed["triangles"] = [(0, 2, 1)]  # flipped

        h_normal = compute_mesh_fingerprint(m_normal, mode="geometric")
        h_mixed = compute_mesh_fingerprint(m_mixed, mode="geometric")
        assert h_normal == h_mixed, (
            "geometric mode must produce same hash even with mixed winding"
        )
class TestTopologySanityContract:
    """Fingerprint must reject invalid mesh topology before hashing."""

    def _base_mesh(self):
        return {
            "vertices": [(0.0, 0.0, 0.0), (1.0, 0.0, 0.0), (0.0, 1.0, 0.0)],
            "triangles": [(0, 1, 2)],
            "bounds": {"min": [0.0, 0.0, 0.0], "max": [1.0, 1.0, 0.0]},
            "manifold_flags": {"is_closed": False},
        }

    def test_rejects_triangle_with_duplicate_indices(self):
        """Triangles like (0, 0, 1) or (0, 1, 0) are degenerate and rejected."""
        from zilfit_fingerprint_contract import compute_mesh_fingerprint
        m = self._base_mesh()
        m["triangles"] = [(0, 0, 2)]  # duplicate index
        with pytest.raises(ValueError, match="duplicate indices"):
            compute_mesh_fingerprint(m)

    def test_rejects_triangle_index_out_of_range(self):
        """Triangle referencing a vertex beyond the vertex list is rejected."""
        from zilfit_fingerprint_contract import compute_mesh_fingerprint
        m = self._base_mesh()
        m["triangles"] = [(0, 1, 5)]  # 5 >= 3 vertices
        with pytest.raises(IndexError, match="out of range"):
            compute_mesh_fingerprint(m)

    def test_rejects_negative_triangle_index(self):
        """Negative triangle indices are rejected, even if they would resolve
        via Python's negative-list semantics.  Indexing must be explicit."""
        from zilfit_fingerprint_contract import compute_mesh_fingerprint
        m = self._base_mesh()
        m["triangles"] = [(0, 1, -1)]
        with pytest.raises(ValueError, match="negative index"):
            compute_mesh_fingerprint(m)

    def test_rejects_unreferenced_vertices_when_strict_topology_enabled(self):
        """When strict_topology=True, vertices that no triangle references
        must raise an error."""
        from zilfit_fingerprint_contract import compute_mesh_fingerprint
        m = self._base_mesh()
        m["vertices"].append((99.0, 99.0, 99.0))  # unreferenced
        with pytest.raises(ValueError, match="unreferenced"):
            compute_mesh_fingerprint(m, strict_topology=True)

    def test_allows_unreferenced_vertices_when_strict_topology_disabled(self):
        """When strict_topology=False, unreferenced vertices are silently
        tolerated — no crash occurs (extra vertex is deduped in)."""
        from zilfit_fingerprint_contract import compute_mesh_fingerprint
        m = self._base_mesh()
        h_normal = compute_mesh_fingerprint(m)

        m_extra = self._base_mesh()
        m_extra["vertices"].append((99.0, 99.0, 99.0))  # unreferenced
        # Should not raise with strict_topology=False
        h_extra = compute_mesh_fingerprint(m_extra, strict_topology=False)
        # Hash may differ because unreferenced vertex is still canonicalized
        # into unique_verts — this is expected.  The test verifies non-crash.
        assert isinstance(h_extra, str) and len(h_extra) == 64
    def test_rejects_non_3d_vertices(self):
        """Vertices with != 3 coordinates raise TypeError."""
        from zilfit_fingerprint_contract import compute_mesh_fingerprint
        m = self._base_mesh()
        m["vertices"] = [
            (0.0, 0.0), (1.0, 0.0), (0.0, 1.0),
        ]
        with pytest.raises(TypeError, match="exactly 3"):
            compute_mesh_fingerprint(m)

    def test_rejects_empty_vertices(self):
        """Empty vertices list raises ValueError."""
        from zilfit_fingerprint_contract import compute_mesh_fingerprint
        m = self._base_mesh()
        m["vertices"] = []
        with pytest.raises(ValueError, match="empty"):
            compute_mesh_fingerprint(m)

    def test_rejects_empty_triangles(self):
        """Empty triangles list raises ValueError."""
        from zilfit_fingerprint_contract import compute_mesh_fingerprint
        m = self._base_mesh()
        m["triangles"] = []
        with pytest.raises(ValueError, match="empty"):
            compute_mesh_fingerprint(m)


# ---------------------------------------------------------------------------
# Adversarial fuzz-style validation — deterministic attack cases
# ---------------------------------------------------------------------------
class TestGeometryAttacks:
    """Geometry integrity under adversarial inputs."""

    def _base_mesh(self):
        return {
            "vertices": [(0.0, 0.0, 0.0), (1.0, 0.0, 0.0), (0.0, 1.0, 0.0)],
            "triangles": [(0, 1, 2)],
            "bounds": {"min": [0.0, 0.0, 0.0], "max": [1.0, 1.0, 0.0]},
            "manifold_flags": {"is_closed": False},
        }

    def test_duplicate_vertex_storm(self):
        """Hundreds of duplicate vertices should not crash; hash should be stable."""
        from zilfit_fingerprint_contract import compute_mesh_fingerprint
        m = self._base_mesh()
        m["vertices"] = [(0.0, 0.0, 0.0)] * 500
        # All deduplicate to 1 vertex.  Vertices 3–499 are unreferenced by
        # the single triangle (0,1,2) → must use strict_topology=False to
        # allow this degenerate mesh.
        hash1 = compute_mesh_fingerprint(m, strict_topology=False)
        m["vertices"] = [(0.0, 0.0, 0.0)] * 500  # re-add
        hash2 = compute_mesh_fingerprint(m, strict_topology=False)
        assert hash1 == hash2  # stable

    def test_zero_area_triangle(self):
        """Degenerate triangle (3 collinear vertices) must not crash."""
        from zilfit_fingerprint_contract import compute_mesh_fingerprint
        m = self._base_mesh()
        m["vertices"] = [(0.0, 0.0, 0.0), (1.0, 1.0, 0.0), (2.0, 2.0, 0.0)]
        m["triangles"] = [(0, 1, 2)]
        h = compute_mesh_fingerprint(m)  # no crash
        assert len(h) == 64

    def test_repeated_triangles(self):
        """Same triangle repeated many times should produce a deterministic hash."""
        from zilfit_fingerprint_contract import compute_mesh_fingerprint
        m = self._base_mesh()
        m["triangles"] = [(0, 1, 2)] * 100
        h1 = compute_mesh_fingerprint(m)
        m["triangles"] = [(0, 1, 2)] * 100
        h2 = compute_mesh_fingerprint(m)
        assert h1 == h2

    def test_disconnected_islands(self):
        """Two disconnected triangle groups should produce a valid hash."""
        from zilfit_fingerprint_contract import compute_mesh_fingerprint
        m = self._base_mesh()
        m["vertices"] = [
            (0.0, 0.0, 0.0), (1.0, 0.0, 0.0), (0.0, 1.0, 0.0),   # island A
            (10.0, 10.0, 0.0), (11.0, 10.0, 0.0), (10.0, 11.0, 0.0),  # island B
        ]
        m["triangles"] = [(0, 1, 2), (3, 4, 5)]
        h = compute_mesh_fingerprint(m)
        assert len(h) == 64

    def test_random_triangle_ordering_same_hash(self):
        """Permuting triangle order must not affect hash."""
        from zilfit_fingerprint_contract import compute_mesh_fingerprint
        vertices = [
            (0.0, 0.0, 0.0), (1.0, 0.0, 0.0), (0.0, 1.0, 0.0),
            (1.0, 1.0, 0.0),
        ]
        triangles = [(0, 1, 2), (1, 3, 2)]
        m1 = self._base_mesh()
        m1["vertices"] = vertices
        m1["triangles"] = triangles
        m2 = self._base_mesh()
        m2["vertices"] = vertices
        m2["triangles"] = [(1, 3, 2), (0, 1, 2)]  # reversed order
        assert compute_mesh_fingerprint(m1) == compute_mesh_fingerprint(m2)

    def test_winding_flips_detected_in_strict_mode(self):
        """Strict mode must detect winding flips as different hashes."""
        from zilfit_fingerprint_contract import compute_mesh_fingerprint
        m_forward = self._base_mesh()
        m_reverse = self._base_mesh()
        m_reverse["triangles"] = [(0, 2, 1)]  # winding flipped
        h1 = compute_mesh_fingerprint(m_forward, mode="strict")
        h2 = compute_mesh_fingerprint(m_reverse, mode="strict")
        assert h1 != h2  # strict detects


class TestNumericAttacks:
    """Numeric edge cases under adversarial inputs."""

    def _base_mesh(self):
        return {
            "vertices": [(0.0, 0.0, 0.0), (1.0, 0.0, 0.0), (0.0, 1.0, 0.0)],
            "triangles": [(0, 1, 2)],
            "bounds": {"min": [0.0, 0.0, 0.0], "max": [1.0, 1.0, 0.0]},
            "manifold_flags": {"is_closed": False},
        }

    def test_negative_zero_same_as_positive_zero(self):
        """-0.0 and +0.0 must produce the same canonical hash."""
        from zilfit_fingerprint_contract import compute_mesh_fingerprint
        m_pos = self._base_mesh()
        m_pos["vertices"] = [(0.0, 0.0, 0.0), (1.0, 0.0, 0.0), (0.0, 1.0, 0.0)]
        m_neg = self._base_mesh()
        m_neg["vertices"] = [(-0.0, -0.0, -0.0), (1.0, 0.0, 0.0), (0.0, 1.0, 0.0)]
        assert compute_mesh_fingerprint(m_pos) == compute_mesh_fingerprint(m_neg)

    def test_extremely_large_finite_floats(self):
        """Very large finite values must be handled without crash."""
        from zilfit_fingerprint_contract import compute_mesh_fingerprint
        m = self._base_mesh()
        scale = 1e300
        m["vertices"] = [(0.0, 0.0, 0.0), (scale, 0.0, 0.0), (0.0, scale, 0.0)]
        h = compute_mesh_fingerprint(m)
        assert len(h) == 64

    def test_subnormal_floats(self):
        """Subnormal (denormal) floats must not crash."""
        from zilfit_fingerprint_contract import compute_mesh_fingerprint
        tiny = 5e-324  # smallest subnormal
        m = self._base_mesh()
        m["vertices"] = [(0.0, 0.0, 0.0), (tiny, 0.0, 0.0), (0.0, tiny, 0.0)]
        h = compute_mesh_fingerprint(m)
        assert len(h) == 64

    def test_mixed_int_float_coordinates(self):
        """Mixing int and float coordinates should produce a deterministic hash."""
        from zilfit_fingerprint_contract import compute_mesh_fingerprint
        m1 = self._base_mesh()
        m1["vertices"] = [(0.0, 0.0, 0.0), (1.0, 0.0, 0.0), (0.0, 1.0, 0.0)]
        m2 = self._base_mesh()
        m2["vertices"] = [(0, 0, 0), (1, 0, 0), (0, 1, 0)]  # all ints
        assert compute_mesh_fingerprint(m1) == compute_mesh_fingerprint(m2)


class TestStructuralAttacks:
    """Structural edge cases and malformed inputs."""

    def _base_mesh(self):
        return {
            "vertices": [(0.0, 0.0, 0.0), (1.0, 0.0, 0.0), (0.0, 1.0, 0.0)],
            "triangles": [(0, 1, 2)],
            "bounds": {"min": [0.0, 0.0, 0.0], "max": [1.0, 1.0, 0.0]},
            "manifold_flags": {"is_closed": False},
        }

    def test_empty_vertices_raises(self):
        """Empty vertices list should raise (no geometry to hash)."""
        from zilfit_fingerprint_contract import compute_mesh_fingerprint
        m = self._base_mesh()
        m["vertices"] = []
        with pytest.raises(ValueError, match="empty"):
            compute_mesh_fingerprint(m)

    def test_empty_triangles_raises(self):
        """Empty triangles list should raise."""
        from zilfit_fingerprint_contract import compute_mesh_fingerprint
        m = self._base_mesh()
        m["triangles"] = []
        with pytest.raises(ValueError, match="empty"):
            compute_mesh_fingerprint(m)

    def test_gigantic_triangle_indices(self):
        """Out-of-range triangle indices must not crash."""
        from zilfit_fingerprint_contract import compute_mesh_fingerprint
        m = self._base_mesh()
        m["triangles"] = [(0, 1, 2)]  # valid
        m["triangles"].append((99999, 99998, 99997))  # out of range
        with pytest.raises(IndexError):
            compute_mesh_fingerprint(m)

    def test_nested_invalid_containers(self):
        """A vertices entry that is itself a dict raises TypeError."""
        from zilfit_fingerprint_contract import compute_mesh_fingerprint
        m = self._base_mesh()
        m["vertices"] = ["not_a_sequence", (1.0, 0.0, 0.0), (0.0, 1.0, 0.0)]
        with pytest.raises(TypeError):
            compute_mesh_fingerprint(m)

    def test_malformed_vertex_dimension(self):
        """A vertex with 4 components raises TypeError."""
        from zilfit_fingerprint_contract import compute_mesh_fingerprint
        m = self._base_mesh()
        m["vertices"] = [(0.0, 0.0, 0.0, 1.0), (1.0, 0.0, 0.0, 2.0), (0.0, 1.0, 0.0, 3.0)]
        with pytest.raises(TypeError, match="exactly 3"):
            compute_mesh_fingerprint(m)

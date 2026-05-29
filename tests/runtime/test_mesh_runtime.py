"""
ZILFIT Mesh Runtime Tests

Tests for zilfit_mesh_runtime.py:
  1) Voxel field sampling
  2) Marching cubes isosurface extraction
  3) Mesh topology validation (watertight, manifold)
  4) Triangle quality analysis
  5) Printability estimation
  6) Full pipeline (extract + validate + assess)
  7) Schema validation
"""

from __future__ import annotations

import json
import math
import pytest
from pathlib import Path
from runtime.zilfit_mesh_runtime import (
    VoxelVolume,
    MeshMetadata,
    ManifoldReport,
    PrintabilityReport,
    TriangleQualityReport,
    voxelize_field,
    extract_isosurface,
    validate_mesh_topology,
    analyze_triangle_quality,
    estimate_printability,
    extract_and_validate_mesh,
    validate_mesh_metadata_against_schema,
    _triangle_area,
    _triangle_normal,
    _edge_length,
    _triangle_angles,
    _build_full_mc_table,
    _MC_FULL_TABLE,
    MIN_WALL_THICKNESS_MM,
    DENSITY_MIN,
    DENSITY_MAX,
    GYROID_CELL_SIZE_MIN_MM,
    GYROID_CELL_SIZE_MAX_MM,
    MIN_TRIANGLE_AREA_MM2,
    MAX_ASPECT_RATIO,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------
def make_gyroid_field_fn(
    density: float = 0.25,
    cell_size: float = 6.0,
) -> callable:
    """Create a gyroid implicit field function.
    F(x,y,z) = sin(kx)*cos(ky) + sin(ky)*cos(kz) + sin(kz)*sin(kx) - t
    """
    k = math.pi / cell_size
    t = 0.4 - density * 2.0
    return lambda x, y, z: (
        math.sin(k * x) * math.cos(k * y)
        + math.sin(k * y) * math.cos(k * z)
        + math.sin(k * z) * math.sin(k * x)
        - t
    )


def make_box_field_fn() -> callable:
    """Spherical field: negative inside sphere, positive outside."""
    def fn(x, y, z):
        r = math.sqrt(x * x + y * y + z * z)
        return r - 5.0
    return fn


def make_tetrahedron() -> tuple:
    """Return a well-formed tetrahedron."""
    verts = [
        (0.0, 0.0, 0.0),
        (5.0, 0.0, 0.0),
        (2.5, 5.0, 0.0),
        (2.5, 2.5, 4.0),
    ]
    tris = [
        (0, 1, 2),  # bottom
        (0, 2, 3),  # face
        (1, 3, 2),  # face
        (0, 3, 1),  # face
    ]
    return verts, tris


# ===========================================================================
# 1) Voxel Field Sampling
# ===========================================================================
class TestVoxelizeField:

    def test_grid_shape_preserved(self):
        vol = voxelize_field(make_gyroid_field_fn(), (8, 12, 6), 1.0, 1.0, 1.0)
        assert vol.grid_shape == (8, 12, 6)

    def test_total_voxels_product(self):
        vol = voxelize_field(make_gyroid_field_fn(), (5, 4, 3), 1.0, 1.0, 1.0)
        assert vol.total_voxels == 60

    def test_field_values_length_matches(self):
        vol = voxelize_field(make_gyroid_field_fn(), (5, 4, 3), 1.0, 1.0, 1.0)
        assert len(vol.field_values) == 60

    def test_sphere_negative_inside(self):
        vol = voxelize_field(
            make_box_field_fn(), (11, 11, 11), 1.0, 1.0, 1.0,
            origin=(-5.0, -5.0, -5.0),
        )
        center = vol.field_values[5 + 5 * 11 + 5 * 11 * 11]
        assert center < 0  # center is inside sphere radius 5

    def test_sphere_positive_outside(self):
        vol = voxelize_field(
            make_box_field_fn(), (11, 11, 11), 1.0, 1.0, 1.0,
            origin=(-5.0, -5.0, -5.0),
        )
        corner = vol.field_values[0]  # at (-5,-5,-5), distance ~8.66
        assert corner > 0  # outside

    def test_origin_applied(self):
        vol = voxelize_field(
            make_gyroid_field_fn(), (2, 2, 2), 1.0, 1.0, 1.0,
            origin=(10.0, 20.0, 30.0),
        )
        assert vol.origin == (10.0, 20.0, 30.0)

    def test_to_dict(self):
        vol = voxelize_field(make_gyroid_field_fn(), (4, 4, 4), 1.0, 1.0, 1.0,
                             iso_value=0.3)
        d = vol.to_dict()
        assert d["grid_shape"] == [4, 4, 4]
        assert d["total_voxels"] == 64
        assert d["iso_value"] == 0.3

    def test_iso_value_stored(self):
        vol = voxelize_field(make_gyroid_field_fn(), (4, 4, 4),
                             1.0, 1.0, 1.0, iso_value=0.5)
        assert vol.iso_value == 0.5

    def test_zero_grid_empty(self):
        vol = voxelize_field(make_gyroid_field_fn(), (0, 0, 0), 1.0, 1.0, 1.0)
        assert vol.total_voxels == 0
        assert vol.field_values == []


# ===========================================================================
# 2) Marching Cubes Extraction
# ===========================================================================
class TestMCFullTable:

    def test_256_cases(self):
        assert len(_MC_FULL_TABLE) == 256

    def test_case_0_empty(self):
        assert _MC_FULL_TABLE[0] == []

    def test_case_255_empty(self):
        assert _MC_FULL_TABLE[255] == []

    def test_case_1_one_triangle(self):
        tris = _MC_FULL_TABLE[1]
        verts = [v for v in tris if v != -1]
        assert len(verts) == 3

    def test_symmetry(self):
        for n in [1, 2, 3, 4, 5, 10, 15]:
            a = [v for v in _MC_FULL_TABLE[n] if v != -1]
            b = [v for v in _MC_FULL_TABLE[255 - n] if v != -1]
            assert len(a) == len(b)


class TestExtractIsosurface:

    def test_sphere_produces_triangles(self):
        vol = voxelize_field(
            make_box_field_fn(), (15, 15, 15), 1.0, 1.0, 1.0,
            origin=(-7.0, -7.0, -7.0),
        )
        r = extract_isosurface(vol, zone_name="sphere_test")
        assert r["triangle_count"] > 0
        assert r["vertex_count"] > 0
        assert r["iso_extraction_success"] is True

    def test_field_above_iso_empty(self):
        vol = voxelize_field(lambda x, y, z: 10.0, (5, 5, 5), 1.0, 1.0, 1.0)
        r = extract_isosurface(vol)
        assert r["triangle_count"] == 0
        assert r["iso_extraction_success"] is False

    def test_bounding_box_computed(self):
        vol = voxelize_field(
            make_box_field_fn(), (15, 15, 15), 1.0, 1.0, 1.0,
            origin=(-7.0, -7.0, -7.0),
        )
        r = extract_isosurface(vol)
        bb = r["bounding_box"]
        assert bb["x_max"] > bb["x_min"]
        assert bb["z_max"] > bb["z_min"]

    def test_iso_passthrough(self):
        vol = voxelize_field(
            make_box_field_fn(), (11, 11, 11), 1.0, 1.0, 1.0,
            origin=(-5.0, -5.0, -5.0),
            iso_value=0.5,
        )
        r = extract_isosurface(vol)
        assert r["iso_value"] == 0.5

    def test_metadata_passthrough(self):
        vol = voxelize_field(make_box_field_fn(), (5, 5, 5), 1.0, 1.0, 1.0)
        r = extract_isosurface(vol, zone_name="heel", edition="CALM")
        assert r["zone_name"] == "heel"
        assert r["edition"] == "CALM"

    def test_grid_shape_in_result(self):
        vol = voxelize_field(make_box_field_fn(), (8, 12, 6), 1.0, 1.0, 1.0)
        r = extract_isosurface(vol)
        assert r["grid_shape"] == [8, 12, 6]

    def test_resolution_affects_triangle_count(self):
        """Finer grid should (generally) produce more triangles."""
        vol_coarse = voxelize_field(
            make_box_field_fn(), (11, 11, 11), 1.0, 1.0, 1.0,
            origin=(-5.0, -5.0, -5.0),
        )
        vol_fine = voxelize_field(
            make_box_field_fn(), (21, 21, 21), 0.5, 0.5, 0.5,
            origin=(-5.0, -5.0, -5.0),
        )
        r_coarse = extract_isosurface(vol_coarse)
        r_fine = extract_isosurface(vol_fine)
        assert r_fine["triangle_count"] >= r_coarse["triangle_count"]


# ===========================================================================
# 3) Mesh Topology Validation
# ===========================================================================
class TestValidateMeshTopology:

    def test_empty_not_manifold(self):
        r = validate_mesh_topology([], [])
        assert r.is_watertight is False
        assert r.is_manifold is False
        assert r.total_triangles == 0

    def test_single_triangle_boundary(self):
        verts = [(0, 0, 0), (1, 0, 0), (0, 1, 0)]
        tris = [(0, 1, 2)]
        r = validate_mesh_topology(verts, tris)
        assert r.is_watertight is False
        assert len(r.boundary_edges) == 3

    def test_tetrahedron_watertight(self):
        verts, tris = make_tetrahedron()
        r = validate_mesh_topology(verts, tris)
        assert r.is_watertight is True
        assert r.is_manifold is True
        assert len(r.boundary_edges) == 0
        assert len(r.non_manifold_edges) == 0

    def test_duplicate_detection(self):
        verts = [(0, 0, 0), (0, 0, 0), (1, 0, 0), (0, 1, 0)]
        tris = [(0, 2, 3), (1, 2, 3)]
        r = validate_mesh_topology(verts, tris)
        assert r.duplicate_vertices > 0

    def test_report_to_dict(self):
        verts, tris = make_tetrahedron()
        r = validate_mesh_topology(verts, tris)
        d = r.to_dict()
        assert "is_watertight" in d
        assert "is_manifold" in d
        assert "total_vertices" in d
        assert "summary" in d

    def test_summary_contains_vertex_count(self):
        verts, tris = make_tetrahedron()
        r = validate_mesh_topology(verts, tris)
        assert "4" in r.summary  # 4 vertices in tetrahedron


# ===========================================================================
# 4) Triangle Quality Analysis
# ===========================================================================
class TestTriangleQuality:

    def test_equilateral_angles(self):
        v0 = (0, 0, 0)
        v1 = (1, 0, 0)
        v2 = (0.5, math.sqrt(3) / 2, 0)
        angles = _triangle_angles(v0, v1, v2)
        for a in angles:
            assert abs(a - 60.0) < 0.1

    def test_right_angle(self):
        v0 = (0, 0, 0)
        v1 = (3, 0, 0)
        v2 = (0, 4, 0)
        angles = _triangle_angles(v0, v1, v2)
        assert any(abs(a - 90.0) < 0.1 for a in angles)

    def test_area_right_triangle(self):
        area = _triangle_area((0, 0, 0), (4, 0, 0), (0, 3, 0))
        assert abs(area - 6.0) < 0.001

    def test_edge_length(self):
        assert abs(_edge_length((0, 0, 0), (3, 4, 0)) - 5.0) < 1e-10

    def test_normal_z_up(self):
        n = _triangle_normal((0, 0, 0), (1, 0, 0), (0, 1, 0))
        assert abs(n[2] - 1.0) < 0.01

    def test_degenerate_collinear(self):
        area = _triangle_area((0, 0, 0), (1, 0, 0), (2, 0, 0))
        assert area < 1e-10


class TestAnalyzeTriangleQuality:

    def test_tetrahedron_good(self):
        verts, tris = make_tetrahedron()
        reports = analyze_triangle_quality(verts, tris, sample_size=4)
        assert len(reports) > 0
        for r in reports:
            assert r.is_degenerate is False

    def test_empty(self):
        assert analyze_triangle_quality([], []) == []

    def test_fields_present(self):
        verts = [(0, 0, 0), (1, 0, 0), (0, 1, 0)]
        tris = [(0, 1, 2)]
        reps = analyze_triangle_quality(verts, tris)
        assert len(reps) == 1
        r = reps[0]
        assert r.area_mm2 > 0
        assert r.aspect_ratio > 0
        assert 0 < r.min_angle_deg < 180
        assert len(r.normal) == 3


# ===========================================================================
# 5) Printability Estimation
# ===========================================================================
class TestEstimatePrintability:

    def test_tetrahedron_printable(self):
        verts, tris = make_tetrahedron()
        r = estimate_printability(verts, tris)
        assert r.printable is True
        assert r.score >= 0.9
        assert len(r.blockers) == 0

    def test_empty_not_printable(self):
        r = estimate_printability([], [])
        assert r.printable is False

    def test_all_check_names(self):
        verts = [(0, 0, 0), (1, 0, 0), (0, 1, 0)]
        tris = [(0, 1, 2)]
        r = estimate_printability(verts, tris)
        names = [c["name"] for c in r.checks]
        assert "manifold_integrity" in names
        assert "watertight" in names
        assert "degenerate_triangles" in names
        assert "aspect_ratio" in names
        assert "minimum_feature_size" in names
        assert "normal_consistency" in names

    def test_score_in_range(self):
        verts = [(0, 0, 0), (1, 0, 0), (0, 1, 0)]
        tris = [(0, 1, 2)]
        r = estimate_printability(verts, tris)
        assert 0.0 <= r.score <= 1.0

    def test_to_dict_complete(self):
        r = estimate_printability([], [])
        d = r.to_dict()
        assert "printable" in d
        assert "score" in d
        assert "checks" in d
        assert "warnings" in d
        assert "blockers" in d
        assert "degenerate_triangles" in d
        assert "max_aspect_ratio" in d

    def test_warnings_and_blockers_lists(self):
        r = estimate_printability([], [])
        assert isinstance(r.warnings, list)
        assert isinstance(r.blockers, list)


# ===========================================================================
# 6) Full Pipeline Integration
# ===========================================================================
class TestFullPipeline:

    def test_sphere_full_pipeline(self):
        """End-to-end: sphere voxel → mesh → validate → printability."""
        vol = voxelize_field(
            make_box_field_fn(), (15, 15, 15), 1.0, 1.0, 1.0,
            origin=(-7.0, -7.0, -7.0),
        )
        meta = extract_and_validate_mesh(
            vol,
            zone_name="sphere",
            edition="CALM",
            source_field_id="test-field-001",
        )
        assert meta.triangle_count > 0
        assert meta.vertex_count > 0
        assert meta.edition == "CALM"
        assert meta.is_hybrid is False
        assert meta.manifold_report.total_triangles == meta.triangle_count
        assert meta.printability_report.score >= 0.0

    def test_empty_volume_pipeline(self):
        vol = voxelize_field(lambda x, y, z: 10.0, (5, 5, 5), 1.0, 1.0, 1.0)
        meta = extract_and_validate_mesh(
            vol, edition="UNKNOWN", source_field_id="empty",
        )
        assert meta.triangle_count == 0
        assert meta.printability_report.printable is False

    def test_hybrid_flag(self):
        vol = voxelize_field(
            make_box_field_fn(), (15, 15, 15), 1.0, 1.0, 1.0,
            origin=(-7.0, -7.0, -7.0),
        )
        meta = extract_and_validate_mesh(
            vol, edition="HYBRID", is_hybrid=True,
            source_field_id="hyb-001",
        )
        assert meta.is_hybrid is True
        assert meta.edition == "HYBRID"

    def test_bounding_box_positive_dimensions(self):
        vol = voxelize_field(
            make_box_field_fn(), (15, 15, 15), 1.0, 1.0, 1.0,
            origin=(-7.0, -7.0, -7.0),
        )
        meta = extract_and_validate_mesh(vol, source_field_id="bb-test")
        bb = meta.bounding_box
        assert bb["x_max"] >= bb["x_min"]
        assert bb["y_max"] >= bb["y_min"]
        assert bb["z_max"] >= bb["z_min"]

    def test_surface_area_positive(self):
        vol = voxelize_field(
            make_box_field_fn(), (15, 15, 15), 1.0, 1.0, 1.0,
            origin=(-7.0, -7.0, -7.0),
        )
        meta = extract_and_validate_mesh(vol, source_field_id="sa-test")
        assert meta.surface_area_mm2 > 0

    def test_volume_positive(self):
        vol = voxelize_field(
            make_box_field_fn(), (15, 15, 15), 1.0, 1.0, 1.0,
            origin=(-7.0, -7.0, -7.0),
        )
        meta = extract_and_validate_mesh(vol, source_field_id="vol-test")
        assert meta.volume_mm3 > 0

    def test_to_dict(self):
        vol = voxelize_field(
            make_box_field_fn(), (11, 11, 11), 1.0, 1.0, 1.0,
            origin=(-5.0, -5.0, -5.0),
        )
        meta = extract_and_validate_mesh(vol, source_field_id="dict-test")
        d = meta.to_dict()
        assert "mesh_id" in d
        assert "triangle_count" in d
        assert "manifold_report" in d
        assert "printability_report" in d

    def test_to_json_valid(self):
        vol = voxelize_field(
            make_box_field_fn(), (11, 11, 11), 1.0, 1.0, 1.0,
            origin=(-5.0, -5.0, -5.0),
        )
        meta = extract_and_validate_mesh(vol, source_field_id="json-test")
        s = meta.to_json()
        parsed = json.loads(s)  # should not raise
        assert "mesh_id" in parsed

    def test_mesh_id_is_uuid(self):
        import uuid as _uuid
        vol = voxelize_field(
            make_box_field_fn(), (11, 11, 11), 1.0, 1.0, 1.0,
            origin=(-5.0, -5.0, -5.0),
        )
        meta = extract_and_validate_mesh(vol, source_field_id="uuid-test")
        _uuid.UUID(meta.mesh_id)  # raises if invalid


# ===========================================================================
# 7) Schema Validation
# ===========================================================================
class TestSchemaValidation:

    def test_valid_metadata_passes(self):
        vol = voxelize_field(
            make_box_field_fn(), (11, 11, 11), 1.0, 1.0, 1.0,
            origin=(-5.0, -5.0, -5.0),
        )
        meta = extract_and_validate_mesh(vol, source_field_id="schema-valid")
        errors = validate_mesh_metadata_against_schema(meta)
        assert errors == []

    def test_schema_file_exists(self):
        schema_path = Path("/root/hermes/zilfit-ip-core/schemas/mesh_runtime.schema.json")
        assert schema_path.exists()

    def test_schema_valid_json(self):
        schema_path = Path("/root/hermes/zilfit-ip-core/schemas/mesh_runtime.schema.json")
        with open(schema_path) as f:
            s = json.load(f)  # should not raise
        assert "$schema" in s
        assert "required" in s
        assert s["title"] == "ZILFIT Mesh Runtime Schema"

    def test_schema_has_mesh_metadata_fields(self):
        schema_path = Path("/root/hermes/zilfit-ip-core/schemas/mesh_runtime.schema.json")
        with open(schema_path) as f:
            s = json.load(f)
        req = s["required"]
        assert "mesh_id" in req
        assert "triangle_count" in req
        assert "manifold_report" in req
        assert "printability_report" in req

    def test_printability_score_constrained(self):
        """Printability score must be between 0 and 1."""
        vol = voxelize_field(
            make_box_field_fn(), (15, 15, 15), 1.0, 1.0, 1.0,
            origin=(-7.0, -7.0, -7.0),
        )
        meta = extract_and_validate_mesh(vol, source_field_id="score-test")
        pr = meta.printability_report
        assert 0.0 <= pr.score <= 1.0

    def test_quality_summary_structure(self):
        vol = voxelize_field(
            make_box_field_fn(), (15, 15, 15), 1.0, 1.0, 1.0,
            origin=(-7.0, -7.0, -7.0),
        )
        meta = extract_and_validate_mesh(vol, source_field_id="qc-test")
        qs = meta.quality_summary
        assert "total_triangles_analyzed" in qs
        assert "min_area_mm2" in qs
        assert "max_area_mm2" in qs
        assert "avg_area_mm2" in qs
        assert "max_aspect_ratio" in qs

    def test_manifold_report_required_fields(self):
        vol = voxelize_field(
            make_box_field_fn(), (11, 11, 11), 1.0, 1.0, 1.0,
            origin=(-5.0, -5.0, -5.0),
        )
        meta = extract_and_validate_mesh(vol, source_field_id="mr-test")
        mr = meta.manifold_report
        assert hasattr(mr, "is_watertight")
        assert hasattr(mr, "is_manifold")
        assert hasattr(mr, "total_vertices")
        assert hasattr(mr, "total_triangles")


# ===========================================================================
# 8) Engineering Constraints
# ===========================================================================
class TestEngineeringConstraints:

    def test_wall_thickness_constant(self):
        assert MIN_WALL_THICKNESS_MM == 0.6

    def test_density_range(self):
        assert DENSITY_MIN == 0.15
        assert DENSITY_MAX == 0.45
        assert DENSITY_MIN < DENSITY_MAX

    def test_cell_size_range(self):
        assert GYROID_CELL_SIZE_MIN_MM == 5.0
        assert GYROID_CELL_SIZE_MAX_MM == 7.0
        assert GYROID_CELL_SIZE_MIN_MM < GYROID_CELL_SIZE_MAX_MM

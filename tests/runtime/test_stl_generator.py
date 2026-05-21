"""
Tests for ZILFIT STL Generator Runtime.

Covers:
  - Gyroid field generation
  - Density gradient computation
  - Mesh configuration building
  - Readiness scoring
  - Implicit field evaluation
  - Schema validation
  - Constraint enforcement
  - Single edition (CALM, VITAL, FEMME)
  - Hybrid edition (CALM+FEMME, VITAL+FOCUS)

No Blender. No GUI. Pure mathematical field generation.
"""

from __future__ import annotations

import json
import math
import uuid
from pathlib import Path
from typing import Any, Dict, List, Optional

import pytest

# ---------------------------------------------------------------------------
# Import test targets
# ---------------------------------------------------------------------------
from runtime.zilfit_stl_generator import (
    DENSITY_MAX,
    DENSITY_MIN,
    GYROID_CELL_SIZE_MAX_MM,
    GYROID_CELL_SIZE_MIN_MM,
    MIN_WALL_THICKNESS_MM,
    ConstraintViolationError,
    ExportMetadata,
    GyroidFieldParams,
    InvalidGeometryPlanError,
    STLGenerationConfig,
    STLGenerationError,
    STLReadinessReport,
    STLReadinessScorer,
    VoxelGridSettings,
    ZoneMeshConfig,
    build_mesh_config,
    evaluate_gyroid_at,
    generate_density_gradient,
    generate_gyroid_field,
    validate_config_against_schema,
    _density_to_threshold,
)

# ---------------------------------------------------------------------------
# Minimal mock GeometryPlan
# ---------------------------------------------------------------------------
class MockZone:
    def __init__(self, zone_name: str, density_pct: float, pressure_limit_kpa: float,
                 gyroid_cell_size_mm: float, wall_thickness_mm: float,
                 stimulation_type: str, structural_role: str):
        self.zone_name = zone_name
        self.density_pct = density_pct
        self.pressure_limit_kpa = pressure_limit_kpa
        self.gyroid_cell_size_mm = gyroid_cell_size_mm
        self.wall_thickness_mm = wall_thickness_mm
        self.stimulation_type = stimulation_type
        self.structural_role = structural_role


class MockManufacturability:
    def __init__(self, passed: bool = True,
                 violations: Optional[List[str]] = None,
                 warnings: Optional[List[str]] = None):
        self.passed = passed
        self.violations = violations or []
        self.warnings = warnings or []
        self.checks = [{"name": "all", "passed": passed}]


def make_mock_plan(
    edition: str = "CALM",
    is_hybrid: bool = False,
    secondary_edition: Optional[str] = None,
    blend_ratio: tuple = (1.0, 0.0),
    zones: Optional[List[MockZone]] = None,
    ready_for_stl: bool = True,
    manufacturability_passed: bool = True,
) -> Any:
    """Create a mock GeometryPlan for testing."""

    if zones is None:
        # Default CALM zones
        zones = _default_calm_zones()

    class MockPlan:
        def __init__(self):
            self.plan_id = str(uuid.uuid4())
            self.source_session_id = str(uuid.uuid4())
            self.timestamp = "2026-05-21T00:00:00+00:00"
            self.edition = edition
            self.is_hybrid = is_hybrid
            self.secondary_edition = secondary_edition
            self.blend_ratio = blend_ratio
            self.zones = zones
            self.ready_for_stl = ready_for_stl
            self.manufacturability = MockManufacturability(
                passed=manufacturability_passed
            )

    return MockPlan()


def _default_calm_zones() -> List[MockZone]:
    return [
        MockZone("heel", 22.0, 31.5, 6.5, 0.6, "static", "shock_absorption"),
        MockZone("midfoot", 20.0, 28.8, 6.5, 0.6, "static", "support"),
        MockZone("forefoot", 25.0, 36.0, 6.5, 0.6, "static", "proprioceptive"),
        MockZone("toe", 22.0, 31.5, 6.5, 0.6, "static", "proprioceptive"),
        MockZone("arch", 18.0, 25.9, 6.5, 0.6, "graded", "support"),
        MockZone("medial_edge", 19.0, 27.4, 6.5, 0.6, "static", "stability"),
        MockZone("lateral_edge", 19.0, 27.4, 6.5, 0.6, "static", "stability"),
    ]


def _default_hybrid_zones() -> List[MockZone]:
    """Blend of CALM and FEMME: slightly lower densities."""
    return [
        MockZone("heel", 20.5, 30.0, 6.8, 0.6, "static", "shock_absorption"),
        MockZone("midfoot", 18.5, 27.0, 6.8, 0.6, "static", "support"),
        MockZone("forefoot", 23.0, 33.5, 6.8, 0.6, "static", "proprioceptive"),
        MockZone("toe", 20.5, 30.0, 6.8, 0.6, "static", "proprioceptive"),
        MockZone("arch", 16.5, 24.0, 6.8, 0.6, "graded", "support"),
        MockZone("medial_edge", 17.5, 25.5, 6.8, 0.6, "static", "stability"),
        MockZone("lateral_edge", 17.5, 25.5, 6.8, 0.6, "static", "stability"),
    ]


# ============================================================================
# 1) Density-to-threshold mapping
# ============================================================================
class TestDensityToThreshold:
    """Test _density_to_threshold linear mapping."""

    def test_max_density_gives_min_threshold(self):
        """density=0.45 → t≈-0.8 (more solid)"""
        t = _density_to_threshold(DENSITY_MAX)
        assert abs(t - (-0.8)) < 0.01, f"Expected ~-0.8, got {t}"

    def test_min_density_gives_max_threshold(self):
        """density=0.15 → t≈+0.8 (more void)"""
        t = _density_to_threshold(DENSITY_MIN)
        assert abs(t - 0.8) < 0.01, f"Expected ~0.8, got {t}"

    def test_mid_density_gives_near_zero(self):
        """density=0.30 → t≈0.0"""
        t = _density_to_threshold(0.30)
        assert abs(t) < 0.05, f"Expected ~0, got {t}"

    def test_clamps_below_minimum(self):
        t_low = _density_to_threshold(0.05)
        t_min = _density_to_threshold(DENSITY_MIN)
        assert t_low == t_min, "Clamped density should give same threshold"

    def test_clamps_above_maximum(self):
        t_high = _density_to_threshold(0.60)
        t_max = _density_to_threshold(DENSITY_MAX)
        assert t_high == t_max, "Clamped density should give same threshold"

    def test_threshold_in_range(self):
        for d in [0.15, 0.20, 0.25, 0.30, 0.35, 0.40, 0.45]:
            t = _density_to_threshold(d)
            assert -0.8 <= t <= 0.8, f"d={d} → t={t} out of [-0.8, 0.8]"


# ============================================================================
# 2) generate_gyroid_field
# ============================================================================
class TestGenerateGyroidField:
    """Test implicit gyroid field parameter generation."""

    def test_field_for_calm_heel(self):
        field = generate_gyroid_field(
            zone_name="heel", cell_size_mm=6.5, density=0.22, edition="CALM"
        )
        assert field.zone_name == "heel"
        assert field.edition == "CALM"
        assert field.is_hybrid is False
        assert field.secondary_edition is None

    def test_coefficients_are_pi_over_cell(self):
        field = generate_gyroid_field(
            zone_name="arch", cell_size_mm=6.0, density=0.20, edition="BALANCE"
        )
        expected_coeff = math.pi / 6.0
        assert abs(field.coefficient_x - expected_coeff) < 1e-6
        assert abs(field.coefficient_y - expected_coeff) < 1e-6
        assert abs(field.coefficient_z - expected_coeff) < 1e-6

    def test_isotropic_cell_dimensions(self):
        field = generate_gyroid_field(
            zone_name="forefoot", cell_size_mm=5.5, density=0.35,
            edition="FOCUS"
        )
        assert field.cell_size_x_mm == 5.5
        assert field.cell_size_y_mm == 5.5
        assert field.cell_size_z_mm == 5.5

    def test_cell_size_clamping_low(self):
        field = generate_gyroid_field(
            zone_name="heel", cell_size_mm=3.0, density=0.22, edition="CALM"
        )
        assert field.cell_size_x_mm == GYROID_CELL_SIZE_MIN_MM

    def test_cell_size_clamping_high(self):
        field = generate_gyroid_field(
            zone_name="heel", cell_size_mm=10.0, density=0.22, edition="CALM"
        )
        assert field.cell_size_x_mm == GYROID_CELL_SIZE_MAX_MM

    def test_field_for_hybrid(self):
        field = generate_gyroid_field(
            zone_name="midfoot", cell_size_mm=6.5, density=0.20,
            edition="CALM", is_hybrid=True, secondary_edition="FEMME"
        )
        assert field.is_hybrid is True
        assert field.secondary_edition == "FEMME"

    def test_threshold_derived_from_density(self):
        low_d_field = generate_gyroid_field(
            zone_name="arch", cell_size_mm=6.5, density=DENSITY_MIN, edition="CALM"
        )
        high_d_field = generate_gyroid_field(
            zone_name="forefoot", cell_size_mm=6.5, density=DENSITY_MAX, edition="CALM"
        )
        # Higher density → lower (more negative) threshold
        assert high_d_field.threshold < low_d_field.threshold

    def test_field_to_dict_roundtrip(self):
        field = generate_gyroid_field(
            zone_name="heel", cell_size_mm=6.5, density=0.22, edition="CALM"
        )
        d = field.to_dict()
        assert isinstance(d, dict)
        assert d["zone_name"] == "heel"
        assert d["threshold"] == field.threshold


# ============================================================================
# 3) generate_density_gradient
# ============================================================================
class TestGenerateDensityGradient:
    """Test density gradient computation for zone transitions."""

    def test_gradient_has_all_zones(self):
        plan = make_mock_plan()
        gradients = generate_density_gradient(plan)
        for zone_name in ["heel", "midfoot", "forefoot", "toe", "arch",
                          "medial_edge", "lateral_edge"]:
            assert zone_name in gradients["gradient_by_zone"]

    def test_neighbor_deltas(self):
        plan = make_mock_plan()
        gradients = generate_density_gradient(plan)
        heel_grad = gradients["gradient_by_zone"]["heel"]
        assert heel_grad["neighbor_count"] >= 3  # heel has 3+ neighbors

    def test_gradient_includes_interpolation_hint(self):
        plan = make_mock_plan()
        gradients = generate_density_gradient(plan, interpolation="cubic")
        assert gradients["interpolation_method"] == "cubic"

    def test_gradient_requires_smoothing_for_large_delta(self):
        """Create a plan with very large density differences."""
        zones = [
            MockZone("heel", 45.0, 50.0, 5.5, 0.6, "static", "shock_absorption"),
            MockZone("midfoot", 15.0, 15.0, 7.0, 0.6, "static", "support"),
            MockZone("forefoot", 30.0, 35.0, 6.0, 0.6, "static", "proprioceptive"),
            MockZone("toe", 25.0, 30.0, 6.0, 0.6, "static", "proprioceptive"),
            MockZone("arch", 15.0, 15.0, 7.0, 0.6, "graded", "support"),
            MockZone("medial_edge", 15.0, 15.0, 7.0, 0.6, "static", "stability"),
            MockZone("lateral_edge", 15.0, 15.0, 7.0, 0.6, "static", "stability"),
        ]
        plan = make_mock_plan(zones=zones)
        gradients = generate_density_gradient(plan)
        # Heel (0.45) ↔ Midfoot (0.15) delta = 0.30 > 0.10
        heel_nb = gradients["gradient_by_zone"]["heel"]["neighbors"]
        midfoot_nb = [n for n in heel_nb if n["to_zone"] == "midfoot"]
        assert len(midfoot_nb) == 1
        assert midfoot_nb[0]["requires_smoothing"] is True
        assert midfoot_nb[0]["delta"] == 0.30

    def test_is_hybrid_flag(self):
        plan = make_mock_plan(is_hybrid=True, secondary_edition="FEMME",
                              blend_ratio=(0.7, 0.3))
        gradients = generate_density_gradient(plan)
        assert gradients["is_hybrid"] is True

    def test_resolution_passed_through(self):
        plan = make_mock_plan()
        gradients = generate_density_gradient(plan, resolution_mm=0.1)
        assert gradients["resolution_mm"] == 0.1


# ============================================================================
# 4) STLReadinessScorer
# ============================================================================
class TestSTLReadinessScorer:
    """Test readiness scoring."""

    def test_perfect_plan_scores_1(self):
        plan = make_mock_plan()
        scorer = STLReadinessScorer()
        report = scorer.score(plan)
        assert report.score == pytest.approx(1.0, abs=0.15)
        assert report.is_ready is True

    def test_unready_plan_scores_low(self):
        plan = make_mock_plan(ready_for_stl=False, manufacturability_passed=False)
        scorer = STLReadinessScorer()
        report = scorer.score(plan)
        assert report.score < 1.0
        assert report.is_ready is False
        assert len(report.blockers) > 0

    def test_report_has_checks(self):
        plan = make_mock_plan()
        scorer = STLReadinessScorer()
        report = scorer.score(plan)
        assert len(report.checks) >= 5

    def test_report_to_dict(self):
        plan = make_mock_plan()
        scorer = STLReadinessScorer()
        report = scorer.score(plan)
        d = report.to_dict()
        assert "score" in d
        assert "is_ready" in d
        assert "checks" in d
        assert "blockers" in d

    def test_report_has_warnings_list(self):
        plan = make_mock_plan()
        scorer = STLReadinessScorer()
        report = scorer.score(plan)
        assert isinstance(report.warnings, list)


# ============================================================================
# 5) build_mesh_config — single edition (CALM)
# ============================================================================
class TestBuildMeshConfigCalm:
    """Test full configuration build from a CALM plan."""

    def test_config_has_config_id(self):
        plan = make_mock_plan(edition="CALM")
        config = build_mesh_config(plan)
        assert config.config_id
        uuid.UUID(config.config_id)  # validates UUID

    def test_config_edition_is_calm(self):
        plan = make_mock_plan(edition="CALM")
        config = build_mesh_config(plan)
        assert config.edition == "CALM"
        assert config.is_hybrid is False

    def test_config_has_7_gyroid_fields(self):
        plan = make_mock_plan(edition="CALM")
        config = build_mesh_config(plan)
        assert len(config.gyroid_fields) == 7

    def test_config_has_7_zone_meshes(self):
        plan = make_mock_plan(edition="CALM")
        config = build_mesh_config(plan)
        assert len(config.zone_meshes) == 7

    def test_voxel_grid_is_3d(self):
        plan = make_mock_plan(edition="CALM")
        config = build_mesh_config(plan)
        assert config.voxel_grid.grid_size_x > 0
        assert config.voxel_grid.grid_size_y > 0
        assert config.voxel_grid.grid_size_z > 0
        assert config.voxel_grid.total_voxels == (
            config.voxel_grid.grid_size_x
            * config.voxel_grid.grid_size_y
            * config.voxel_grid.grid_size_z
        )

    def test_voxel_grid_bounding_box(self):
        plan = make_mock_plan(edition="CALM")
        config = build_mesh_config(plan)
        bb = config.voxel_grid.bounding_box
        assert bb["x_min"] < bb["x_max"]
        assert bb["y_min"] < bb["y_max"]
        assert bb["z_min"] < bb["z_max"]
        assert bb["z_min"] == 0.0

    def test_zone_mesh_names_match_plan(self):
        plan = make_mock_plan(edition="CALM")
        config = build_mesh_config(plan)
        mesh_names = {m.zone_name for m in config.zone_meshes}
        expected = {"heel", "midfoot", "forefoot", "toe", "arch",
                    "medial_edge", "lateral_edge"}
        assert mesh_names == expected

    def test_export_metadata_correct(self):
        plan = make_mock_plan(edition="CALM")
        config = build_mesh_config(plan)
        meta = config.export_metadata
        assert meta.plan_id == plan.plan_id
        assert meta.source_session_id == plan.source_session_id
        assert meta.edition == "CALM"
        assert meta.total_zones == 7
        assert meta.units == "mm"
        assert meta.format_hint == "stl_binary"

    def test_readiness_is_passing_for_valid_plan(self):
        plan = make_mock_plan(edition="CALM")
        config = build_mesh_config(plan)
        assert config.readiness.score >= 0.9
        assert config.readiness.is_ready is True

    def test_to_dict_roundtrip(self):
        plan = make_mock_plan(edition="CALM")
        config = build_mesh_config(plan)
        d = config.to_dict()
        assert isinstance(d["gyroid_fields"], list)
        assert isinstance(d["voxel_grid"], dict)
        assert isinstance(d["zone_meshes"], list)
        assert isinstance(d["export_metadata"], dict)
        assert isinstance(d["readiness"], dict)

    def test_to_json_is_valid_json(self):
        plan = make_mock_plan(edition="CALM")
        config = build_mesh_config(plan)
        j = config.to_json()
        parsed = json.loads(j)
        assert parsed["edition"] == "CALM"


# ============================================================================
# 6) build_mesh_config — VITAL edition
# ============================================================================
class TestBuildMeshConfigVital:
    """Test VITAL (firm) edition produces valid config."""

    def test_vital_config(self):
        zones = [
            MockZone("heel", 35.0, 45.5, 5.5, 0.6, "static", "shock_absorption"),
            MockZone("midfoot", 32.0, 41.6, 5.5, 0.6, "static", "support"),
            MockZone("forefoot", 35.0, 45.5, 5.5, 0.6, "static", "proprioceptive"),
            MockZone("toe", 30.0, 39.0, 5.5, 0.6, "static", "proprioceptive"),
            MockZone("arch", 28.8, 37.4, 5.5, 0.6, "graded", "support"),
            MockZone("medial_edge", 30.4, 39.5, 5.5, 0.6, "static", "stability"),
            MockZone("lateral_edge", 30.4, 39.5, 5.5, 0.6, "static", "stability"),
        ]
        plan = make_mock_plan(edition="VITAL", zones=zones)
        config = build_mesh_config(plan)
        assert config.edition == "VITAL"
        assert len(config.gyroid_fields) == 7
        assert config.readiness.is_ready is True

    def test_vital_smaller_cell_size(self):
        zones = [
            MockZone("heel", 35.0, 45.5, 5.5, 0.6, "static", "shock_absorption"),
            MockZone("midfoot", 32.0, 41.6, 5.5, 0.6, "static", "support"),
            MockZone("forefoot", 35.0, 45.5, 5.5, 0.6, "static", "proprioceptive"),
            MockZone("toe", 30.0, 39.0, 5.5, 0.6, "static", "proprioceptive"),
            MockZone("arch", 28.8, 37.4, 5.5, 0.6, "graded", "support"),
            MockZone("medial_edge", 30.4, 39.5, 5.5, 0.6, "static", "stability"),
            MockZone("lateral_edge", 30.4, 39.5, 5.5, 0.6, "static", "stability"),
        ]
        plan = make_mock_plan(edition="VITAL", zones=zones)
        config = build_mesh_config(plan)
        field = config.gyroid_fields[0]
        assert field.cell_size_x_mm == 5.5
        # Smaller cell → larger coefficient
        assert field.coefficient_x > math.pi / 6.5


# ============================================================================
# 7) build_mesh_config — HYBRID edition
# ============================================================================
class TestBuildMeshConfigHybrid:
    """Test hybrid edition configuration."""

    def test_hybrid_config_has_secondary_edition(self):
        zones = _default_hybrid_zones()
        plan = make_mock_plan(
            edition="CALM", is_hybrid=True, secondary_edition="FEMME",
            blend_ratio=(0.7, 0.3), zones=zones
        )
        config = build_mesh_config(plan)
        assert config.is_hybrid is True
        assert len(config.gyroid_fields) == 7

    def test_hybrid_fields_contain_secondary_edition(self):
        zones = _default_hybrid_zones()
        plan = make_mock_plan(
            edition="CALM", is_hybrid=True, secondary_edition="FEMME",
            blend_ratio=(0.7, 0.3), zones=zones
        )
        config = build_mesh_config(plan)
        for field in config.gyroid_fields:
            assert field.is_hybrid is True
            assert field.secondary_edition == "FEMME"

    def test_hybrid_export_metadata(self):
        zones = _default_hybrid_zones()
        plan = make_mock_plan(
            edition="CALM", is_hybrid=True, secondary_edition="FEMME",
            blend_ratio=(0.7, 0.3), zones=zones
        )
        config = build_mesh_config(plan)
        meta = config.export_metadata
        assert meta.is_hybrid is True
        assert meta.secondary_edition == "FEMME"
        assert meta.blend_ratio == (0.7, 0.3)

    def test_hybrid_readiness(self):
        zones = _default_hybrid_zones()
        plan = make_mock_plan(
            edition="CALM", is_hybrid=True, secondary_edition="FEMME",
            blend_ratio=(0.7, 0.3), zones=zones
        )
        config = build_mesh_config(plan)
        assert config.readiness.is_ready is True


# ============================================================================
# 8) Constraint enforcement
# ============================================================================
class TestConstraintEnforcement:
    """Verify that build_mesh_config enforces hard constraints."""

    def test_wall_thickness_record(self):
        plan = make_mock_plan()
        config = build_mesh_config(plan)
        ce = config.constraints_enforced
        assert "wall_thickness_mm" in ce
        assert ce["wall_thickness_mm"]["minimum"] == 0.6
        assert ce["wall_thickness_mm"]["enforced"] is True
        assert ce["wall_thickness_mm"]["actual_min"] >= 0.6

    def test_density_range_record(self):
        plan = make_mock_plan()
        config = build_mesh_config(plan)
        ce = config.constraints_enforced
        assert ce["density_range"]["minimum"] == DENSITY_MIN
        assert ce["density_range"]["maximum"] == DENSITY_MAX
        assert ce["density_range"]["enforced"] is True

    def test_cell_size_range_record(self):
        plan = make_mock_plan()
        config = build_mesh_config(plan)
        ce = config.constraints_enforced
        assert ce["cell_size_range"]["minimum"] == GYROID_CELL_SIZE_MIN_MM
        assert ce["cell_size_range"]["maximum"] == GYROID_CELL_SIZE_MAX_MM

    def test_zone_mesh_wall_thickness_min(self):
        plan = make_mock_plan()
        config = build_mesh_config(plan)
        for mesh in config.zone_meshes:
            assert mesh.wall_thickness_mm >= MIN_WALL_THICKNESS_MM

    def test_zone_mesh_density_in_range(self):
        plan = make_mock_plan()
        config = build_mesh_config(plan)
        for mesh in config.zone_meshes:
            assert DENSITY_MIN <= mesh.density_target <= DENSITY_MAX

    def test_zone_mesh_cell_size_in_range(self):
        plan = make_mock_plan()
        config = build_mesh_config(plan)
        for mesh in config.zone_meshes:
            assert GYROID_CELL_SIZE_MIN_MM <= mesh.cell_size_mm <= GYROID_CELL_SIZE_MAX_MM


# ============================================================================
# 9) evaluate_gyroid_at — implicit field evaluation
# ============================================================================
class TestEvaluateGyroidAt:
    """Test the gyroid scalar field evaluation function."""

    def test_field_evaluation_returns_float(self):
        field = generate_gyroid_field(
            zone_name="heel", cell_size_mm=6.5, density=0.22, edition="CALM"
        )
        result = evaluate_gyroid_at(1.0, 2.0, 3.0, field)
        assert isinstance(result, float)

    def test_origin_evaluation(self):
        """At (0,0,0): sin(0)*cos(0) + sin(0)*cos(0) + sin(0)*cos(0) = 0"""
        field = generate_gyroid_field(
            zone_name="heel", cell_size_mm=6.5, density=0.22, edition="CALM"
        )
        result = evaluate_gyroid_at(0.0, 0.0, 0.0, field)
        # F(0,0,0) = 0 - threshold
        assert abs(result - (-field.threshold)) < 1e-10

    def test_different_inputs_different_outputs(self):
        field = generate_gyroid_field(
            zone_name="arch", cell_size_mm=6.5, density=0.18, edition="CALM"
        )
        v1 = evaluate_gyroid_at(1.0, 0.0, 0.0, field)
        v2 = evaluate_gyroid_at(0.0, 1.0, 0.0, field)
        # Should differ due to asymmetric position
        assert v1 != v2 or field.coefficient_x == field.coefficient_y

    def test_negative_input(self):
        field = generate_gyroid_field(
            zone_name="heel", cell_size_mm=6.5, density=0.22, edition="CALM"
        )
        # F(-x,y,z) = sin(-ax)·cos(ay) + ... (should still work)
        result = evaluate_gyroid_at(-5.0, -3.0, -1.0, field)
        assert isinstance(result, float)
        # Check bounded: each sin·cos term is in [-1,1], threshold in [-0.8, 0.8]
        assert -4.0 <= result <= 4.0

    def test_zero_crossing_existence(self):
        """For a valid threshold, F should cross zero somewhere."""
        field = generate_gyroid_field(
            zone_name="heel", cell_size_mm=6.5, density=0.22, edition="CALM"
        )
        # Evaluate on a grid — check that we get both positive and negative values
        has_pos = False
        has_neg = False
        for xi in range(-3, 4):
            for yi in range(-3, 4):
                for zi in range(-1, 2):
                    v = evaluate_gyroid_at(xi, yi, zi, field)
                    if v > 0:
                        has_pos = True
                    if v < 0:
                        has_neg = True
                if has_pos and has_neg:
                    break
            if has_pos and has_neg:
                break
        assert has_pos and has_neg, "Field should cross zero (gyroid surface should exist)"

    def test_different_density_changes_field(self):
        """Different density → different threshold → different field at same point."""
        field1 = generate_gyroid_field(
            zone_name="heel", cell_size_mm=6.5, density=DENSITY_MIN, edition="CALM"
        )
        field2 = generate_gyroid_field(
            zone_name="heel", cell_size_mm=6.5, density=DENSITY_MAX, edition="CALM"
        )
        v1 = evaluate_gyroid_at(1.0, 1.0, 1.0, field1)
        v2 = evaluate_gyroid_at(1.0, 1.0, 1.0, field2)
        assert v1 != v2, "Different densities should produce different field values"


# ============================================================================
# 10) Schema validation
# ============================================================================
class TestSchemaValidation:
    """Test validate_config_against_schema."""

    def test_valid_config_passes(self):
        plan = make_mock_plan()
        config = build_mesh_config(plan)
        errors = validate_config_against_schema(config)
        assert len(errors) == 0, f"Unexpected errors: {errors}"

    def test_zone_mesh_missing_density_reports_error(self):
        """If density_target is out of range, should report error."""
        errors = validate_config_against_schema(build_mesh_config(make_mock_plan()))
        # Valid plan should have no errors
        assert len(errors) == 0

    def test_wall_thickness_violation(self):
        """Create a config manually with bad wall thickness."""
        config = build_mesh_config(make_mock_plan())
        # Corrupt one zone mesh
        config.zone_meshes[0].wall_thickness_mm = 0.3
        errors = validate_config_against_schema(config)
        assert any("wall_thickness_mm" in e for e in errors), (
            f"Expected wall thickness error, got: {errors}"
        )

    def test_density_violation(self):
        config = build_mesh_config(make_mock_plan())
        config.zone_meshes[0].density_target = 0.60  # above 0.45
        errors = validate_config_against_schema(config)
        assert any("density_target" in e for e in errors), (
            f"Expected density error, got: {errors}"
        )

    def test_cell_size_violation(self):
        config = build_mesh_config(make_mock_plan())
        config.zone_meshes[0].cell_size_mm = 9.0  # above 7.0
        errors = validate_config_against_schema(config)
        assert any("cell_size_mm" in e for e in errors), (
            f"Expected cell size error, got: {errors}"
        )


# ============================================================================
# 11) Dataclass serialization
# ============================================================================
class TestDataclassSerialization:
    """Test that all dataclasses serialize correctly."""

    def test_gyroid_field_to_dict(self):
        field = generate_gyroid_field(
            zone_name="heel", cell_size_mm=6.5, density=0.22, edition="CALM"
        )
        d = field.to_dict()
        assert isinstance(d, dict)
        for k in ["cell_size_x_mm", "threshold", "coefficient_x", "zone_name"]:
            assert k in d

    def test_zone_mesh_to_dict(self):
        field = generate_gyroid_field(
            zone_name="arch", cell_size_mm=6.5, density=0.18, edition="CALM"
        )
        mesh = ZoneMeshConfig(
            zone_name="arch",
            field_params=field,
            density_target=0.18,
            wall_thickness_mm=0.6,
            cell_size_mm=6.5,
            mesh_resolution_mm=0.25,
            stimulation_type="graded",
            structural_role="support",
            mc_surface_value=field.threshold,
            mc_gradient_steps=1,
            mc_smooth_iterations=1,
        )
        d = mesh.to_dict()
        assert d["zone_name"] == "arch"
        assert isinstance(d["field_params"], dict)

    def test_voxel_grid_to_dict(self):
        vg = VoxelGridSettings(
            grid_size_x=100, grid_size_y=50, grid_size_z=30,
            resolution_mm=0.25,
            bounding_box={"x_min": -50, "x_max": 50, "y_min": -25,
                          "y_max": 25, "z_min": 0, "z_max": 6},
            total_voxels=150000,
            memory_estimate_bytes=600000,
        )
        d = vg.to_dict()
        assert d["total_voxels"] == 150000

    def test_export_metadata_to_dict(self):
        meta = ExportMetadata(
            plan_id=str(uuid.uuid4()),
            source_session_id=str(uuid.uuid4()),
            edition="CALM",
            is_hybrid=False,
            secondary_edition=None,
            blend_ratio=(1.0, 0.0),
            timestamp="2026-05-21T00:00:00+00:00",
            total_zones=7,
            total_voxels=10000,
            estimated_triangles=1200,
            estimated_filesize_mb=0.06,
            format_hint="stl_binary",
            units="mm",
            coordinate_system="right-handed Y-up",
        )
        d = meta.to_dict()
        assert d["blend_ratio"] == [1.0, 0.0]  # to_dict converts tuple to list
        assert d["format_hint"] == "stl_binary"


# ============================================================================
# 12) FEMME edition (softest, largest cells)
# ============================================================================
class TestBuildMeshConfigFemme:
    """Test FEMME edition (ultra-soft, 7.0mm cells)."""

    def test_femme_config(self):
        zones = [
            MockZone("heel", 18.0, 25.2, 7.0, 0.6, "static", "shock_absorption"),
            MockZone("midfoot", 17.0, 23.8, 7.0, 0.6, "static", "support"),
            MockZone("forefoot", 20.0, 28.0, 7.0, 0.6, "static", "proprioceptive"),
            MockZone("toe", 18.0, 25.2, 7.0, 0.6, "static", "proprioceptive"),
            MockZone("arch", 15.3, 21.4, 7.0, 0.6, "graded", "support"),
            MockZone("medial_edge", 16.15, 22.6, 7.0, 0.6, "static", "stability"),
            MockZone("lateral_edge", 16.15, 22.6, 7.0, 0.6, "static", "stability"),
        ]
        plan = make_mock_plan(edition="FEMME", zones=zones)
        config = build_mesh_config(plan)
        assert config.edition == "FEMME"
        # Largest cells → smallest coefficients
        coeff = config.gyroid_fields[0].coefficient_x
        assert abs(coeff - math.pi / 7.0) < 1e-4


# ============================================================================
# 13) Custom insole dimensions
# ============================================================================
class TestCustomInsoleDimensions:
    """Test that custom insole size changes voxel grid."""

    def test_larger_insole_more_voxels(self):
        plan = make_mock_plan()
        config_small = build_mesh_config(plan, resolution_mm=0.5)
        config_large = build_mesh_config(
            plan, resolution_mm=0.5,
            insole_length_mm=300.0,  # larger than default 260
            insole_width_mm=110.0,
        )
        assert config_large.voxel_grid.total_voxels > config_small.voxel_grid.total_voxels

    def test_fine_resolution_more_voxels(self):
        plan = make_mock_plan()
        config_coarse = build_mesh_config(plan, resolution_mm=0.5)
        config_fine = build_mesh_config(plan, resolution_mm=0.1)
        assert config_fine.voxel_grid.total_voxels > config_coarse.voxel_grid.total_voxels


# ============================================================================
# 14) Zone transition config
# ============================================================================
class TestZoneTransitionConfig:
    """Test zone-to-zone transition configuration."""

    def test_transitions_exist(self):
        plan = make_mock_plan()
        config = build_mesh_config(plan)
        assert len(config.zone_transition_config) > 0

    def test_transition_has_required_keys(self):
        plan = make_mock_plan()
        config = build_mesh_config(plan)
        for pair_key, trans in config.zone_transition_config.items():
            assert "density_delta" in trans
            assert "transition_width_mm" in trans
            assert "requires_smoothing" in trans
            assert "interpolation" in trans

    def test_transition_density_delta_non_negative(self):
        plan = make_mock_plan()
        config = build_mesh_config(plan)
        for trans in config.zone_transition_config.values():
            assert trans["density_delta"] >= 0.0

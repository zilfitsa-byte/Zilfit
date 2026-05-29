"""Tests for ZILFIT P01 BALANCE Export Builder.

Covers:
  - export validity (all 3 artifacts produced)
  - transition validation (sigmoid, no step, delta cap)
  - shrinkage compensation (1.5%)
  - shell thickness enforcement (0.8 mm)
  - MJF-only compatibility
  - density floor/ceiling enforcement
"""

import json
import os
import sys
import tempfile
from pathlib import Path

PROJ_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(PROJ_ROOT / "runtime"))
sys.path.insert(0, str(PROJ_ROOT))

from zilfit_p01_balance_export import (
    EXPORT_ADJACENT_DELTA,
    EXPORT_DENSITY_CEILING,
    EXPORT_DENSITY_FLOOR,
    EXPORT_MANUFACTURING,
    EXPORT_SHELL_THICKNESS,
    EXPORT_SHRINKAGE_PCT,
    build_balance_export_plan,
    build_sigmoid_transitions,
    export_all,
    export_balance_plan,
    export_mesh_config,
    export_print_sheet,
    validate_adjacent_delta,
    validate_density,
    validate_mjf_compatibility,
    validate_no_hard_edges,
    validate_shell_thickness,
)


# ─── Artifact export validity ────────────────────────────────────────

def test_export_three_artifacts():
    with tempfile.TemporaryDirectory() as td:
        paths = export_all(output_dir=td)
        assert "balance_plan.json" in paths
        assert "balance_mesh_config.json" in paths
        assert "balance_print_sheet.md" in paths
        for name, p in paths.items():
            assert os.path.exists(p), f"{name} not created at {p}"


def test_export_plan_is_valid_json():
    with tempfile.TemporaryDirectory() as td:
        paths = export_all(output_dir=td)
        with open(paths["balance_plan.json"]) as f:
            data = json.load(f)
        assert data["edition"] == "BALANCE"
        assert "density_by_zone" in data
        assert "ready_for_print" in data
        assert "ready_for_stl" in data


def test_export_ready_for_print_true():
    plan = build_balance_export_plan()
    assert plan["ready_for_print"] is True


def test_export_ready_for_stl_true():
    plan = build_balance_export_plan()
    assert plan["ready_for_stl"] is True


# ─── Density floor / ceiling enforcement ─────────────────────────────

def test_density_floor_is_018():
    assert EXPORT_DENSITY_FLOOR == 0.18


def test_density_ceiling_is_045():
    assert EXPORT_DENSITY_CEILING == 0.45


def test_balance_densities_within_export_range():
    plan = build_balance_export_plan()
    for z, d in plan["density_by_zone"].items():
        assert EXPORT_DENSITY_FLOOR <= d <= EXPORT_DENSITY_CEILING, f"{z}={d} out of range"


def test_density_below_floor_detected():
    errs = validate_density({"heel": 0.10})
    assert any("floor" in e for e in errs)


def test_density_above_ceiling_detected():
    errs = validate_density({"heel": 0.50})
    assert any("ceiling" in e for e in errs)


# ─── Transition validation ───────────────────────────────────────────

def test_no_step_transitions_in_export_plan():
    plan = build_balance_export_plan()
    ts = plan["sigmoid_transition_rules"]["transitions"]
    errs = validate_no_hard_edges(ts)
    assert len(errs) == 0, f"Unexpected hard-edge violations: {errs}"


def test_sigmoid_transitions_generated():
    plan = build_balance_export_plan()
    ts = plan["sigmoid_transition_rules"]["transitions"]
    assert len(ts) == 5  # 5 transitions for 6 zones


def test_each_transition_has_points():
    plan = build_balance_export_plan()
    for t in plan["sigmoid_transition_rules"]["transitions"]:
        assert len(t["transition_points"]) >= 2


def test_adjacent_delta_cap_constant():
    assert EXPORT_ADJACENT_DELTA == 0.06


def test_adjacent_delta_violation_detected():
    # metatarsal->midfoot in SUPPORTED_FOOT_ZONES order: heel,metatarsal,midfoot,...
    errs = validate_adjacent_delta({
        "heel": 0.30, "metatarsal": 0.42, "midfoot": 0.32,
        "arch": 0.28, "forefoot": 0.31, "toes": 0.26,
    })
    # delta between heel(0.30) and metatarsal(0.42) = 0.12 > 0.06
    assert any(e for e in errs)


def test_no_hard_edges_on_valid_transitions():
    density = build_balance_export_plan()["density_by_zone"]
    ts = build_sigmoid_transitions(density)
    errs = validate_no_hard_edges(ts)
    assert len(errs) == 0


# ─── Shrinkage compensation ──────────────────────────────────────────

def test_shrinkage_compensation_is_15():
    assert EXPORT_SHRINKAGE_PCT == 1.5


def test_export_plan_has_shrinkage():
    plan = build_balance_export_plan()
    assert plan["manufacturing_plan"]["shrinkage_compensation_pct"] == 1.5


def test_mesh_config_has_shrinkage():
    plan = build_balance_export_plan()
    with tempfile.TemporaryDirectory() as td:
        path = export_mesh_config(plan, td)
        with open(path) as f:
            data = json.load(f)
        assert data["shrinkage_compensation_pct"] == 1.5


# ─── Shell thickness enforcement ─────────────────────────────────────

def test_shell_thickness_is_08():
    assert EXPORT_SHELL_THICKNESS == 0.8


def test_export_plan_shell_08():
    plan = build_balance_export_plan()
    assert plan["shell_thickness_mm"] == 0.8


def test_shell_thickness_passes():
    assert len(validate_shell_thickness(0.8)) == 0


def test_shell_thickness_violation_detected():
    errs = validate_shell_thickness(0.5)
    assert any("!=" in e for e in errs)


def test_mesh_config_shell_thickness():
    plan = build_balance_export_plan()
    with tempfile.TemporaryDirectory() as td:
        path = export_mesh_config(plan, td)
        with open(path) as f:
            data = json.load(f)
        assert data["shell_thickness_mm"] == 0.8


# ─── MJF-only compatibility ──────────────────────────────────────────

def test_mjf_only_process_constant():
    assert EXPORT_MANUFACTURING == "MJF"


def test_export_plan_is_mjf():
    plan = build_balance_export_plan()
    assert plan["manufacturing_plan"]["primary_process"] == "MJF"


def test_mjf_compatibility_passes():
    plan = build_balance_export_plan()
    errs = validate_mjf_compatibility(plan)
    assert len(errs) == 0, f"Unexpected MJF errors: {errs}"


def test_mjf_rejects_non_mjf():
    fake_plan = {"manufacturing_plan": {"primary_process": "SLS"}}
    errs = validate_mjf_compatibility(fake_plan)
    assert any("not MJF" in e for e in errs)


def test_mesh_config_mjf_process():
    plan = build_balance_export_plan()
    with tempfile.TemporaryDirectory() as td:
        path = export_mesh_config(plan, td)
        with open(path) as f:
            data = json.load(f)
        assert data["manufacturing_process"] == "MJF"


# ─── Print sheet content checks ──────────────────────────────────────

def test_print_sheet_mentions_density_zones():
    plan = build_balance_export_plan()
    with tempfile.TemporaryDirectory() as td:
        path = export_print_sheet(plan, td)
        with open(path) as f:
            content = f.read()
    assert "Density by Zone" in content
    assert "heel" in content
    assert "ready_for_print" in content


def test_print_sheet_exports_shelling():
    plan = build_balance_export_plan()
    with tempfile.TemporaryDirectory() as td:
        path = export_print_sheet(plan, td)
        with open(path) as f:
            content = f.read()
    assert "0.8" in content
    assert "MJF" in content

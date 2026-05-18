"""Tests for X Research Radar planning tool.

All tests use local/mock data only — no auth, no network, no X connection.
"""

import pathlib
import io
import sys
from unittest import mock

import yaml

REPO_ROOT = pathlib.Path(__file__).resolve().parent.parent

# Import after setting up path
sys.path.insert(0, str(REPO_ROOT / "tools"))
import x_research_radar_plan as radar_tool  # noqa: E402


# ── Fixtures ─────────────────────────────────────────────────────────

VALID_CONFIG = {
    "radar": {
        "name": "Test Radar",
        "version": "0.1.0",
        "mode": "local_planning_only",
        "integration_target": "hermes_v0.14_x_search",
        "blocked_actions": [
            "post",
            "reply",
            "like",
            "follow",
            "auto_execute",
        ],
        "allowed_actions": [
            "plan_queries",
            "render_reports",
        ],
        "constraint": "engineering_research_only",
    },
    "query_groups": [
        {
            "id": "ai_product_design",
            "name": "AI Product Design",
            "description": "AI tools for product design.",
            "sample_queries": ["AI design tools"],
            "tags": ["ai", "design"],
            "priority": "high",
        },
        {
            "id": "footwear_customization",
            "name": "Footwear Customization",
            "description": "Custom footwear tech.",
            "sample_queries": ["custom shoe scan"],
            "tags": ["footwear"],
            "priority": "high",
        },
    ],
    "report_template": {
        "title": "Test Report",
        "sections": [
            {"id": "summary", "name": "Summary", "description": "High-level findings"}
        ],
    },
}


def _write_temp_config(tmp_path, config_dict):
    cfg_path = tmp_path / "config" / "test_radar.yaml"
    cfg_path.parent.mkdir(exist_ok=True)
    with open(cfg_path, "w", encoding="utf-8") as f:
        yaml.dump(config_dict, f)
    return str(cfg_path)


# ── Tests ────────────────────────────────────────────────────────────

def test_config_has_8_query_groups():
    """Verify the real config has exactly 8 query groups."""
    cfg = radar_tool.load_config()
    groups = cfg["query_groups"]
    assert len(groups) == 8, f"Expected 8 query groups, got {len(groups)}"


def test_query_group_ids():
    """Verify all expected query group IDs are present."""
    cfg = radar_tool.load_config()
    ids = {g["id"] for g in cfg["query_groups"]}
    expected_ids = {
        "ai_product_design_tools",
        "ai_cad_parametric_design",
        "footwear_customization",
        "three_d_printed_shoes_materials",
        "sports_shoe_biomechanics",
        "mobile_measurement_cv_ux",
        "competitors_adjacent_products",
        "manufacturing_sample_readiness",
    }
    assert ids == expected_ids, f"Expected {expected_ids}, got {ids}"


def test_query_groups_have_sample_queries():
    """Every query group must have at least one sample query."""
    cfg = radar_tool.load_config()
    for g in cfg["query_groups"]:
        queries = g.get("sample_queries")
        assert queries, f"Query group '{g['id']}' must have sample_queries"
        assert len(queries) >= 1, f"Query group '{g['id']}' must have >=1 query"


def test_query_groups_have_priority():
    """Every query group must declare a priority."""
    cfg = radar_tool.load_config()
    for g in cfg["query_groups"]:
        assert g.get("priority"), f"Query group '{g['id']}' must have priority"


def test_all_query_group_ids_unique():
    """Query group IDs must be unique."""
    cfg = radar_tool.load_config()
    ids = [g["id"] for g in cfg["query_groups"]]
    assert len(ids) == len(set(ids)), "Duplicate query group IDs found"


def test_blocked_actions_include_posting_replying_liking_following():
    """Blocked actions MUST include: post, reply, like, follow, auto_execute."""
    cfg = radar_tool.load_config()
    blocked = set(cfg["radar"]["blocked_actions"])
    required_blocked = {"post", "reply", "like", "follow", "auto_execute"}
    for action in required_blocked:
        assert action in blocked, f"Blocked actions must include '{action}'"


def test_blocked_actions_include_auto_execution():
    """Blocked actions must include auto_execute."""
    cfg = radar_tool.load_config()
    blocked = cfg["radar"]["blocked_actions"]
    assert "auto_execute" in blocked, "auto_execute must be in blocked_actions"


def test_mode_is_local_planning_only():
    """Mode must NOT be 'active' — planning only for now."""
    cfg = radar_tool.load_config()
    assert cfg["radar"]["mode"] == "local_planning_only", \
        f"Mode must be local_planning_only, got {cfg['radar']['mode']}"


def test_no_auth_config_in_radar_config():
    """Config must NOT contain any auth/network credentials."""
    cfg = radar_tool.load_config()
    raw = str(cfg)
    forbidden = ["api_key", "secret", "token", "password", "oauth", "bearer"]
    lowercase_raw = raw.lower()
    for keyword in forbidden:
        assert keyword not in lowercase_raw, \
            f"Config must not contain '{keyword}' — found in radar config"


def test_constraint_is_engineering_research_only():
    """Constraint must enforce engineering research only."""
    cfg = radar_tool.load_config()
    assert cfg["radar"]["constraint"] == "engineering_research_only"


def test_validate_config_passes_for_valid_config():
    """A valid config should pass validation."""
    assert radar_tool.validate_config(VALID_CONFIG) is True


def test_validate_fails_missing_blocked_actions(monkeypatch, tmp_path):
    """Config missing required blocked actions must fail validation."""
    bad_config = dict(VALID_CONFIG)
    bad_config["radar"] = dict(VALID_CONFIG["radar"])
    bad_config["radar"]["blocked_actions"] = ["post"]  # Missing reply, like, follow, auto_execute

    captured = io.StringIO()
    monkeypatch.setattr(sys, "stdout", captured)
    result = radar_tool.validate_config(bad_config)
    assert result is False
    assert "Missing blocked_actions" in captured.getvalue()


def test_validate_fails_empty_query_groups(monkeypatch, tmp_path):
    """Config with empty query_groups must fail."""
    bad_config = {
        "radar": dict(VALID_CONFIG["radar"]),
        "query_groups": [],
        "report_template": {"sections": [{"id": "s", "name": "s"}]},
    }
    captured = io.StringIO()
    monkeypatch.setattr(sys, "stdout", captured)
    result = radar_tool.validate_config(bad_config)
    assert result is False


def test_validate_fails_missing_top_level_key(monkeypatch, tmp_path):
    """Config missing a top-level key must fail validation."""
    bad_config = {
        "radar": dict(VALID_CONFIG["radar"]),
        "query_groups": VALID_CONFIG["query_groups"][:],
    }
    captured = io.StringIO()
    monkeypatch.setattr(sys, "stdout", captured)
    result = radar_tool.validate_config(bad_config)
    assert result is False
    assert "report_template" in captured.getvalue()


def test_validate_fails_duplicate_ids(monkeypatch, tmp_path):
    """Config with duplicate query group IDs must fail."""
    bad_groups = [
        VALID_CONFIG["query_groups"][0],
        VALID_CONFIG["query_groups"][0],  # duplicate id
    ]
    bad_config = dict(VALID_CONFIG)
    bad_config["query_groups"] = bad_groups
    captured = io.StringIO()
    monkeypatch.setattr(sys, "stdout", captured)
    result = radar_tool.validate_config(bad_config)
    assert result is False


def test_print_plan_runs_without_error(monkeypatch, tmp_path):
    """print_plan() should run without errors on valid config."""
    captured = io.StringIO()
    monkeypatch.setattr(sys, "stdout", captured)
    radar_tool.print_plan(VALID_CONFIG)
    output = captured.getvalue()
    assert "Test Radar" in output
    assert "AI Product Design" in output
    assert "Blocked" in output


def test_print_summary_runs_without_error(monkeypatch, tmp_path):
    """print_summary() should run without errors on valid config."""
    captured = io.StringIO()
    monkeypatch.setattr(sys, "stdout", captured)
    radar_tool.print_summary(VALID_CONFIG)
    output = captured.getvalue()
    assert "Summary" in output
    assert "2" in output  # 2 query groups in test config


def test_load_real_config_no_exceptions():
    """Loading the real config should not raise."""
    cfg = radar_tool.load_config()
    assert cfg is not None
    assert "radar" in cfg
    assert "query_groups" in cfg
    assert "report_template" in cfg


def test_summary_mentions_all_critical_blocked(monkeypatch, tmp_path):
    """Summary must state all critical actions are blocked."""
    captured = io.StringIO()
    monkeypatch.setattr(sys, "stdout", captured)
    radar_tool.print_summary(VALID_CONFIG)
    output = captured.getvalue()
    assert "All critical actions blocked" in output


def test_validate_fails_active_mode(monkeypatch, tmp_path):
    """Config with mode='active' must fail validation."""
    bad_config = dict(VALID_CONFIG)
    bad_config["radar"] = dict(VALID_CONFIG["radar"])
    bad_config["radar"]["mode"] = "active"
    captured = io.StringIO()
    monkeypatch.setattr(sys, "stdout", captured)
    result = radar_tool.validate_config(bad_config)
    assert result is False
    assert "must NOT be 'active'" in captured.getvalue()


def test_biomechanics_has_engineering_only_note(monkeypatch, tmp_path):
    """The biomechanics group must have an engineering-only note."""
    cfg = radar_tool.load_config()
    for g in cfg["query_groups"]:
        if g["id"] == "sports_shoe_biomechanics":
            note = g.get("note", "")
            assert "engineering" in note.lower() or "technical" in note.lower(), \
                "Biomechanics group must note engineering-only scope"
            break
    else:
        assert False, "sports_shoe_biomechanics group not found"


# ── pytest entry point ───────────────────────────────────────────────
if __name__ == "__main__":
    import pytest
    sys.exit(pytest.main([__file__, "-v"]))

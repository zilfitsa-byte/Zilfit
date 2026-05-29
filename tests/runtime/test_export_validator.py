"""Tests for ZILFIT Export Validator (P01 BALANCE handoff)."""

import json
import os
from pathlib import Path

import pytest

BASE = Path(__file__).resolve().parent.parent.parent
PLAN_PATH = BASE / "exports" / "p01_balance" / "balance_plan.json"

import sys
sys.path.insert(0, str(BASE / "runtime"))

from zilfit_export_validator import _load, validate, ValidationResult

# ── Fixtures ──────────────────────────────────────────────────────────

@pytest.fixture()
def plan():
    with open(PLAN_PATH) as f:
        return json.load(f)

# ── 1. الملف موجود ──

def test_plan_file_exists():
    assert PLAN_PATH.exists(), f"Plan file not found: {PLAN_PATH}"

# ── 2. JSON صالح ──

def test_plan_is_valid_json():
    with open(PLAN_PATH) as f:
        data = json.load(f)
    assert isinstance(data, dict)

# ── 3. density داخل 0.18–0.45 (floor/ceiling) ──

def test_density_within_global_bounds(plan):
    dbz = plan["density_by_zone"]
    dr = plan["density_range"]
    floor = dr["floor"]
    ceil = dr["ceiling"]
    for zone, d in dbz.items():
        assert floor <= d <= ceil, f"{zone}: {d} outside [{floor}, {ceil}]"

# ── 4. BALANCE density داخل 0.26–0.32 ──

def test_balance_density_range(plan):
    assert plan["edition"] == "BALANCE"
    dbz = plan["density_by_zone"]
    br = plan["density_range"]
    for zone, d in dbz.items():
        assert br["min"] <= d <= br["max"], \
            f"{zone}: {d} outside BALANCE range [{br['min']}, {br['max']}]"

# ── 5. shell thickness >= 0.8 ──

def test_shell_thickness(plan):
    shell = plan["wall_thickness"]["outer_shell_mm"]
    assert shell >= 0.8, f"Shell thickness {shell} < 0.8 mm"

# ── 6. shrink compensation = 1.5 ──

def test_shrink_compensation(plan):
    assert abs(plan["shrink_compensation_pct"] - 1.5) < 0.01, \
        f"Shrink compensation {plan['shrink_compensation_pct']} != 1.5%"

# ── 7. process = MJF ──

def test_process_is_mjf(plan):
    assert plan["process"] == "MJF", f"Process is {plan['process']}, expected MJF"

# ── 8. no hard edges ──

def test_no_hard_edges(plan):
    st = plan["sigmoid_transitions"]
    assert st["hard_edges_allowed"] is False, "hard_edges_allowed must be False"

# ── 9. adjacent delta <= 0.06 ──

def test_adjacent_delta(plan):
    dbz = plan["density_by_zone"]
    st = plan["sigmoid_transitions"]
    delta_max = st["adjacent_delta_max"]
    zone_order = ["heel", "metatarsal", "midfoot", "arch", "forefoot", "toes"]
    for i in range(len(zone_order) - 1):
        a, b = zone_order[i], zone_order[i + 1]
        d = abs(dbz[b] - dbz[a])
        assert d <= delta_max + 1e-9, \
            f"Adjacent delta {a}-> {b}: {d} > {delta_max}"

# ── 10. ready flags كلها true ──

def test_ready_flags_all_true(plan):
    assert plan["ready_for_nTop"] is True
    assert plan["ready_for_print"] is True
    assert plan["ready_for_stl"] is True

# ── 11. validate() returns score == TOTAL ──

def test_validate_returns_perfect_score(plan):
    result = validate(plan)
    from zilfit_export_validator import TOTAL
    assert result.passed(), f"Blockers: {result.blockers}"
    assert result.score == TOTAL, f"Score {result.score}/{TOTAL}"
    assert not result.blockers

# ── 12. validate() rejects bad plan ──

def test_validator_catches_missing_process():
    bad_plan = {
        "prototype_id": "X", "edition": "BALANCE",
        "density_by_zone": {"heel": 0.30},
        "density_range": {"floor": 0.18, "ceiling": 0.45, "min": 0.26, "max": 0.32},
        "wall_thickness": {"outer_shell_mm": 0.8},
        "shrink_compensation_pct": 1.5,
        "sigmoid_transitions": {"hard_edges_allowed": False, "adjacent_delta_max": 0.06},
        "ready_for_nTop": True, "ready_for_print": True, "ready_for_stl": True,
        # process missing
    }
    r = validate(bad_plan)
    assert not r.passed(), "Should fail without process field"
    assert any("process" in b.lower() or "Process" in b for b in r.blockers)

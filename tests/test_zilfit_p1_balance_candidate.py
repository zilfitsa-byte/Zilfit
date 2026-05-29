"""
Tests for ZILFIT Prototype P1 — BALANCE Candidate.

Covers:
  - All scenario counts (4 weights x 2 usages x 4 phases = 32)
  - Determinism
  - Status values
  - Score ranges
  - Deterministic physics sanity (pressure positive, higher weight = higher pressure)
  - Baseline vs stress-check separation
  - Gait phase coverage
  - Usage mode coverage
  - Hard block logic
  - Report generation completeness
  - Verdict correctness
"""

import json
import math
import os
import sys
from pathlib import Path

import pytest

# Add runtime dir to path
ROOT = Path(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, str(ROOT / "runtime"))

from zilfit_p1_balance_candidate import (
    ALL_WEIGHTS_KG,
    BALANCE_DENSITY,
    BASELINE_WEIGHT_KG,
    CONTACT_AREA_CM2,
    EDITION,
    GAIT_PHASE_KEYS,
    GAIT_PHASES,
    G_CONST,
    STRESS_CHECK_WEIGHTS_KG,
    STIFFNESS_MODIFIER,
    USAGE_KEYS,
    USAGE_MODES,
    ZONES,
    analyze_p1,
    check_hard_blocks,
    compute_compression_stress,
    compute_effective_pressure,
    compute_scores,
    compute_toe_displacement_proxy,
    compute_zone_pressure,
    estimate_fatigue_probability,
    estimate_overload_risk,
    generate_markdown_report,
    run_p1_simulation,
    run_scenario,
)

# ──────────────────────────────────────────────────────────────────────
# CONSTANTS & COVERAGE
# ──────────────────────────────────────────────────────────────────────

EXPECTED_SCENARIOS = (
    len(ALL_WEIGHTS_KG)
    * len(USAGE_KEYS)
    * len(GAIT_PHASE_KEYS)
)


def test_expected_scenario_count():
    assert EXPECTED_SCENARIOS == 4 * 2 * 4, "Should be 32 scenarios"


# ──────────────────────────────────────────────────────────────────────
# SIMULATION RUNS
# ──────────────────────────────────────────────────────────────────────

def test_p1_simulation_total():
    scenarios = run_p1_simulation()
    assert len(scenarios) == EXPECTED_SCENARIOS


# ──────────────────────────────────────────────────────────────────────
# DETERMINISM
# ──────────────────────────────────────────────────────────────────────

def test_determinism():
    s1 = run_p1_simulation()
    s2 = run_p1_simulation()
    for a, b in zip(s1, s2):
        assert a == b


# ──────────────────────────────────────────────────────────────────────
# SCENARIO STRUCTURE
# ──────────────────────────────────────────────────────────────────────

def test_scenario_keys():
    s = run_scenario(80, "daily_walking", "heel_strike")
    required_keys = [
        "weight_kg", "usage_mode", "gait_phase", "density_map",
        "stiffness_modifier", "base_pressures_kpa", "effective_pressures_kpa",
        "compressive_stresses_mpa", "fatigue_probabilities",
        "toe_displacements_mm", "overload_risks", "scores",
        "hard_blocks", "status",
    ]
    for key in required_keys:
        assert key in s, f"Missing key: {key}"


def test_status_values():
    scenarios = run_p1_simulation()
    statuses = set(s["status"] for s in scenarios)
    allowed = {"pass", "needs_revision", "blocked"}
    assert statuses <= allowed, f"Unexpected statuses: {statuses - allowed}"


# ──────────────────────────────────────────────────────────────────────
# SCORE RANGES
# ──────────────────────────────────────────────────────────────────────

def test_score_ranges():
    scenarios = run_p1_simulation()
    for s in scenarios:
        sc = s["scores"]
        assert 0.0 <= sc["comfort_confidence"] <= 100.0
        assert 0.0 <= sc["overload_risk"] <= 100.0
        assert 0.0 <= sc["fatigue_risk"] <= 100.0
        assert 0.0 <= sc["prototype_readiness"] <= 100.0


# ──────────────────────────────────────────────────────────────────────
# DETERMINISTIC PHYSICS SANITY
# ──────────────────────────────────────────────────────────────────────

def test_pressure_positive():
    scenarios = run_p1_simulation()
    for s in scenarios:
        for zone in ZONES:
            assert s["base_pressures_kpa"][zone] >= 0
            assert s["effective_pressures_kpa"][zone] >= 0


def test_higher_weight_higher_pressure():
    """A heavier body should always produce higher effective pressure."""
    scenarios = run_p1_simulation()
    for w1 in ALL_WEIGHTS_KG:
        for w2 in ALL_WEIGHTS_KG:
            if w2 <= w1:
                continue
            for sc1 in scenarios:
                if sc1["weight_kg"] != w1:
                    continue
                for sc2 in scenarios:
                    if (sc2["weight_kg"] != w2
                            or sc2["usage_mode"] != sc1["usage_mode"]
                            or sc2["gait_phase"] != sc1["gait_phase"]):
                        continue
                    for zone in ZONES:
                        assert (
                            sc2["base_pressures_kpa"][zone]
                            >= sc1["base_pressures_kpa"][zone]
                        ), (
                            f"{w2}kg < {w1}kg at {zone} "
                            f"({sc2['base_pressures_kpa'][zone]} < "
                            f"{sc1['base_pressures_kpa'][zone]})"
                        )


def test_density_reduces_pressure():
    """Higher density should reduce effective pressure via better spreading."""
    scenarios = run_p1_simulation()
    for s in scenarios:
        for zone in ZONES:
            assert s["effective_pressures_kpa"][zone] <= s["base_pressures_kpa"][zone]


def test_stress_positive():
    scenarios = run_p1_simulation()
    for s in scenarios:
        for zone in ZONES:
            assert s["compressive_stresses_mpa"][zone] >= 0


def test_fatigue_range():
    scenarios = run_p1_simulation()
    for s in scenarios:
        for zone in ZONES:
            fp = s["fatigue_probabilities"][zone]
            assert 0 <= fp <= 1


# ──────────────────────────────────────────────────────────────────────
# COVERAGE: ALL WEIGHTS
# ──────────────────────────────────────────────────────────────────────

def test_all_weights_present():
    scenarios = run_p1_simulation()
    weights_found = set(s["weight_kg"] for s in scenarios)
    assert weights_found == set(ALL_WEIGHTS_KG)


def test_baseline_weight_in_scenarios():
    scenarios = run_p1_simulation()
    baseline_sc = [s for s in scenarios if s["weight_kg"] == BASELINE_WEIGHT_KG]
    assert len(baseline_sc) == len(USAGE_KEYS) * len(GAIT_PHASE_KEYS)


def test_stress_check_weights():
    scenarios = run_p1_simulation()
    for wk in STRESS_CHECK_WEIGHTS_KG:
        count = sum(1 for s in scenarios if s["weight_kg"] == wk)
        assert count == len(USAGE_KEYS) * len(GAIT_PHASE_KEYS)


# ──────────────────────────────────────────────────────────────────────
# COVERAGE: ALL GAIT PHASES
# ──────────────────────────────────────────────────────────────────────

def test_all_gait_phases_present():
    scenarios = run_p1_simulation()
    gait_found = set(s["gait_phase"] for s in scenarios)
    assert gait_found == set(GAIT_PHASE_KEYS)


def test_gait_phase_scenario_count():
    """Each gait phase should appear: weights * usages times."""
    scenarios = run_p1_simulation()
    expected = len(ALL_WEIGHTS_KG) * len(USAGE_KEYS)
    for gk in GAIT_PHASE_KEYS:
        count = sum(1 for s in scenarios if s["gait_phase"] == gk)
        assert count == expected, f"Phase {gk}: {count} != {expected}"


# ──────────────────────────────────────────────────────────────────────
# COVERAGE: ALL USAGE MODES
# ──────────────────────────────────────────────────────────────────────

def test_all_usage_modes_present():
    scenarios = run_p1_simulation()
    usage_found = set(s["usage_mode"] for s in scenarios)
    assert usage_found == set(USAGE_KEYS)


# ──────────────────────────────────────────────────────────────────────
# DENSITY & EDITION
# ──────────────────────────────────────────────────────────────────────

def test_balanced_density():
    """BALANCE should have uniform density across all zones."""
    vals = list(BALANCE_DENSITY.values())
    assert all(v == vals[0] for v in vals), "BALANCE density should be uniform"


def test_stiffness_modifier_neutral():
    assert STIFFNESS_MODIFIER == 1.0


# ──────────────────────────────────────────────────────────────────────
# HARDBLOCK LOGIC
# ──────────────────────────────────────────────────────────────────────

def test_hard_blocks_are_strings():
    scenarios = run_p1_simulation()
    for s in scenarios:
        for b in s["hard_blocks"]:
            assert isinstance(b, str)


def test_density_hard_block_at_125kg():
    """With BALANCE density=0.50 everywhere, no density block should trigger."""
    scenarios = run_p1_simulation()
    for s in scenarios:
        if s["weight_kg"] >= 110:
            # BALANCE has density 0.50 everywhere > 0.18
            for block in s["hard_blocks"]:
                assert "density" not in block, (
                    f"Unexpected density block at {s['weight_kg']}kg: {block}"
                )


# ──────────────────────────────────────────────────────────────────────
# ANALYSIS
# ──────────────────────────────────────────────────────────────────────

def test_analysis_totals():
    scenarios = run_p1_simulation()
    analysis = analyze_p1(scenarios)
    assert analysis["total_scenarios"] == EXPECTED_SCENARIOS
    assert (analysis["pass"] + analysis["needs_revision"]
            + analysis["blocked"] == EXPECTED_SCENARIOS)


def test_analysis_per_weight():
    scenarios = run_p1_simulation()
    analysis = analyze_p1(scenarios)
    for wk in ALL_WEIGHTS_KG:
        wk_str = str(wk)
        assert wk_str in analysis["per_weight"]
        wa = analysis["per_weight"][wk_str]
        assert wa["total"] == len(USAGE_KEYS) * len(GAIT_PHASE_KEYS)
        assert 0 <= wa["pass_rate"] <= 100
        assert (wa["pass"] + wa["needs_revision"] + wa["blocked"]
                == wa["total"])


def test_analysis_per_gait_phase():
    scenarios = run_p1_simulation()
    analysis = analyze_p1(scenarios)
    for gk in GAIT_PHASE_KEYS:
        assert gk in analysis["per_gait_phase"]
        ga = analysis["per_gait_phase"][gk]
        assert "avg_comfort" in ga
        assert "avg_readiness" in ga
        assert "critical_zones" in ga


def test_analysis_per_usage():
    scenarios = run_p1_simulation()
    analysis = analyze_p1(scenarios)
    for uk in USAGE_KEYS:
        assert uk in analysis["per_usage_mode"]
        ua = analysis["per_usage_mode"][uk]
        assert "avg_comfort" in ua
        assert "avg_readiness" in ua
        assert "blocked_count" in ua


def test_verdict_is_valid():
    scenarios = run_p1_simulation()
    analysis = analyze_p1(scenarios)
    assert analysis["overall_verdict"] in ("pass", "needs_revision", "blocked")


def test_measurement_instructions_present():
    scenarios = run_p1_simulation()
    analysis = analyze_p1(scenarios)
    mi = analysis["measurement_instructions"]
    assert "physical_dimensions" in mi
    assert "mechanical_tests" in mi
    assert "comfort_validation" in mi
    assert "fatigue_observation" in mi
    assert "comparison_to_simulation" in mi
    for items in mi.values():
        assert isinstance(items, list)
        assert len(items) > 0


# ──────────────────────────────────────────────────────────────────────
# REPORT GENERATION
# ──────────────────────────────────────────────────────────────────────

def test_markdown_report_non_empty():
    scenarios = run_p1_simulation()
    analysis = analyze_p1(scenarios)
    md = generate_markdown_report(analysis)
    assert len(md) > 200
    assert "P1" in md
    assert "BALANCE" in md


def test_json_report_contains_keys():
    scenarios = run_p1_simulation()
    analysis = analyze_p1(scenarios)
    jr = analysis  # same dict, ready for JSON
    required = [
        "edition", "total_scenarios", "pass", "needs_revision", "blocked",
        "overall_verdict", "per_weight", "per_gait_phase", "per_usage_mode",
        "measurement_instructions", "density_map",
    ]
    for key in required:
        assert key in jr, f"Missing key: {key}"


def test_json_serializable():
    scenarios = run_p1_simulation()
    analysis = analyze_p1(scenarios)
    # Should not raise
    json_str = json.dumps(analysis, default=str)
    parsed = json.loads(json_str)
    assert parsed["edition"] == EDITION
    assert parsed["total_scenarios"] == EXPECTED_SCENARIOS

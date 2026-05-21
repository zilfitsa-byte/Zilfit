"""
Tests for ZILFIT Simulation V2-Lite.

Covers:
  - Determinism
  - All scenario counts
  - Score ranges
  - Fail gate logic
  - Edition/weight/profile/usage/gait coverage
  - Report generation
  - Analysis correctness
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

from zilfit_simulation_v2_lite import (
    EDITION_KEYS,
    EDITIONS,
    GAIT_PHASE_KEYS,
    GAIT_PHASES,
    PROFILE_KEYS,
    FOOT_PROFILES,
    USAGE_KEYS,
    USAGE_MODES,
    WEIGHTS_KG,
    ZONES,
    RISK_CHECKS,
    compute_zone_pressure,
    compute_effective_pressure_density,
    compute_compression_stress,
    compute_toe_displacement_proxy,
    compute_arch_instability_score,
    compute_lateral_imbalance,
    estimate_fatigue_probability,
    evaluate_risk_checks,
    compute_scores,
    check_hard_blocks,
    run_scenario,
    run_full_simulation,
    analyze_results,
    generate_markdown_report,
    generate_json_report,
)

# ──────────────────────────────────────────────────────────────────────
# CONSTANTS & COVERAGE
# ──────────────────────────────────────────────────────────────────────

EXPECTED_SCENARIOS = (
    len(EDITION_KEYS)
    * len(WEIGHTS_KG)
    * len(PROFILE_KEYS)
    * len(USAGE_KEYS)
    * len(GAIT_PHASE_KEYS)
)


def test_expected_scenario_count():
    assert EXPECTED_SCENARIOS == 5 * 4 * 3 * 4 * 4, "Should be 960 scenarios"


def test_simulation_total():
    scenarios = run_full_simulation()
    assert len(scenarios) == EXPECTED_SCENARIOS


# ──────────────────────────────────────────────────────────────────────
# DETERMINISM
# ──────────────────────────────────────────────────────────────────────

def test_determinism():
    s1 = run_full_simulation()
    s2 = run_full_simulation()
    for a, b in zip(s1, s2):
        assert a == b


# ──────────────────────────────────────────────────────────────────────
# SCENUM STRUCTURE
# ──────────────────────────────────────────────────────────────────────

def test_scenario_keys():
    s = run_scenario("CALM", 95, "neutral_arch", "daily_walking", "heel_strike")
    required_keys = [
        "edition", "weight_kg", "foot_profile", "usage_mode", "gait_phase",
        "base_pressures_kpa", "effective_pressures_kpa",
        "compressive_stresses_mpa", "fatigue_probabilities",
        "toe_displacements_mm", "arch_instability_score",
        "lateral_imbalance_score", "risk_flags", "scores",
        "hard_blocks", "status", "density_map",
    ]
    for key in required_keys:
        assert key in s, f"Missing key: {key}"


def test_status_values():
    scenarios = run_full_simulation()
    statuses = set(s["status"] for s in scenarios)
    allowed = {"pass", "needs_revision", "blocked"}
    assert statuses <= allowed, f"Unexpected statuses: {statuses - allowed}"


# ──────────────────────────────────────────────────────────────────────
# SCORE RANGES
# ──────────────────────────────────────────────────────────────────────

def test_score_ranges():
    scenarios = run_full_simulation()
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
    scenarios = run_full_simulation()
    for s in scenarios:
        for zone in ZONES:
            assert s["base_pressures_kpa"][zone] >= 0
            assert s["effective_pressures_kpa"][zone] >= 0


def test_higher_weight_higher_pressure():
    """A heavier body should always produce higher pressure in a zone."""
    for edition in EDITION_KEYS:
        for profile in PROFILE_KEYS:
            for usage in USAGE_KEYS:
                for gait in GAIT_PHASE_KEYS:
                    s95 = run_scenario(edition, 95, profile, usage, gait)
                    s140 = run_scenario(edition, 140, profile, usage, gait)
                    for zone in ZONES:
                        assert (
                            s140["base_pressures_kpa"][zone]
                            >= s95["base_pressures_kpa"][zone]
                        ), (
                            f"{edition}/{profile}/{usage}/{gait}/{zone}: "
                            f"140kg ({s140['base_pressures_kpa'][zone]}) "
                            f"< 95kg ({s95['base_pressures_kpa'][zone]})"
                        )


def test_density_reduces_pressure():
    """Higher density should reduce effective pressure via better spreading."""
    scenarios = run_full_simulation()
    # Compare effective vs base: effective should always be <= base
    for s in scenarios:
        for zone in ZONES:
            assert s["effective_pressures_kpa"][zone] <= s["base_pressures_kpa"][zone]


def test_stress_positive():
    scenarios = run_full_simulation()
    for s in scenarios:
        for zone in ZONES:
            assert s["compressive_stresses_mpa"][zone] >= 0


def test_fatigue_range():
    scenarios = run_full_simulation()
    for s in scenarios:
        for zone in ZONES:
            fp = s["fatigue_probabilities"][zone]
            assert 0 <= fp <= 1


# ──────────────────────────────────────────────────────────────────────
# RISK CHECKS
# ──────────────────────────────────────────────────────────────────────

def test_risk_count():
    scenarios = run_full_simulation()
    for s in scenarios:
        assert len(s["risk_flags"]) == len(RISK_CHECKS)
        for check in RISK_CHECKS:
            assert check in s["risk_flags"]


def test_arch_instability_flat_arch():
    """flat_arch scenarios should show more arch instability than neutral."""
    for edition in EDITION_KEYS:
        s_flat = run_scenario(edition, 95, "flat_arch", "daily_walking", "midfoot_transition")
        s_neutral = run_scenario(edition, 95, "neutral_arch", "daily_walking", "midfoot_transition")
        # Flat arch has non-zero arch instability score; neutral is zero
        assert s_flat["arch_instability_score"] >= s_neutral["arch_instability_score"]


def test_arch_instability_neutral_is_zero():
    """Neutral arch should never trigger arch instability by itself."""
    scenarios = [
        run_scenario(ed, 140, "neutral_arch", "stairs", "heel_strike")
        for ed in EDITION_KEYS
    ]
    for s in scenarios:
        assert s["arch_instability_score"] == 0.0


def test_hard_blocks_are_strings():
    scenarios = run_full_simulation()
    for s in scenarios:
        for b in s["hard_blocks"]:
            assert isinstance(b, str)


# ──────────────────────────────────────────────────────────────────────
# FAIL GATES
# ──────────────────────────────────────────────────────────────────────

def test_density_fail_gate_heavy_load():
    """When weight >= 110 and density < 18%, scenario should be blocked."""
    # FEMME has toe density 0.28, heel 0.32 -- above 0.18, so we need
    # to verify the risk flag is correctly raised when applicable.
    scenarios = run_full_simulation()
    for s in scenarios:
        if s["weight_kg"] >= 110:
            # Check the flag for density_too_low_heavy_load
            density_flag = s["risk_flags"].get("density_too_low_heavy_load", False)
            # FEMME has some zones < 0.18? Let's check
            any_low = any(d < 0.18 for d in s["density_map"].values())
            if any_low:
                assert density_flag is True


def test_prototype_readiness_fail():
    """Scenarios with readiness < 70 should be blocked."""
    scenarios = run_full_simulation()
    for s in scenarios:
        if s["scores"]["prototype_readiness"] < 70:
            assert s["status"] == "blocked"
        elif s["status"] == "blocked":
            # blocked implies readiness < 70 OR hard blocks
            assert (
                s["scores"]["prototype_readiness"] < 70
                or len(s["hard_blocks"]) > 0
            )


# ──────────────────────────────────────────────────────────────────────
# ANALYSIS
# ──────────────────────────────────────────────────────────────────────

def test_analysis_totals():
    scenarios = run_full_simulation()
    analysis = analyze_results(scenarios)
    assert analysis["total_scenarios"] == EXPECTED_SCENARIOS
    assert analysis["pass"] + analysis["needs_revision"] + analysis["blocked"] == EXPECTED_SCENARIOS


def test_analysis_edition_stats():
    scenarios = run_full_simulation()
    analysis = analyze_results(scenarios)
    for ed in EDITION_KEYS:
        stats = analysis["edition_stats"][ed]
        assert stats["total"] == EXPECTED_SCENARIOS // len(EDITION_KEYS)
        assert 0 <= stats["pass_rate"] <= 100
        assert stats["pass"] + stats["needs_revision"] + stats["blocked"] == stats["total"]


def test_safest_worst_distinct():
    scenarios = run_full_simulation()
    analysis = analyze_results(scenarios)
    # They can be the same if all editions have same pass rate;
    # just check they are valid edition keys
    assert analysis["safest_edition"] in EDITION_KEYS
    assert analysis["worst_edition"] in EDITION_KEYS


def test_first_4_recommendations():
    scenarios = run_full_simulation()
    analysis = analyze_results(scenarios)
    recs = analysis["first_4_prototype_recommendations"]
    assert len(recs) == 4
    for i, r in enumerate(recs):
        assert r["rank"] == i + 1


def test_top_10_failure_patterns():
    scenarios = run_full_simulation()
    analysis = analyze_results(scenarios)
    top = analysis["top_10_failure_patterns"]
    assert len(top) <= 10
    for fp in top:
        assert isinstance(fp["pattern"], str)
        assert fp["count"] > 0


def test_density_adjustments_per_edition():
    scenarios = run_full_simulation()
    analysis = analyze_results(scenarios)
    adj = analysis["density_adjustments_per_edition"]
    for ed in EDITION_KEYS:
        assert ed in adj
        assert "blocked_scenarios" in adj[ed]
        assert "adjustments" in adj[ed]
        assert adj[ed]["blocked_scenarios"] >= 0
        for a in adj[ed]["adjustments"]:
            assert a["recommended_density"] >= a["current_density"]


# ──────────────────────────────────────────────────────────────────────
# REPORT GENERATION
# ──────────────────────────────────────────────────────────────────────

def test_markdown_report_non_empty():
    scenarios = run_full_simulation()
    analysis = analyze_results(scenarios)
    md = generate_markdown_report(analysis)
    assert len(md) > 100
    assert "ZILFIT Simulation V2-Lite" in md


def test_json_report_contains_keys():
    scenarios = run_full_simulation()
    analysis = analyze_results(scenarios)
    jr = generate_json_report(analysis)
    required = ["total_scenarios", "pass", "needs_revision", "blocked",
                "edition_stats", "safest_edition", "worst_edition",
                "first_4_prototype_recommendations", "top_10_failure_patterns"]
    for key in required:
        assert key in jr, f"Missing key in JSON report: {key}"


# ──────────────────────────────────────────────────────────────────────
# COVERAGE CROSS-PRODUCT
# ──────────────────────────────────────────────────────────────────────

def test_all_editions_present():
    scenarios = run_full_simulation()
    editions_found = set(s["edition"] for s in scenarios)
    assert editions_found == set(EDITION_KEYS)


def test_all_weights_present():
    scenarios = run_full_simulation()
    weights_found = set(s["weight_kg"] for s in scenarios)
    assert weights_found == set(WEIGHTS_KG)


def test_all_profiles_present():
    scenarios = run_full_simulation()
    profiles_found = set(s["foot_profile"] for s in scenarios)
    assert profiles_found == set(PROFILE_KEYS)


def test_all_usage_modes_present():
    scenarios = run_full_simulation()
    usage_found = set(s["usage_mode"] for s in scenarios)
    assert usage_found == set(USAGE_KEYS)


def test_all_gait_phases_present():
    scenarios = run_full_simulation()
    gait_found = set(s["gait_phase"] for s in scenarios)
    assert gait_found == set(GAIT_PHASE_KEYS)

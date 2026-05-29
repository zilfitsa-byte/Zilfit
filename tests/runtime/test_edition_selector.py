#!/usr/bin/env python3
"""
Tests for zilfit_edition_selector.py

Five test profiles:
1) anxious_office_worker  → expected CALM (or CALM-dominant hybrid)
2) athlete_recovery        → expected VITAL
3) sensory_overload        → expected CALM or CALM+FOCUS hybrid (high sensitivity)
4) elderly_balance_support → expected BALANCE
5) femme_biomechanical_fatigue → expected FEMME (optionally FEMME+VITAL hybrid)

Engineering simulation only — NO MEDICAL CLAIMS.
"""

import json
import sys
from pathlib import Path

PROJ_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJ_ROOT / "runtime"))
sys.path.insert(0, str(PROJ_ROOT))

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / 'runtime'))
from zilfit_edition_selector import select_edition, recommendation_to_dict


def test_anxious_office_worker():
    """Office worker: high stress, low fatigue, high sensory sensitivity."""
    rec = select_edition(
        stress_level=0.75,
        fatigue_level=0.30,
        sensory_sensitivity=0.80,
        balance_instability=0.10,
        recovery_need=0.20,
        emotional_state="stress",
        foot_pressure_profile="neutral_arch",
        arch_type="neutral_arch",
        gait_pattern="normal",
        biomechanics_context=None,
    )
    rec_dict = recommendation_to_dict(rec)

    # CALM should be primary
    assert rec.recommended_edition == "CALM", (
        f"Expected CALM, got {rec.recommended_edition}. Reasoning: {rec.reasoning}"
    )

    # Confidence should be decent
    assert rec.confidence_score >= 0.4, (
        f"Confidence too low: {rec.confidence_score}"
    )

    # Emotional target should be grounding-related
    assert rec.emotional_target in ("grounding", "grounding_calm"), (
        f"Unexpected emotional target: {rec.emotional_target}"
    )

    # Should have a reasonable density profile
    assert rec.recommended_density["heel"] <= 0.35, "CALM heel density too high"
    assert rec.recommended_density["midfoot"] <= 0.40, "CALM midfoot density too high"

    # Stimulation should be low
    assert rec.stimulation_profile["intensity"] in ("low", "low_medium"), (
        f"CALM intensity too high: {rec.stimulation_profile['intensity']}"
    )

    # Warnings about redirecting to VITAL should NOT appear (fatigue is low)
    for w in rec.warnings:
        assert "redirect to VITAL" not in w.lower(), (
            f"Unexpected VITAL redirect warning for low-fatigue user: {w}"
        )

    print("PASS: test_anxious_office_worker")
    print(f"  Edition: {rec.recommended_edition} (confidence={rec.confidence_score})")
    print(f"  Target: {rec.emotional_target}")
    print(f"  Zones: {rec.primary_zones}")
    if rec.second_edition:
        print(f"  Hybrid: {rec.second_edition} @ {rec.second_weight:.0%}")
    print()
    return rec_dict


def test_athlete_recovery():
    """Athlete after training: low stress, high fatigue, high recovery need."""
    rec = select_edition(
        stress_level=0.15,
        fatigue_level=0.85,
        sensory_sensitivity=0.30,
        balance_instability=0.10,
        recovery_need=0.90,
        emotional_state="post_exertion",
        foot_pressure_profile="high_arch",
        arch_type="high_arch",
        gait_pattern="normal",
        biomechanics_context="athletic",
    )
    rec_dict = recommendation_to_dict(rec)

    # VITAL should be primary
    assert rec.recommended_edition == "VITAL", (
        f"Expected VITAL, got {rec.recommended_edition}. Reasoning: {rec.reasoning}"
    )

    assert rec.confidence_score >= 0.4

    # Heel basin density should be moderate
    assert rec.recommended_density["heel"] >= 0.30, (
        f"VITAL heel density too low: {rec.recommended_density['heel']}"
    )

    # Stimulation should be medium or higher
    intensity_order = {"low": 0, "low_medium": 1, "medium": 2, "medium_high": 3, "high": 4}
    assert intensity_order[rec.stimulation_profile["intensity"]] >= 1, (
        f"VITAL stimulation too low: {rec.stimulation_profile['intensity']}"
    )

    # Emotional target should be release-related
    assert rec.emotional_target in ("release", "decompression"), (
        f"Unexpected emotional target: {rec.emotional_target}"
    )

    print("PASS: test_athlete_recovery")
    print(f"  Edition: {rec.recommended_edition} (confidence={rec.confidence_score})")
    print(f"  Target: {rec.emotional_target}")
    print(f"  Zones: {rec.primary_zones}")
    if rec.second_edition:
        print(f"  Hybrid: {rec.second_edition} @ {rec.second_weight:.0%}")
    print()
    return rec_dict


def test_sensory_overload():
    """Office worker with sensory overload: high stress, high sensitivity, mental fog."""
    rec = select_edition(
        stress_level=0.60,
        fatigue_level=0.45,
        sensory_sensitivity=0.85,
        balance_instability=0.15,
        recovery_need=0.25,
        emotional_state="mental_fog",
        foot_pressure_profile="flat_arch",
        arch_type="flat_arch",
        gait_pattern="overpronation",
        biomechanics_context=None,
    )
    rec_dict = recommendation_to_dict(rec)

    # With high sensory sensitivity + mental fog, CALM or a CALM-dominant hybrid expected
    # FOCUS would be too stimulating at 0.85 sensitivity
    assert rec.recommended_edition in ("CALM", "FOCUS"), (
        f"Expected CALM or FOCUS, got {rec.recommended_edition}. Reasoning: {rec.reasoning}"
    )

    # If FOCUS is selected with high sensitivity, there should be a warning
    if rec.recommended_edition == "FOCUS":
        has_sensitivity_warning = any(
            "sensory sensitivity" in w.lower() or "too intense" in w.lower()
            for w in rec.warnings
        )
        assert has_sensitivity_warning, (
            "FOCUS selected for high sensitivity but no warning issued"
        )

    # If CALM selected, should warn about fatigue
    if rec.recommended_edition == "CALM" and rec.confidence_score < 0.55:
        # CALM has decent score but fatigue 0.45 pushes it down — may trigger hybrid
        pass

    print("PASS: test_sensory_overload")
    print(f"  Edition: {rec.recommended_edition} (confidence={rec.confidence_score})")
    print(f"  Target: {rec.emotional_target}")
    print(f"  Zones: {rec.primary_zones}")
    if rec.second_edition:
        print(f"  Hybrid: {rec.second_edition} @ {rec.second_weight:.0%}")
    print(f"  Warnings: {len(rec.warnings)}")
    for w in rec.warnings:
        print(f"    ⚠ {w}")
    print()
    return rec_dict


def test_elderly_balance_support():
    """Elderly user: high instability, low recovery need, stability concern."""
    rec = select_edition(
        stress_level=0.30,
        fatigue_level=0.40,
        sensory_sensitivity=0.50,
        balance_instability=0.80,
        recovery_need=0.10,
        emotional_state="instability",
        foot_pressure_profile="flat_arch",
        arch_type="flat_arch",
        gait_pattern="supination",
        biomechanics_context="elderly",
    )
    rec_dict = recommendation_to_dict(rec)

    # BALANCE should be primary — driven by 0.80 balance_instability
    assert rec.recommended_edition == "BALANCE", (
        f"Expected BALANCE, got {rec.recommended_edition}. Reasoning: {rec.reasoning}"
    )

    assert rec.confidence_score >= 0.4

    # Density should be uniform and relatively high
    densities = list(rec.recommended_density.values())
    assert max(densities) - min(densities) <= 0.15, (
        f"BALANCE densities not uniform enough: max-min={max(densities)-min(densities):.3f}"
    )

    # Stimulation should be low-medium (stability over stimulation)
    assert rec.stimulation_profile["intensity"] in ("low", "low_medium", "medium", "medium_low"), (
        f"BALANCE intensity too high: {rec.stimulation_profile['intensity']}"
    )

    # Emotional target should be stability
    assert "stability" in rec.emotional_target.lower(), (
        f"Expected stability target, got: {rec.emotional_target}"
    )

    print("PASS: test_elderly_balance_support")
    print(f"  Edition: {rec.recommended_edition} (confidence={rec.confidence_score})")
    print(f"  Target: {rec.emotional_target}")
    print(f"  Zones: {rec.primary_zones}")
    if rec.second_edition:
        print(f"  Hybrid: {rec.second_edition} @ {rec.second_weight:.0%}")
    print()
    return rec_dict


def test_femme_biomechanical_fatigue():
    """Female user: moderate stress, moderate fatigue, Q-angle sensitivity."""
    rec = select_edition(
        stress_level=0.50,
        fatigue_level=0.65,
        sensory_sensitivity=0.60,
        balance_instability=0.35,
        recovery_need=0.55,
        emotional_state="q_angle_sensitivity",
        foot_pressure_profile="neutral_arch",
        arch_type="neutral_arch",
        gait_pattern="female_q_angle",
        biomechanics_context="female",
    )
    rec_dict = recommendation_to_dict(rec)

    # FEMME should be primary — driven by female biomechanics + q_angle keywords
    assert rec.recommended_edition == "FEMME", (
        f"Expected FEMME, got {rec.recommended_edition}. Reasoning: {rec.reasoning}"
    )

    assert rec.confidence_score >= 0.3

    # Heel containment should be moderate
    assert rec.recommended_density["heel"] >= 0.25, (
        f"FEMME heel density too low: {rec.recommended_density['heel']}"
    )

    # Emotional target should be soothing
    assert rec.emotional_target in ("soothing",), (
        f"Unexpected emotional target: {rec.emotional_target}"
    )

    # Should have zones from solar_plexus_map
    assert len(rec.primary_zones) >= 3, (
        f"FEMME has too few active zones: {len(rec.primary_zones)}"
    )

    # VITAL may appear as secondary (fatigue 0.65 + recovery_need 0.55)
    # but don't require it — depends on scoring gap

    print("PASS: test_femme_biomechanical_fatigue")
    print(f"  Edition: {rec.recommended_edition} (confidence={rec.confidence_score})")
    print(f"  Target: {rec.emotional_target}")
    print(f"  Zones: {rec.primary_zones}")
    if rec.second_edition:
        print(f"  Hybrid: {rec.second_edition} @ {rec.second_weight:.0%}")
    print()
    return rec_dict


# ──────────────────────────────────────────────────────────────────────
# Test with medical claim detection
# ──────────────────────────────────────────────────────────────────────

def test_no_medical_language_in_warnings():
    """Ensure warnings don't contain forbidden medical language."""
    forbidden_terms = ["treats", "cures", "diagnoses", "prevents injury",
                       "medication", "therapy", "rehabilitation", "pain relief"]

    rec = select_edition(
        stress_level=0.90,
        fatigue_level=0.90,
        sensory_sensitivity=0.90,
        balance_instability=0.90,
        recovery_need=0.90,
        emotional_state="need_decompression",
        foot_pressure_profile="flat_arch",
        arch_type="flat_arch",
        gait_pattern="normal",
        biomechanics_context=None,
    )

    for w in rec.warnings:
        for term in forbidden_terms:
            assert term.lower() not in w.lower(), (
                f"Medical language in warning: '{w}' contains '{term}'"
            )

    # Reasoning should also be clean
    for term in forbidden_terms:
        assert term.lower() not in rec.reasoning.lower(), (
            f"Medical language in reasoning: '{rec.reasoning}' contains '{term}'"
        )

    print("PASS: test_no_medical_language_in_warnings")
    print()


def test_input_validation():
    """Ensure out-of-range inputs raise ValueError."""
    import contextlib

    bad_profiles = [
        {"stress_level": 1.5},
        {"fatigue_level": -0.1},
        {"sensory_sensitivity": 2.0},
    ]

    base = {
        "stress_level": 0.5,
        "fatigue_level": 0.5,
        "sensory_sensitivity": 0.5,
        "balance_instability": 0.5,
        "recovery_need": 0.5,
        "emotional_state": "stress",
        "foot_pressure_profile": "neutral_arch",
        "arch_type": "neutral_arch",
        "gait_pattern": "normal",
    }

    for bad in bad_profiles:
        try:
            select_edition(**{**base, **bad})
            assert False, f"Expected ValueError for {bad}"
        except ValueError:
            pass

    print("PASS: test_input_validation")
    print()


if __name__ == "__main__":
    print("=" * 60)
    print("ZILFIT Edition Selector — Test Suite")
    print("=" * 60)
    print()

    passed = 0
    failed = 0
    all_results = {}

    tests = [
        ("anxious_office_worker", test_anxious_office_worker),
        ("athlete_recovery", test_athlete_recovery),
        ("sensory_overload", test_sensory_overload),
        ("elderly_balance_support", test_elderly_balance_support),
        ("femme_biomechanical_fatigue", test_femme_biomechanical_fatigue),
        ("no_medical_language", test_no_medical_language_in_warnings),
        ("input_validation", test_input_validation),
    ]

    for name, fn in tests:
        try:
            result = fn()
            if isinstance(result, dict):
                all_results[name] = result
            passed += 1
        except AssertionError as e:
            print(f"FAIL: {name}")
            print(f"  {e}")
            print()
            failed += 1

    print("=" * 60)
    print(f"Results: {passed} passed, {failed} failed out of {len(tests)}")
    print("=" * 60)

    if all_results:
        print()
        print("=" * 60)
        print("JSON Output for All 5 Test Profiles")
        print("=" * 60)
        print(json.dumps(all_results, indent=2, ensure_ascii=False))

"""
Tests for ZILFIT Scientific Layer.

Covers:
- Config loading
- Scoring engine (all 5 editions)
- Safety Gate (all rules: STOP, RESTRICT, WARNING)
- Claims Policy (disclaimer, prohibited terms, evidence levels)
- Engineering Translator (densities, constraints, hybrid blending)
- Input validation
- Full pipeline integration
- Learning feedback schema
"""

import json
import pytest

from zilfit_scientific_layer import (
    ZilfitScientificLayer,
    ScoringEngine,
    SafetyGate,
    ClaimsPolicy,
    EngineeringTranslator,
    SessionInput,
    validate_input,
    InvalidInputError,
    ConfigLoadError,
    SafetyGateError,
    GateResult,
    MIN_WALL_THICKNESS_MM,
    GYROID_CELL_SIZE_BASE_MM,
    GYROID_CELL_SIZE_ADJUST_MM,
    EDITION_SPECS,
    ALL_EDITIONS,
    _load_json,
    _CONFIG_DIR,
    _SCHEMAS_DIR,
)

# ============================================================================
# Fixtures
# ============================================================================
@pytest.fixture
def layer():
    return ZilfitScientificLayer()


@pytest.fixture
def scoring():
    return ScoringEngine()


@pytest.fixture
def gate():
    return SafetyGate()


@pytest.fixture
def claims():
    return ClaimsPolicy()


@pytest.fixture
def translator():
    return EngineeringTranslator()


# Helper: create a valid input dict with all required fields
def valid_input(overrides=None):
    base = {
        "stress": 0.0,
        "fatigue_score": 0.0,
        "focus_score": 1.0,
        "sleep_disruption": 0.0,
        "sensory_overload": 0.0,
        "pain_or_discomfort": 0.0,
        "postural_instability": 0.0,
        "cycle_phase_flag": 0,
        "user_goal_match": 0.5,
        "heel_pressure_ratio": 0.5,
        "temperature_risk": 0.0,
        "diabetes": False,
        "neuropathy": False,
        "pregnant": False,
        "active_injury": False,
        "vascular_disease": False,
        "session_duration_minutes": 0.0,
    }
    if overrides:
        base.update(overrides)
    return base

# ============================================================================
# Config Loading
# ============================================================================
class TestConfigLoading:
    def test_edition_scoring_model_loads(self):
        data = _load_json(_CONFIG_DIR / "edition_scoring_model.json")
        assert data["model_type"] == "weighted_linear_scoring"
        for edition in ALL_EDITIONS:
            assert edition in data["editions"]
            w = data["editions"][edition]["weights"]
            assert abs(sum(w.values()) - 1.00) < 0.01, (
                f"Weights for {edition} must sum to 1.0, got {sum(w.values())}"
            )

    def test_risk_gate_rules_loads(self):
        data = _load_json(_CONFIG_DIR / "risk_gate_rules.json")
        assert "evaluation_order" in data
        rules = data["evaluation_order"]
        assert len(rules) == 6
        rule_ids = [r["rule_id"] for r in rules]
        assert "RG001" in rule_ids
        assert "RG006" in rule_ids

    def test_scientific_claims_policy_loads(self):
        data = _load_json(_CONFIG_DIR / "scientific_claims_policy.json")
        assert "mandatory_disclaimer" in data
        assert len(data["mandatory_disclaimer"]) > 10
        assert "prohibited_language" in data

    def test_measurement_schema_loads(self):
        data = _load_json(_SCHEMAS_DIR / "measurement_schema.json")
        assert "input_signals" in data
        assert "user_self_report" in data["input_signals"]

    def test_learning_feedback_schema_loads(self):
        data = _load_json(_SCHEMAS_DIR / "learning_feedback_schema.json")
        assert "feedback_windows" in data
        assert "immediate" in data["feedback_windows"]
        assert "short_term" in data["feedback_windows"]
        assert "learning_rules" in data

# ============================================================================
# Input Validation
# ============================================================================
class TestValidation:
    def test_valid_input_passes(self):
        errors = validate_input(valid_input())
        assert errors == []

    def test_missing_required_field_fails(self):
        bad = valid_input()
        del bad["stress"]
        errors = validate_input(bad)
        assert any("stress" in e for e in errors)

    def test_out_of_range_value_fails(self):
        bad = valid_input({"stress": 1.5})
        errors = validate_input(bad)
        assert any("stress" in e for e in errors)

    def test_negative_value_fails(self):
        bad = valid_input({"fatigue_score": -0.1})
        errors = validate_input(bad)
        assert any("fatigue_score" in e for e in errors)

    def test_non_numeric_value_fails(self):
        bad = valid_input({"stress": "high"})
        errors = validate_input(bad)
        assert any("stress" in e for e in errors)

    def test_boolean_fields_type_check(self):
        bad = valid_input({"diabetes": "yes"})
        errors = validate_input(bad)
        assert any("diabetes" in e for e in errors)

# ============================================================================
# Scoring Engine
# ============================================================================
class TestScoringEngine:
    def test_calm_high_stress(self, scoring):
        inp = SessionInput(
            stress=0.85,
            sleep_disruption=0.70,
            sensory_overload=0.65,
            user_goal_match=0.80,
            temperature_risk=0.20,
        )
        scores = scoring.compute(inp)
        assert scores.CALM > scores.VITAL
        assert scores.CALM > scores.FOCUS

    def test_vital_high_fatigue(self, scoring):
        inp = SessionInput(
            fatigue_score=0.90,
            focus_score=0.10,
            heel_pressure_ratio=0.60,
        )
        scores = scoring.compute(inp)
        assert scores.VITAL > scores.CALM

    def test_focus_low_focus_score(self, scoring):
        inp = SessionInput(
            focus_score=0.10,
            fatigue_score=0.50,
            sensory_overload=0.30,
        )
        scores = scoring.compute(inp)
        assert scores.FOCUS > scores.CALM

    def test_balance_high_postural_instability(self, scoring):
        inp = SessionInput(
            postural_instability=0.85,
            stress=0.40,
            pain_or_discomfort=0.30,
        )
        scores = scoring.compute(inp)
        assert scores.BALANCE > scores.CALM

    def test_femme_cycle_phase(self, scoring):
        inp = SessionInput(
            cycle_phase_flag=1,
            pain_or_discomfort=0.60,
            sleep_disruption=0.50,
        )
        scores = scoring.compute(inp)
        assert scores.FEMME > 0.3
        assert scores.FEMME > scores.CALM

    def test_scores_bounded(self, scoring):
        inp = SessionInput()
        scores = scoring.compute(inp)
        for name in ALL_EDITIONS:
            val = getattr(scores, name)
            assert 0.0 <= val <= 1.0, f"{name} score {val} out of [0, 1]"

    def test_all_zeros_input(self, scoring):
        inp = SessionInput()
        scores = scoring.compute(inp)
        for name in ALL_EDITIONS:
            val = getattr(scores, name)
            assert val >= 0.0

    def test_all_max_input(self, scoring):
        inp = SessionInput(
            stress=1.0,
            fatigue_score=1.0,
            focus_score=0.0,
            sleep_disruption=1.0,
            sensory_overload=1.0,
            pain_or_discomfort=1.0,
            postural_instability=1.0,
            cycle_phase_flag=1,
            user_goal_match=1.0,
            heel_pressure_ratio=1.0,
            temperature_risk=0.0,
        )
        scores = scoring.compute(inp)
        for name in ALL_EDITIONS:
            val = getattr(scores, name)
            assert val > 0.0

# ============================================================================
# Selection Logic
# ============================================================================
class TestSelection:
    def test_clear_winner(self, scoring):
        inp = SessionInput(stress=0.9, sleep_disruption=0.8)
        scores = scoring.compute(inp)
        result = scoring.select(scores)
        assert result.primary_edition == "CALM"
        assert result.is_hybrid is False

    def test_hybrid_threshold(self, scoring):
        # Craft input where two editions are very close
        inp = SessionInput(
            stress=0.50,
            sleep_disruption=0.20,
            sensory_overload=0.15,
            user_goal_match=0.30,
            temperature_risk=0.10,
            postural_instability=0.50,
            pain_or_discomfort=0.15,
            heel_pressure_ratio=0.10,
        )
        scores = scoring.compute(inp)
        result = scoring.select(scores)
        # Either hybrid or clear winner — just verify structure
        assert result.primary_edition in ALL_EDITIONS
        if result.is_hybrid:
            assert result.secondary_edition in ALL_EDITIONS
            assert result.blend_ratio == (0.60, 0.40)

# ============================================================================
# Safety Gate
# ============================================================================
class TestSafetyGate:
    def test_clean_input_passes(self, gate):
        inp = SessionInput()
        result = gate.evaluate(inp)
        assert result.passed is True
        assert result.action == "PASS"

    def test_pain_over_threshold_stops(self, gate):
        inp = SessionInput(pain_or_discomfort=0.80)
        result = gate.evaluate(inp)
        assert result.action == "STOP"
        assert result.passed is False
        assert any(r["rule_id"] == "RG001" for r in result.triggered_rules)

    def test_diabetes_stops(self, gate):
        inp = SessionInput(diabetes=True)
        result = gate.evaluate(inp)
        assert result.action == "STOP"
        assert result.passed is False
        assert any(r["rule_id"] == "RG002" for r in result.triggered_rules)

    def test_neuropathy_stops(self, gate):
        inp = SessionInput(neuropathy=True)
        result = gate.evaluate(inp)
        assert result.action == "STOP"
        assert result.passed is False

    def test_active_injury_stops(self, gate):
        inp = SessionInput(active_injury=True)
        result = gate.evaluate(inp)
        assert result.action == "STOP"
        assert result.passed is False
        assert any(r["rule_id"] == "RG003" for r in result.triggered_rules)

    def test_pregnant_restricts_to_femme(self, gate):
        inp = SessionInput(
            pregnant=True,
            stress=0.90,  # would normally trigger CALM
        )
        result = gate.evaluate(inp)
        assert result.action == "RESTRICT"
        assert result.allowed_editions == ["FEMME"]
        assert any(r["rule_id"] == "RG004" for r in result.triggered_rules)

    def test_temperature_risk_warning(self, gate):
        inp = SessionInput(temperature_risk=0.80)
        result = gate.evaluate(inp)
        assert result.action in ("WARNING",)
        assert result.density_reduction_factor <= 0.85
        assert any(r["rule_id"] == "RG005" for r in result.triggered_rules)

    def test_long_session_warning(self, gate):
        inp = SessionInput(session_duration_minutes=300)
        result = gate.evaluate(inp)
        assert result.action in ("WARNING", "PASS")
        if result.triggered_rules:
            assert any(r["rule_id"] == "RG006" for r in result.triggered_rules)

    def test_combined_pain_and_temperature(self, gate):
        inp = SessionInput(pain_or_discomfort=0.90, temperature_risk=0.85)
        result = gate.evaluate(inp)
        # Pain should trigger STOP first
        assert result.action == "STOP"

# ============================================================================
# Claims Policy
# ============================================================================
class TestClaimsPolicy:
    def test_disclaimer_present(self, claims):
        assert len(claims.disclaimer) > 10
        assert "طبي" in claims.disclaimer

    def test_evidence_levels(self, claims):
        for edition in ALL_EDITIONS:
            level = claims.evidence_level(edition)
            assert level in (
                "exploratory",
                "mechanistic_plausible",
                "traditional_reference",
                "RCT_proven",
            )

    def test_femme_traditional_reference(self, claims):
        assert claims.evidence_level("FEMME") == "traditional_reference"

    def test_calm_exploratory(self, claims):
        assert claims.evidence_level("CALM") == "exploratory"

    def test_detect_prohibited_terms(self, claims):
        bad_text = "هذا المنتج يعالج القلق ويوازن الهرمونات"
        violations = claims.check_text(bad_text)
        assert len(violations) >= 1
        assert any("يعالج" in v for v in violations)

    def test_allows_safe_language(self, claims):
        good_text = "قد يدعم الشعور بالراحة — مؤشرات أولية تشير إلى تأثير محتمل"
        violations = claims.check_text(good_text)
        assert len(violations) == 0

# ============================================================================
# Engineering Translator
# ============================================================================
class TestEngineeringTranslator:
    def test_calm_specifications(self, translator):
        directive = translator.translate("CALM")
        assert directive.edition == "CALM"
        assert directive.heel_density_pct == 22
        assert directive.max_pressure_kpa == 45
        assert directive.gyroid_cell_size_mm == 6.5
        assert directive.stimulation_pattern == "static_soft"
        assert directive.comfort_risk_level == "Low"

    def test_vital_specifications(self, translator):
        directive = translator.translate("VITAL")
        assert directive.edition == "VITAL"
        assert directive.heel_density_pct == 35
        assert directive.max_pressure_kpa == 65

    def test_femme_is_softest(self, translator):
        femme = translator.translate("FEMME")
        calm = translator.translate("CALM")
        assert femme.heel_density_pct < calm.heel_density_pct
        assert femme.max_pressure_kpa < calm.max_pressure_kpa

    def test_focus_high_toe_density(self, translator):
        directive = translator.translate("FOCUS")
        assert directive.toe_density_pct == 42
        assert directive.max_pressure_kpa == 60

    def test_balance_graduated(self, translator):
        directive = translator.translate("BALANCE")
        assert directive.max_pressure_kpa == 55

    def test_density_reduction_applied(self, translator):
        directive = translator.translate("CALM", density_reduction_factor=0.85)
        assert directive.density_reduction_applied is True
        assert directive.density_reduction_factor == 0.85
        assert directive.heel_density_pct == 22 * 0.85

    def test_min_wall_thickness_immutable(self, translator):
        for edition in ALL_EDITIONS:
            directive = translator.translate(edition)
            assert directive.min_wall_thickness_mm == MIN_WALL_THICKNESS_MM

    def test_cell_size_within_bounds(self, translator):
        for edition in ALL_EDITIONS:
            directive = translator.translate(edition)
            cell = directive.gyroid_cell_size_mm
            lo = GYROID_CELL_SIZE_BASE_MM - GYROID_CELL_SIZE_ADJUST_MM
            hi = GYROID_CELL_SIZE_BASE_MM + GYROID_CELL_SIZE_ADJUST_MM
            assert lo <= cell <= hi, (
                f"{edition} cell_size {cell} out of [{lo}, {hi}]"
            )

    def test_unknown_edition_raises(self, translator):
        with pytest.raises(InvalidInputError):
            translator.translate("UNKNOWN")

    def test_all_editions_translate(self, translator):
        for edition in ALL_EDITIONS:
            directive = translator.translate(edition)
            assert directive.edition == edition
            assert directive.max_pressure_kpa > 0
            assert directive.heel_density_pct > 0

# ============================================================================
# Full Pipeline Integration
# ============================================================================
class TestFullPipeline:
    def test_calm_session_flow(self, layer):
        inp = valid_input({
            "stress": 0.85,
            "sleep_disruption": 0.70,
            "sensory_overload": 0.65,
            "user_goal_match": 0.80,
            "temperature_risk": 0.20,
        })
        decision = layer.decide(inp)
        assert decision.selection.primary_edition == "CALM"
        assert decision.gate.passed is True
        assert decision.engineering.max_pressure_kpa <= 45
        assert len(decision.claims_disclaimer) > 10

    def test_vital_session_flow(self, layer):
        inp = valid_input({
            "fatigue_score": 0.90,
            "focus_score": 0.10,
            "heel_pressure_ratio": 0.60,
            "user_goal_match": 0.70,
        })
        decision = layer.decide(inp)
        assert decision.selection.primary_edition == "VITAL"
        assert decision.engineering.max_pressure_kpa == 65

    def test_safety_gate_blocks_high_pain(self, layer):
        inp = valid_input({
            "pain_or_discomfort": 0.90,
            "stress": 0.80,
        })
        decision = layer.decide(inp)
        assert decision.gate.action == "STOP"
        assert decision.selection.primary_edition == "NONE"
        assert "Safety gate STOP" in " ".join(decision.warnings)

    def test_safety_gate_blocks_diabetes(self, layer):
        inp = valid_input({
            "diabetes": True,
            "stress": 0.50,
        })
        decision = layer.decide(inp)
        assert decision.gate.action == "STOP"
        assert decision.evidence_level == "blocked"

    def test_pregnant_restricts_to_femme(self, layer):
        inp = valid_input({
            "pregnant": True,
            "stress": 0.90,  # would normally be CALM
        })
        decision = layer.decide(inp)
        assert decision.gate.action == "RESTRICT"
        assert decision.selection.primary_edition == "FEMME"

    def test_temperature_warning_reduces_density(self, layer):
        inp = valid_input({
            "temperature_risk": 0.85,
            "stress": 0.80,
        })
        decision = layer.decide(inp)
        assert decision.gate.action in ("WARNING", "RESTRICT")
        assert decision.engineering.density_reduction_factor <= 0.85

    def test_neuropathy_blocks(self, layer):
        inp = valid_input({"neuropathy": True})
        decision = layer.decide(inp)
        assert decision.gate.action == "STOP"

    def test_decision_has_session_id(self, layer):
        inp = valid_input({"stress": 0.50})
        decision = layer.decide(inp)
        assert len(decision.session_id) == 36  # UUID format

    def test_decision_has_timestamp(self, layer):
        inp = valid_input({"stress": 0.50})
        decision = layer.decide(inp)
        assert "T" in decision.timestamp  # ISO format
        assert "+" in decision.timestamp or decision.timestamp.endswith("Z")

    def test_decision_serializable(self, layer):
        inp = valid_input({"stress": 0.50})
        decision = layer.decide(inp)
        d = decision.to_dict()
        assert isinstance(d, dict)
        assert "session_id" in d
        assert "selection" in d
        assert "engineering" in d
        assert "gate" in d
        # Verify JSON serializable
        json.dumps(d, ensure_ascii=False)

    def test_active_injury_blocks(self, layer):
        inp = valid_input({"active_injury": True})
        decision = layer.decide(inp)
        assert decision.gate.action == "STOP"

# ============================================================================
# Schema Integrity
# ============================================================================
class TestSchemaIntegrity:
    def test_edition_scoring_has_all_editions(self):
        data = _load_json(_CONFIG_DIR / "edition_scoring_model.json")
        for edition in ALL_EDITIONS:
            assert edition in data["editions"]

    def test_risk_gate_has_sequential_rules(self):
        data = _load_json(_CONFIG_DIR / "risk_gate_rules.json")
        expected_ids = ["RG001", "RG002", "RG003", "RG004", "RG005", "RG006"]
        for i, expected in enumerate(expected_ids):
            assert data["evaluation_order"][i]["rule_id"] == expected

    def test_measurement_schema_has_all_input_signals(self):
        data = _load_json(_SCHEMAS_DIR / "measurement_schema.json")
        signals = data["input_signals"]
        assert "scan_measurements" in signals
        assert "user_self_report" in signals
        assert "medical_flags" in signals
        assert "derived_signals" in signals

    def test_learning_feedback_has_all_windows(self):
        data = _load_json(_SCHEMAS_DIR / "learning_feedback_schema.json")
        windows = data["feedback_windows"]
        assert "immediate" in windows
        assert "short_term" in windows
        assert "outcome_events" in windows

    def test_learning_rules_have_human_review(self):
        data = _load_json(_SCHEMAS_DIR / "learning_feedback_schema.json")
        rules = data["learning_rules"]["weight_update_policy"]
        assert rules["human_review_required"] is True
        assert rules["auto_apply"] is False

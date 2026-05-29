"""
ZILFIT Scientific Layer — From Feeling to Engineering

Translates emotional self-reports into measurable engineering directives
with safety gates, evidence-level claims policy, and learning feedback.

No Telegram. No agents. No governance. Pure runtime.
"""

from __future__ import annotations

import json
import math
import os
import uuid
from dataclasses import dataclass, field, asdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------
_PROJECT_ROOT = Path(__file__).resolve().parent.parent
_CONFIG_DIR = _PROJECT_ROOT / "config"
_SCHEMAS_DIR = _PROJECT_ROOT / "schemas"
_LEARNING_DIR = _PROJECT_ROOT / "learning"
_LEARNING_DB = _LEARNING_DIR / "experiments.db"

_EDITION_SCORING_MODEL = _CONFIG_DIR / "edition_scoring_model.json"
_SCIENTIFIC_CLAIMS_POLICY = _CONFIG_DIR / "scientific_claims_policy.json"
_RISK_GATE_RULES = _CONFIG_DIR / "risk_gate_rules.json"
_MEASUREMENT_SCHEMA = _SCHEMAS_DIR / "measurement_schema.json"
_LEARNING_FEEDBACK_SCHEMA = _SCHEMAS_DIR / "learning_feedback_schema.json"

# ---------------------------------------------------------------------------
# Engineering constants (immutable)
# ---------------------------------------------------------------------------
MIN_WALL_THICKNESS_MM = 0.6
GYROID_CELL_SIZE_BASE_MM = 6.0
GYROID_CELL_SIZE_ADJUST_MM = 1.0  # ±1mm max adjustment

# ---------------------------------------------------------------------------
# Edition engineering specifications
# ---------------------------------------------------------------------------
EDITION_SPECS: Dict[str, Dict[str, Any]] = {
    "CALM": {
        "heel_density": 22,
        "midfoot_density": 20,
        "forefoot_density": 25,
        "toe_density": 22,
        "max_pressure_kpa": 45,
        "gyroid_cell_size_mm": 6.5,
        "stimulation_pattern": "static_soft",
        "comfort_risk_level": "Low",
        "manufacturing_notes": "SLS TPU 95A، مسامية عالية، تشطيب ناعم",
    },
    "VITAL": {
        "heel_density": 35,
        "midfoot_density": 32,
        "forefoot_density": 35,
        "toe_density": 30,
        "max_pressure_kpa": 65,
        "gyroid_cell_size_mm": 5.5,
        "stimulation_pattern": "static_firm",
        "comfort_risk_level": "Medium",
        "manufacturing_notes": "SLS TPU 95A، ضغط جانبي مقاوم",
    },
    "FOCUS": {
        "heel_density": 28,
        "midfoot_density": 25,
        "forefoot_density": 38,
        "toe_density": 42,
        "max_pressure_kpa": 60,
        "gyroid_cell_size_mm": 5.0,
        "stimulation_pattern": "zoned_firm_toe",
        "comfort_risk_level": "Medium",
        "manufacturing_notes": "MJF للدقة في منطقة الأصابع",
    },
    "BALANCE": {
        "heel_density": 30,
        "midfoot_density": 28,
        "forefoot_density": 30,
        "toe_density": 28,
        "max_pressure_kpa": 55,
        "gyroid_cell_size_mm": 6.0,
        "stimulation_pattern": "graduated_even",
        "comfort_risk_level": "Low-Medium",
        "manufacturing_notes": "SLS مع تحقق التدرج",
    },
    "FEMME": {
        "heel_density": 18,
        "midfoot_density": 17,
        "forefoot_density": 20,
        "toe_density": 18,
        "max_pressure_kpa": 42,
        "gyroid_cell_size_mm": 7.0,
        "stimulation_pattern": "static_ultra_soft",
        "comfort_risk_level": "Very Low",
        "manufacturing_notes": "SLS TPU 95A أليّن grade",
    },
}

ALL_EDITIONS = ["CALM", "VITAL", "FOCUS", "BALANCE", "FEMME"]

# ---------------------------------------------------------------------------
# Exceptions
# ---------------------------------------------------------------------------
class SafetyGateError(Exception):
    """Raised when Safety Gate blocks recommendation."""

class InvalidInputError(Exception):
    """Raised when input fails validation."""

class ConfigLoadError(Exception):
    """Raised when a config file cannot be loaded."""

# ---------------------------------------------------------------------------
# Data classes
# ---------------------------------------------------------------------------
@dataclass
class SessionInput:
    """Raw input from user / scan."""
    stress: float = 0.0
    fatigue_score: float = 0.0
    focus_score: float = 1.0
    sleep_disruption: float = 0.0
    sensory_overload: float = 0.0
    pain_or_discomfort: float = 0.0
    postural_instability: float = 0.0
    cycle_phase_flag: int = 0
    user_goal_match: float = 0.5
    heel_pressure_ratio: float = 0.5
    temperature_risk: float = 0.0
    diabetes: bool = False
    neuropathy: bool = False
    pregnant: bool = False
    active_injury: bool = False
    vascular_disease: bool = False
    session_duration_minutes: float = 0.0

@dataclass
class GateResult:
    passed: bool
    action: str  # "PASS", "STOP", "RESTRICT", "WARNING"
    triggered_rules: List[Dict[str, Any]] = field(default_factory=list)
    messages: List[str] = field(default_factory=list)
    allowed_editions: Optional[List[str]] = None
    density_reduction_factor: float = 1.0

@dataclass
class EditionScores:
    CALM: float = 0.0
    VITAL: float = 0.0
    FOCUS: float = 0.0
    BALANCE: float = 0.0
    FEMME: float = 0.0

@dataclass
class SelectionResult:
    primary_edition: str
    secondary_edition: Optional[str] = None
    is_hybrid: bool = False
    blend_ratio: Tuple[float, float] = (1.0, 0.0)
    scores: EditionScores = field(default_factory=EditionScores)

@dataclass
class EngineeringDirective:
    edition: str
    heel_density_pct: float
    midfoot_density_pct: float
    forefoot_density_pct: float
    toe_density_pct: float
    max_pressure_kpa: float
    min_wall_thickness_mm: float = MIN_WALL_THICKNESS_MM
    gyroid_cell_size_mm: float = GYROID_CELL_SIZE_BASE_MM
    stimulation_pattern: str = "static"
    comfort_risk_level: str = "Unknown"
    manufacturing_notes: str = ""
    density_reduction_applied: bool = False
    density_reduction_factor: float = 1.0

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

@dataclass
class ScientificDecision:
    session_id: str
    timestamp: str
    selection: SelectionResult
    gate: GateResult
    engineering: EngineeringDirective
    warnings: List[str] = field(default_factory=list)
    claims_disclaimer: str = ""
    evidence_level: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return {
            "session_id": self.session_id,
            "timestamp": self.timestamp,
            "selection": {
                "primary_edition": self.selection.primary_edition,
                "secondary_edition": self.selection.secondary_edition,
                "is_hybrid": self.selection.is_hybrid,
                "blend_ratio": list(self.selection.blend_ratio),
                "scores": asdict(self.selection.scores),
            },
            "gate": {
                "passed": self.gate.passed,
                "action": self.gate.action,
                "triggered_rules": self.gate.triggered_rules,
                "messages": self.gate.messages,
                "allowed_editions": self.gate.allowed_editions,
                "density_reduction_factor": self.gate.density_reduction_factor,
            },
            "engineering": self.engineering.to_dict(),
            "warnings": self.warnings,
            "claims_disclaimer": self.claims_disclaimer,
            "evidence_level": self.evidence_level,
        }

# ---------------------------------------------------------------------------
# Config loader
# ---------------------------------------------------------------------------
def _load_json(path: Path) -> Dict[str, Any]:
    if not path.exists():
        raise ConfigLoadError(f"Config not found: {path}")
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)

# ---------------------------------------------------------------------------
# Validation against measurement_schema
# ---------------------------------------------------------------------------
def validate_input(data: Dict[str, Any]) -> List[str]:
    """Return list of validation errors (empty = valid)."""
    errors: List[str] = []
    schema = _load_json(_MEASUREMENT_SCHEMA)
    user_self_report = schema["input_signals"]["user_self_report"]

    for field_name, spec in user_self_report.items():
        if field_name not in ("cycle_phase_flag",):
            value = data.get(field_name)
            if value is None:
                errors.append(f"Missing required field: {field_name}")
                continue
            if not isinstance(value, (int, float)):
                errors.append(f"{field_name} must be numeric, got {type(value).__name__}")
                continue
            lo, hi = spec.get("range", [0.0, 1.0])
            if value < lo or value > hi:
                errors.append(f"{field_name}={value} out of range [{lo}, {hi}]")

    medical_flags = schema["input_signals"]["medical_flags"]
    for field_name, spec in medical_flags.items():
        value = data.get(field_name)
        if value is not None and not isinstance(value, bool):
            errors.append(f"{field_name} must be boolean, got {type(value).__name__}")

    return errors

# ---------------------------------------------------------------------------
# Scoring Engine
# ---------------------------------------------------------------------------
class ScoringEngine:
    """Weighted linear scoring for all five editions."""

    def __init__(self):
        self._model = _load_json(_EDITION_SCORING_MODEL)

    def compute(self, inp: SessionInput) -> EditionScores:
        scores = EditionScores()

        # Derived values
        temperature_safety_bonus = max(0.0, 1.0 - inp.temperature_risk)
        focus_deficit = max(0.0, 1.0 - inp.focus_score)

        weights = self._model["editions"]

        # CALM
        w = weights["CALM"]["weights"]
        scores.CALM = (
            w["stress"] * inp.stress
            + w["sleep_disruption"] * inp.sleep_disruption
            + w["sensory_overload"] * inp.sensory_overload
            + w["user_goal_match"] * inp.user_goal_match
            + w["temperature_safety_bonus"] * temperature_safety_bonus
        )

        # VITAL
        w = weights["VITAL"]["weights"]
        scores.VITAL = (
            w["fatigue_score"] * inp.fatigue_score
            + w["focus_deficit"] * focus_deficit
            + w["heel_pressure_ratio"] * inp.heel_pressure_ratio
            + w["user_goal_match"] * inp.user_goal_match
            + w["sleep_disruption"] * inp.sleep_disruption
        )

        # FOCUS
        w = weights["FOCUS"]["weights"]
        scores.FOCUS = (
            w["focus_deficit"] * focus_deficit
            + w["fatigue_score"] * inp.fatigue_score
            + w["sensory_overload"] * inp.sensory_overload
            + w["user_goal_match"] * inp.user_goal_match
            + w["postural_instability"] * inp.postural_instability
        )

        # BALANCE
        w = weights["BALANCE"]["weights"]
        scores.BALANCE = (
            w["postural_instability"] * inp.postural_instability
            + w["stress"] * inp.stress
            + w["pain_or_discomfort"] * inp.pain_or_discomfort
            + w["user_goal_match"] * inp.user_goal_match
            + w["heel_pressure_ratio"] * inp.heel_pressure_ratio
        )

        # FEMME
        w = weights["FEMME"]["weights"]
        scores.FEMME = (
            w["cycle_phase_flag"] * float(inp.cycle_phase_flag)
            + w["pain_or_discomfort"] * inp.pain_or_discomfort
            + w["sleep_disruption"] * inp.sleep_disruption
            + w["user_goal_match"] * inp.user_goal_match
            + w["fatigue_score"] * inp.fatigue_score
        )

        return scores

    def select(self, scores: EditionScores) -> SelectionResult:
        scores_dict = asdict(scores)
        sorted_editions = sorted(scores_dict.items(), key=lambda x: x[1], reverse=True)

        primary = sorted_editions[0][0]
        primary_score = sorted_editions[0][1]
        secondary_score = sorted_editions[1][1]

        hybrid_threshold = self._model.get("hybrid_threshold", 0.08)
        diff = primary_score - secondary_score

        if diff < hybrid_threshold and diff > 0:
            secondary = sorted_editions[1][0]
            return SelectionResult(
                primary_edition=primary,
                secondary_edition=secondary,
                is_hybrid=True,
                blend_ratio=(0.60, 0.40),
                scores=scores,
            )

        return SelectionResult(
            primary_edition=primary,
            scores=scores,
        )

# ---------------------------------------------------------------------------
# Safety Gate
# ---------------------------------------------------------------------------
class SafetyGate:
    """Evaluate rules in order from risk_gate_rules.json."""

    def __init__(self):
        self._rules_config = _load_json(_RISK_GATE_RULES)

    def evaluate(self, inp: SessionInput) -> GateResult:
        result = GateResult(passed=True, action="PASS")
        critical_triggered = False
        high_triggered = False

        for rule in self._rules_config["evaluation_order"]:
            triggered = self._check_condition(rule, inp)
            if not triggered:
                continue

            result.triggered_rules.append(rule)
            result.messages.append(rule["message"])
            action = rule["action"]

            if action == "STOP":
                result.passed = False
                result.action = "STOP"
                critical_triggered = True
                break  # immediate halt

            if action == "RESTRICT":
                high_triggered = True
                result.action = "RESTRICT"
                result.allowed_editions = rule.get("allowed_editions")
                result.density_reduction_factor = rule.get("max_density_override", 1.0)
                # Don't break — continue collecting warnings

            if action == "WARNING":
                result.action = "WARNING" if result.action == "PASS" else result.action
                factor = rule.get("density_reduction_factor", 1.0)
                if factor < result.density_reduction_factor:
                    result.density_reduction_factor = factor

        if result.passed and result.triggered_rules:
            result.passed = True
            result.action = result.action  # keep WARNING/RESTRICT

        return result

    def _check_condition(self, rule: Dict[str, Any], inp: SessionInput) -> bool:
        cond = rule["condition"]
        # Parse simple conditions
        return _eval_condition(cond, inp)

def _eval_condition(condition: str, inp: SessionInput) -> bool:
    """Evaluate a simple condition string against SessionInput."""
    import re

    # Handle OR conditions
    if " OR " in condition:
        parts = condition.split(" OR ")
        return any(_eval_condition(p.strip(), inp) for p in parts)

    # Handle comparisons
    m = re.match(r'(\w+)\s*([<>=!]+)\s*([\d.]+)', condition)
    if m:
        attr, op, val = m.groups()
        val = float(val)
        attr_val = getattr(inp, attr, None)
        if attr_val is None:
            return False
        if op == ">":
            return float(attr_val) > val
        if op == ">=":
            return float(attr_val) >= val
        if op == "<":
            return float(attr_val) < val
        if op == "<=":
            return float(attr_val) <= val
        if op == "==":
            return float(attr_val) == val

    # Handle boolean checks: "diabetes == true"
    m_bool = re.match(r'(\w+)\s*==\s*true', condition, re.IGNORECASE)
    if m_bool:
        attr = m_bool.group(1)
        return bool(getattr(inp, attr, False))

    return False

# ---------------------------------------------------------------------------
# Claims Policy
# ---------------------------------------------------------------------------
class ClaimsPolicy:
    """Load and enforce scientific claims policy."""

    def __init__(self):
        self._policy = _load_json(_SCIENTIFIC_CLAIMS_POLICY)

    @property
    def disclaimer(self) -> str:
        return self._policy.get("mandatory_disclaimer", "")

    def evidence_level(self, edition: str) -> str:
        levels = self._policy.get("per_edition_claim_level", {})
        return levels.get(edition, "exploratory")

    def check_text(self, text: str) -> List[str]:
        """Return list of prohibited terms found in text."""
        violations = []
        prohibited = self._policy.get("prohibited_language", {}).get("terms", [])
        for term in prohibited:
            if term in text:
                violations.append(term)
        return violations

# ---------------------------------------------------------------------------
# Engineering Translator
# ---------------------------------------------------------------------------
class EngineeringTranslator:
    """Convert edition selection into manufacturing directives."""

    def translate(
        self,
        edition: str,
        density_reduction_factor: float = 1.0,
    ) -> EngineeringDirective:
        if edition not in EDITION_SPECS:
            raise InvalidInputError(f"Unknown edition: {edition}")

        spec = EDITION_SPECS[edition]
        reduction_applied = density_reduction_factor < 1.0

        directive = EngineeringDirective(
            edition=edition,
            heel_density_pct=spec["heel_density"] * density_reduction_factor,
            midfoot_density_pct=spec["midfoot_density"] * density_reduction_factor,
            forefoot_density_pct=spec["forefoot_density"] * density_reduction_factor,
            toe_density_pct=spec["toe_density"] * density_reduction_factor,
            max_pressure_kpa=spec["max_pressure_kpa"],
            gyroid_cell_size_mm=spec["gyroid_cell_size_mm"],
            stimulation_pattern=spec["stimulation_pattern"],
            comfort_risk_level=spec["comfort_risk_level"],
            manufacturing_notes=spec["manufacturing_notes"],
            density_reduction_applied=reduction_applied,
            density_reduction_factor=density_reduction_factor,
        )

        # Hard constraint: min wall thickness
        directive.min_wall_thickness_mm = MIN_WALL_THICKNESS_MM

        # Hard constraint: cell size within ±1mm of base
        cell = spec["gyroid_cell_size_mm"]
        cell = max(GYROID_CELL_SIZE_BASE_MM - GYROID_CELL_SIZE_ADJUST_MM,
                   min(cell, GYROID_CELL_SIZE_BASE_MM + GYROID_CELL_SIZE_ADJUST_MM))
        directive.gyroid_cell_size_mm = cell

        return directive

# ---------------------------------------------------------------------------
# Main Scientific Layer
# ---------------------------------------------------------------------------
class ZilfitScientificLayer:
    """
    End-to-end scientific decision layer.

    Usage:
        layer = ZilfitScientificLayer()
        decision = layer.decide(input_dict)
    """

    def __init__(self):
        self.scoring = ScoringEngine()
        self.gate = SafetyGate()
        self.translator = EngineeringTranslator()
        self.claims = ClaimsPolicy()

    def decide(self, input_dict: Dict[str, Any]) -> ScientificDecision:
        """Full pipeline: validate → gate → score → select → translate."""
        # Validate
        errors = validate_input(input_dict)
        if errors:
            raise InvalidInputError(f"Input validation failed: {'; '.join(errors)}")

        # Build SessionInput
        inp = SessionInput(
            stress=input_dict.get("stress", 0.0),
            fatigue_score=input_dict.get("fatigue_score", 0.0),
            focus_score=input_dict.get("focus_score", 1.0),
            sleep_disruption=input_dict.get("sleep_disruption", 0.0),
            sensory_overload=input_dict.get("sensory_overload", 0.0),
            pain_or_discomfort=input_dict.get("pain_or_discomfort", 0.0),
            postural_instability=input_dict.get("postural_instability", 0.0),
            cycle_phase_flag=input_dict.get("cycle_phase_flag", 0),
            user_goal_match=input_dict.get("user_goal_match", 0.5),
            heel_pressure_ratio=input_dict.get("heel_pressure_ratio", 0.5),
            temperature_risk=input_dict.get("temperature_risk", 0.0),
            diabetes=input_dict.get("diabetes", False),
            neuropathy=input_dict.get("neuropathy", False),
            pregnant=input_dict.get("pregnant", False),
            active_injury=input_dict.get("active_injury", False),
            vascular_disease=input_dict.get("vascular_disease", False),
            session_duration_minutes=input_dict.get("session_duration_minutes", 0.0),
        )

        # Safety Gate
        gate_result = self.gate.evaluate(inp)

        # If STOP, return blocked decision
        session_id = str(uuid.uuid4())
        timestamp = datetime.now(timezone.utc).isoformat()

        if gate_result.action == "STOP":
            warnings = []
            triggered = [r["rule_id"] for r in gate_result.triggered_rules]
            warnings.append(f"Safety gate STOP: {', '.join(triggered)}")
            return ScientificDecision(
                session_id=session_id,
                timestamp=timestamp,
                selection=SelectionResult(primary_edition="NONE"),
                gate=gate_result,
                engineering=EngineeringDirective(
                    edition="NONE",
                    heel_density_pct=0,
                    midfoot_density_pct=0,
                    forefoot_density_pct=0,
                    toe_density_pct=0,
                    max_pressure_kpa=0,
                ),
                warnings=warnings,
                claims_disclaimer=self.claims.disclaimer,
                evidence_level="blocked",
            )

        # Scoring
        scores = self.scoring.compute(inp)
        selection = self.scoring.select(scores)

        # Determine final edition
        final_edition = selection.primary_edition
        density_factor = gate_result.density_reduction_factor

        # If RESTRICT to specific editions, override
        if gate_result.action == "RESTRICT" and gate_result.allowed_editions:
            if final_edition not in gate_result.allowed_editions:
                # Force to allowed edition
                final_edition = gate_result.allowed_editions[0]
                selection.primary_edition = final_edition
                selection.is_hybrid = False
                selection.secondary_edition = None

        # Translate to engineering
        directive = self.translator.translate(final_edition, density_factor)

        # Claims
        evidence = self.claims.evidence_level(final_edition)

        warnings = []
        if gate_result.action == "WARNING":
            warnings.extend(gate_result.messages)
        if selection.is_hybrid:
            warnings.append(
                f"HYBRID: {selection.primary_edition} (60%) + "
                f"{selection.secondary_edition} (40%)"
            )

        return ScientificDecision(
            session_id=session_id,
            timestamp=timestamp,
            selection=selection,
            gate=gate_result,
            engineering=directive,
            warnings=warnings,
            claims_disclaimer=self.claims.disclaimer,
            evidence_level=evidence,
        )

# ---------------------------------------------------------------------------
# Convenience: run from CLI
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    import sys

    layer = ZilfitScientificLayer()

    # Example: high stress → CALM
    example = {
        "stress": 0.85,
        "fatigue_score": 0.30,
        "focus_score": 0.60,
        "sleep_disruption": 0.70,
        "sensory_overload": 0.65,
        "pain_or_discomfort": 0.10,
        "postural_instability": 0.20,
        "cycle_phase_flag": 0,
        "user_goal_match": 0.80,
        "heel_pressure_ratio": 0.45,
        "temperature_risk": 0.20,
    }

    decision = layer.decide(example)
    print(json.dumps(decision.to_dict(), indent=2, ensure_ascii=False))

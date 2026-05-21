#!/usr/bin/env python3
"""
ZILFIT Edition Selector — Emotion-Informed Edition Recommendation
================================================================
Engineering weighted-scoring selector that maps user state to a ZILFIT edition.
Reads emotional_recipe.json and solar_plexus_map.json for all scoring rules.
NO network, NO API, NO auth — deterministic stdlib only.
Engineering simulation input only — NO MEDICAL CLAIMS.
"""

import json
import sys
from pathlib import Path
from dataclasses import dataclass, field
from typing import Optional

PROJ_ROOT = Path(__file__).resolve().parent.parent
EMOTIONAL_RECIPE_PATH = PROJ_ROOT / "editions" / "emotion_layer" / "emotional_recipe.json"
SOLAR_PLEXUS_PATH = PROJ_ROOT / "editions" / "emotion_layer" / "solar_plexus_map.json"

# ──────────────────────────────────────────────────────────────────────
# Data structures
# ──────────────────────────────────────────────────────────────────────

@dataclass
class UserProfile:
    stress_level: float                        # 0.0 – 1.0
    fatigue_level: float                       # 0.0 – 1.0 (maps to fatigue_level_1_to_10 / 10)
    sensory_sensitivity: float                 # 0.0 – 1.0 (low → can handle intense stimulation)
    balance_instability: float                 # 0.0 – 1.0
    recovery_need: float                       # 0.0 – 1.0 (post-exertion recovery demand)
    emotional_state: str                       # one of the keywords defined per edition
    foot_pressure_profile: str                 # "flat_arch" | "neutral_arch" | "high_arch"
    arch_type: str                             # same as above — legacy alias
    gait_pattern: str                          # e.g. "normal", "overpronation", "supination", "female_q_angle"
    biomechanics_context: Optional[str] = None # extra context: "female" | "athletic" | "elderly" | None

@dataclass
class EditionRecommendation:
    recommended_edition: str
    confidence_score: float                    # 0.0 – 1.0
    primary_zones: list                        # zone IDs from solar_plexus_map
    stimulation_profile: dict                  # type, frequency_hz, intensity, coverage_percent, description
    recommended_density: dict                  # heel, midfoot, forefoot, toe
    emotional_target: str
    warnings: list
    reasoning: str                             # text explanation
    second_edition: Optional[str] = None       # hybrid edition support
    second_weight: float = 0.0                 # secondary weight (0.0 = pure single edition)

# ──────────────────────────────────────────────────────────────────────
# Edition signal keywords (maps emotional_state to edition affinity)
# ──────────────────────────────────────────────────────────────────────

EDITION_AFFINITY = {
    "CALM": {
        "emotional_keywords": ["stress", "tension", "overwhelm", "nervousness",
                               "need_grounding", "need_calm", "anxious"],
        "activity_keywords": ["rest", "stationary", "desk", "office", "reading"],
    },
    "VITAL": {
        "emotional_keywords": ["post_exertion", "heavy_fatigue", "drained",
                               "muscle_heavy", "need_decompression", "exhausted", "athletic_recovery"],
        "activity_keywords": ["after_match", "after_training", "after_running",
                              "post_exertion", "gym_recovery", "heavy_standing"],
    },
    "FOCUS": {
        "emotional_keywords": ["mental_fog", "distraction", "low_alertness",
                               "need_clarity", "toe_heaviness", "need_focus"],
        "activity_keywords": ["active_walk", "work_focused"],
    },
    "BALANCE": {
        "emotional_keywords": ["instability", "confidence_needed", "uneven_weight",
                               "lateral_tilt", "standing_uncertainty"],
        "activity_keywords": ["long_standing", "walking_elderly", "rehabilitation"],
    },
    "FEMME": {
        "emotional_keywords": ["female_comfort_priority", "pelvis_alignment_concern",
                               "q_angle_sensitivity", "forefoot_width_pressure",
                               "emotional_soothing"],
        "activity_keywords": [],  # detected via biomechanics_context
    },
}

# ──────────────────────────────────────────────────────────────────────
# Scoring engine
# ──────────────────────────────────────────────────────────────────────

def _emotional_match(user: UserProfile, edition: str) -> float:
    """Return 0.0-1.0 how well user's emotional_state matches edition keywords."""
    affinity = EDITION_AFFINITY[edition]
    all_keywords = affinity["emotional_keywords"] + affinity["activity_keywords"]
    state = user.emotional_state.lower().strip()

    # Exact keyword match
    if state in [k.lower() for k in all_keywords]:
        return 1.0

    # Partial match (substring in keyword or keyword in state)
    best = 0.0
    for kw in all_keywords:
        kw_low = kw.lower()
        if kw_low in state or state in kw_low:
            best = max(best, 0.7)
        # word-level partial
        for word in state.split():
            if word in kw_low or kw_low in word:
                best = max(best, 0.5)
    return best


def _dimensional_score(user: UserProfile, edition: str) -> float:
    """Score based on dimensional inputs (stress, fatigue, etc.)."""
    if edition == "CALM":
        # CALM likes high stress, low fatigue, high sensory sensitivity
        return 0.35 * user.stress_level + 0.10 * (1.0 - user.fatigue_level) + \
               0.25 * user.sensory_sensitivity + 0.10 * (1.0 - user.recovery_need) + \
               0.20 * (1.0 - user.balance_instability)

    elif edition == "VITAL":
        # VITAL likes high fatigue, high recovery_need
        return 0.10 * user.stress_level + 0.35 * user.fatigue_level + \
               0.15 * (1.0 - user.sensory_sensitivity) + 0.10 * (1.0 - user.balance_instability) + \
               0.30 * user.recovery_need

    elif edition == "FOCUS":
        # FOCUS likes low-medium stress, low fatigue, low sensory sensitivity (can handle stimulation)
        return 0.15 * (1.0 - user.stress_level) + 0.20 * (1.0 - user.fatigue_level) + \
               0.25 * (1.0 - user.sensory_sensitivity) + 0.15 * (1.0 - user.recovery_need) + \
               0.25 * (1.0 - user.balance_instability)

    elif edition == "BALANCE":
        # BALANCE likes high instability, low-medium fatigue
        return 0.05 * user.stress_level + 0.15 * user.fatigue_level + \
               0.10 * user.sensory_sensitivity + 0.45 * user.balance_instability + \
               0.25 * (1.0 - user.recovery_need)

    elif edition == "FEMME":
        # FEMME: biomechanics_context is the strong predictor
        bio_match = 1.0 if user.biomechanics_context == "female" else 0.3
        # secondary: femme-specific gait pattern
        gait_match = 1.0 if user.gait_pattern in ("female_q_angle", "overpronation") else 0.4
        return 0.30 * user.stress_level + 0.15 * user.fatigue_level + \
               0.10 * user.sensory_sensitivity + 0.05 * user.balance_instability + \
               0.10 * user.recovery_need + 0.20 * bio_match + 0.10 * gait_match

    return 0.0


def _compute_scoring(editions_map: dict, user: UserProfile) -> dict:
    """Return dict of edition_name -> combined_score (0.0-1.0)."""
    scores = {}
    weights = {"emotional": 0.45, "dimensional": 0.55}

    for edition_name in editions_map["editions"].keys():
        emo_score = _emotional_match(user, edition_name)
        dim_score = _dimensional_score(user, edition_name)
        combined = weights["emotional"] * emo_score + weights["dimensional"] * dim_score
        scores[edition_name] = min(combined, 1.0)

    return scores


# ──────────────────────────────────────────────────────────────────────
# Hybrid detection
# ──────────────────────────────────────────────────────────────────────

_HYBRID_THRESHOLD = 0.15  # if second-best is within 15% of best, consider hybrid


def _detect_hybrid(scores: dict, recipe: dict) -> tuple:
    """Return (primary, secondary, secondary_weight) or (primary, None, 0.0)."""
    sorted_scores = sorted(scores.items(), key=lambda x: x[1], reverse=True)
    primary, primary_score = sorted_scores[0]
    if len(sorted_scores) < 2:
        return primary, None, 0.0

    secondary, secondary_score = sorted_scores[1]
    if primary_score - secondary_score < _HYBRID_THRESHOLD:
        # The closer they are, the more weight to secondary
        gap = primary_score - secondary_score
        secondary_weight = round(0.4 * (1.0 - gap / _HYBRID_THRESHOLD), 2)
        secondary_weight = max(secondary_weight, 0.15)
        return primary, secondary, secondary_weight

    return primary, None, 0.0


def _blend_densities(primary_edition: str, secondary_edition: Optional[str],
                     secondary_weight: float, recipe: dict) -> dict:
    """Blend density maps per cross_edition_rules formula."""
    primary_data = recipe["editions"][primary_edition]
    primary_density = primary_data["foot_zones"]

    if not secondary_edition or secondary_weight == 0.0:
        return {z: primary_density[z]["density"] for z in primary_density}

    secondary_data = recipe["editions"][secondary_edition]
    secondary_density = secondary_data["foot_zones"]

    blended = {}
    primary_weight = 1.0 - secondary_weight
    all_zones = set(primary_density.keys()) | set(secondary_density.keys())
    for zone in all_zones:
        p = primary_density.get(zone, {"density": 0.30})["density"]
        s = secondary_density.get(zone, {"density": 0.30})["density"]
        blended[zone] = round(p * primary_weight + s * secondary_weight, 3)

    return blended


def _blend_stimulation(primary_edition: str, secondary_edition: Optional[str],
                       secondary_weight: float, recipe: dict) -> dict:
    """Use the HIGHER intensity profile between two editions."""
    primary_data = recipe["editions"][primary_edition]["stimulation_profile"]

    if not secondary_edition or secondary_weight == 0.0:
        return primary_data

    secondary_data = recipe["editions"][secondary_edition]["stimulation_profile"]

    intensity_order = {"low": 0, "low_medium": 1, "medium": 2, "medium_high": 3, "high": 4}
    p_int = intensity_order.get(primary_data.get("intensity", "low"), 0)
    s_int = intensity_order.get(secondary_data.get("intensity", "low"), 0)

    # Higher intensity wins, blend frequency
    winner = primary_data if p_int >= s_int else secondary_data
    blended = dict(winner)
    blended["frequency_hz"] = round(
        primary_data.get("frequency_hz", 0) * (1 - secondary_weight) +
        secondary_data.get("frequency_hz", 0) * secondary_weight, 1
    )
    return blended


# ──────────────────────────────────────────────────────────────────────
# Warnings generation
# ──────────────────────────────────────────────────────────────────────

def _generate_warnings(user: UserProfile, edition: str, recipe: dict) -> list:
    """Generate safety warnings based on user profile + edition."""
    warnings = []
    edition_data = recipe["editions"].get(edition, {})

    # Fatigue redirection
    if edition == "CALM" and user.fatigue_level >= 0.6:
        warnings.append(
            "High fatigue detected (>=0.6). CALM alone may be insufficient — "
            "consider VITAL secondary edition for post-exertion recovery."
        )

    if edition == "FOCUS" and user.fatigue_level >= 0.6:
        warnings.append(
            "High fatigue detected (>=0.6). FOCUS not intended for post-exertion recovery — "
            "redirect to VITAL if user reports muscle heaviness."
        )

    # Sensory overload
    if edition == "FOCUS" and user.sensory_sensitivity >= 0.7:
        warnings.append(
            "High sensory sensitivity may make FOCUS stimulation feel too intense — "
            "consider reducing forefoot stimulation or adding CALM as secondary."
        )

    # Low weight + BALANCE rigidity
    if edition == "BALANCE" and user.fatigue_level < 0.2:
        warnings.append(
            "BALANCE uses uniform 0.50 density — may feel firm for low-fatigue users. "
            "Z-Physics should verify comfort at this density."
        )

    # FEMME biomechanics
    if edition == "FEMME" and user.biomechanics_context != "female":
        warnings.append(
            "FEMME edition selected without 'female' biomechanics_context. "
            "Verify user intent or consider another edition."
        )

    # Edition-specific safety flags
    for flag in edition_data.get("safety_flags", []):
        warnings.append(f"[{edition}] {flag}")

    return warnings


# ──────────────────────────────────────────────────────────────────────
# Reasoning text
# ──────────────────────────────────────────────────────────────────────

def _build_reasoning(primary: str, secondary: Optional[str],
                     secondary_weight: float, scores: dict, user: UserProfile) -> str:
    parts = []
    parts.append(
        f"Primary edition {primary} scored {scores[primary]:.3f} based on "
        f"stress={user.stress_level:.2f}, fatigue={user.fatigue_level:.2f}, "
        f"sensory={user.sensory_sensitivity:.2f}, balance={user.balance_instability:.2f}, "
        f"recovery={user.recovery_need:.2f}."
    )
    if secondary:
        parts.append(
            f"Secondary edition {secondary} scored {scores[secondary]:.3f}, "
            f"within hybrid threshold — blended at {secondary_weight:.0%} weight."
        )
    if user.biomechanics_context == "female":
        parts.append("Female biomechanics context detected — FEMME edition prioritized.")
    if user.emotional_state:
        emo_match = any(
            user.emotional_state.lower() in [k.lower() for k in v["emotional_keywords"] + v["activity_keywords"]]
            for v in EDITION_AFFINITY.values()
        )
        if emo_match:
            parts.append(f"Emotional state '{user.emotional_state}' matched edition affinity keywords.")

    return " ".join(parts)


# ──────────────────────────────────────────────────────────────────────
# Main selector function
# ──────────────────────────────────────────────────────────────────────

def select_edition(
    stress_level: float,
    fatigue_level: float,
    sensory_sensitivity: float,
    balance_instability: float,
    recovery_need: float,
    emotional_state: str,
    foot_pressure_profile: str = "neutral_arch",
    arch_type: str = "neutral_arch",
    gait_pattern: str = "normal",
    biomechanics_context: Optional[str] = None,
) -> EditionRecommendation:
    """
    Select the best ZILFIT edition for a given user state.

    Returns EditionRecommendation with edition, confidence, zones,
    stimulation profile, density, emotional target, warnings, and reasoning.
    Safe wording only — no medical claims.
    """
    # Validate input ranges
    for name, val in [("stress_level", stress_level), ("fatigue_level", fatigue_level),
                      ("sensory_sensitivity", sensory_sensitivity),
                      ("balance_instability", balance_instability),
                      ("recovery_need", recovery_need)]:
        if not 0.0 <= val <= 1.0:
            raise ValueError(f"{name} must be 0.0-1.0, got {val}")

    # Load recipe and map
    with open(EMOTIONAL_RECIPE_PATH) as f:
        recipe = json.load(f)
    with open(SOLAR_PLEXUS_PATH) as f:
        sp_map = json.load(f)

    user = UserProfile(
        stress_level=stress_level,
        fatigue_level=fatigue_level,
        sensory_sensitivity=sensory_sensitivity,
        balance_instability=balance_instability,
        recovery_need=recovery_need,
        emotional_state=emotional_state,
        foot_pressure_profile=foot_pressure_profile,
        arch_type=arch_type,
        gait_pattern=gait_pattern,
        biomechanics_context=biomechanics_context,
    )

    # Score all editions
    scores = _compute_scoring(recipe, user)

    # Detect hybrid
    primary, secondary, sec_weight = _detect_hybrid(scores, recipe)

    # Get edition data from recipe
    edition_data = recipe["editions"][primary]

    # Primary zones
    sp_edition_data = sp_map["editions"].get(primary.lower(), {})
    primary_zones = sp_edition_data.get("active_zones", [])

    # Stimulation profile (blend if hybrid)
    stim = _blend_stimulation(primary, secondary, sec_weight, recipe)

    # Density map (blend if hybrid)
    density = _blend_densities(primary, secondary, sec_weight, recipe)

    # Emotional target
    emotional_target = sp_edition_data.get("primary_emotion_target", edition_data.get("intended_effect", "comfort"))

    # Warnings
    warnings = _generate_warnings(user, primary, recipe)
    if secondary:
        warnings.extend(_generate_warnings(user, secondary, recipe))

    # Reasoning
    reasoning = _build_reasoning(primary, secondary, sec_weight, scores, user)

    # Confidence: scaled from the primary score with a floor
    confidence = max(scores[primary], 0.3)

    return EditionRecommendation(
        recommended_edition=primary,
        confidence_score=round(confidence, 3),
        primary_zones=primary_zones,
        stimulation_profile=stim,
        recommended_density=density,
        emotional_target=emotional_target,
        warnings=warnings,
        reasoning=reasoning,
        second_edition=secondary,
        second_weight=sec_weight,
    )


def recommendation_to_dict(rec: EditionRecommendation) -> dict:
    """Convert EditionRecommendation to a JSON-serializable dict."""
    return {
        "recommended_edition": rec.recommended_edition,
        "confidence_score": rec.confidence_score,
        "primary_zones": rec.primary_zones,
        "stimulation_profile": rec.stimulation_profile,
        "recommended_density": rec.recommended_density,
        "emotional_target": rec.emotional_target,
        "warnings": rec.warnings,
        "reasoning": rec.reasoning,
        "second_edition": rec.second_edition,
        "second_weight": rec.second_weight,
    }


# ──────────────────────────────────────────────────────────────────────
# CLI entry point — runs all 5 test profiles
# ──────────────────────────────────────────────────────────────────────

def _run_demo():
    profiles = {
        "anxious_office_worker": {
            "stress_level": 0.75,
            "fatigue_level": 0.30,
            "sensory_sensitivity": 0.80,
            "balance_instability": 0.10,
            "recovery_need": 0.20,
            "emotional_state": "stress",
            "foot_pressure_profile": "neutral_arch",
            "arch_type": "neutral_arch",
            "gait_pattern": "normal",
            "biomechanics_context": None,
        },
        "athlete_recovery": {
            "stress_level": 0.15,
            "fatigue_level": 0.85,
            "sensory_sensitivity": 0.30,
            "balance_instability": 0.10,
            "recovery_need": 0.90,
            "emotional_state": "post_exertion",
            "foot_pressure_profile": "high_arch",
            "arch_type": "high_arch",
            "gait_pattern": "normal",
            "biomechanics_context": "athletic",
        },
        "sensory_overload_worker": {
            "stress_level": 0.60,
            "fatigue_level": 0.45,
            "sensory_sensitivity": 0.85,
            "balance_instability": 0.15,
            "recovery_need": 0.25,
            "emotional_state": "mental_fog",
            "foot_pressure_profile": "flat_arch",
            "arch_type": "flat_arch",
            "gait_pattern": "overpronation",
            "biomechanics_context": None,
        },
        "elderly_balance_support": {
            "stress_level": 0.30,
            "fatigue_level": 0.40,
            "sensory_sensitivity": 0.50,
            "balance_instability": 0.80,
            "recovery_need": 0.10,
            "emotional_state": "instability",
            "foot_pressure_profile": "flat_arch",
            "arch_type": "flat_arch",
            "gait_pattern": "supination",
            "biomechanics_context": "elderly",
        },
        "femme_biomechanical_fatigue": {
            "stress_level": 0.50,
            "fatigue_level": 0.65,
            "sensory_sensitivity": 0.60,
            "balance_instability": 0.35,
            "recovery_need": 0.55,
            "emotional_state": "q_angle_sensitivity",
            "foot_pressure_profile": "neutral_arch",
            "arch_type": "neutral_arch",
            "gait_pattern": "female_q_angle",
            "biomechanics_context": "female",
        },
    }

    results = {}
    for name, params in profiles.items():
        rec = select_edition(**params)
        results[name] = {
            "profile": params,
            "recommendation": recommendation_to_dict(rec),
        }

    print(json.dumps(results, indent=2, ensure_ascii=False))
    return results


if __name__ == "__main__":
    _run_demo()

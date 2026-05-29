#!/usr/bin/env python3
"""Adaptive Geometry Rules Engine — converts gait metrics to sole design parameters.

Deterministic rules layer. No ML. Every design decision is traceable to
a numeric input signal.

Inputs:  pressure_balance, roll_angle, fatigue_signal, steps, foot_type
Outputs: heel_cushion_level, arch_support_level, medial_support_bias,
         lateral_support_bias, flexibility_score, fatigue_adjustment,
         next_revision_notes
"""

import math
from typing import Dict, Optional

VALID_FOOT_TYPES = {"normal", "low_arch_geometric", "high_arch_geometric"}

NON_CLINICAL_DISCLAIMER = (
    "All geometry parameters are engineering design values. They do not "
    "constitute medical advice, treatment prescription, or diagnostic "
    "recommendation. For engineering evaluation only."
)


def _clamp(value: float, lo: float, hi: float) -> float:
    return max(lo, min(hi, value))


def compute_geometry(
    pressure_balance: float,
    roll_angle: float,
    fatigue_signal: float,
    steps: int,
    foot_type: str,
    mode: str = "private_tester",
    doctor_overrides: Optional[dict] = None,
) -> dict:
    """Compute adaptive sole geometry parameters from gait metrics.

    Args:
        pressure_balance: Rearfoot/forefoot pressure ratio (0.3–3.0).
        roll_angle: Medial-lateral roll during stance in degrees.
        fatigue_signal: Gait symmetry drift as percentage (0–30).
        steps: Total steps in session.
        foot_type: normal, low_arch_geometric, or high_arch_geometric.
        mode: "private_tester" (auto) or "doctor_override" (manual).
        doctor_overrides: Dict of manual overrides when mode="doctor_override".

    Returns:
        Dict of geometry parameters + revision notes + disclaimer.
    """
    if mode == "doctor_override" and doctor_overrides:
        result = {
            "heel_cushion_level": doctor_overrides.get("heel_cushion_override", 3),
            "arch_support_level": doctor_overrides.get("arch_support_override", 3),
            "medial_support_bias": doctor_overrides.get("medial_bias_override", 50),
            "lateral_support_bias": doctor_overrides.get("lateral_bias_override", 50),
            "flexibility_score": doctor_overrides.get("flexibility_override", 3),
            "fatigue_adjustment": min(fatigue_signal * 1.2, 30),
            "next_revision_notes": doctor_overrides.get(
                "doctor_notes", "Doctor override active — manual geometry applied."
            ),
            "mode": "doctor_override",
            "non_clinical_disclaimer": NON_CLINICAL_DISCLAIMER,
        }
        return result

    if foot_type not in VALID_FOOT_TYPES:
        raise ValueError(f"foot_type must be one of {VALID_FOOT_TYPES}")

    # Heel cushioning: pressure_balance < 0.7 = heel-heavy, > 1.5 = forefoot-heavy
    heel_cushion = round(_clamp(3.5 - pressure_balance, 1, 5))

    # Arch support: base 3, adjusted by foot type
    arch_support = 3
    if foot_type == "low_arch_geometric":
        arch_support -= 1
    elif foot_type == "high_arch_geometric":
        arch_support += 1

    # Flexibility: long sessions = softer
    flexibility = 3
    if steps > 3000:
        flexibility -= 1  # lower number = more flexible

    # Medial/lateral bias from roll angle
    abs_roll = abs(roll_angle)
    bias_delta = _clamp(abs_roll * 6.0, 0, 50)

    if abs_roll < 3.0:
        medial_bias = 50
        lateral_bias = 50
    elif roll_angle > 0:
        medial_bias = _clamp(50 + bias_delta, 0, 100)
        lateral_bias = _clamp(50 - bias_delta, 0, 100)
    else:
        medial_bias = _clamp(50 - bias_delta, 0, 100)
        lateral_bias = _clamp(50 + bias_delta, 0, 100)

    # Fatigue adjustment
    fatigue_adj = _clamp(fatigue_signal * 1.2, 0, 30)

    if fatigue_adj > 15:
        heel_cushion = _clamp(heel_cushion + 1, 1, 5)
        flexibility = _clamp(flexibility + 1, 1, 5)
        arch_support = _clamp(arch_support + 1, 1, 5)

    # Round and clamp final
    heel_cushion = int(_clamp(heel_cushion, 1, 5))
    arch_support = int(_clamp(arch_support, 1, 5))
    flexibility = int(_clamp(flexibility, 1, 5))
    medial_bias = round(medial_bias)
    lateral_bias = round(lateral_bias)
    fatigue_adj = round(fatigue_adj, 1)

    # Next revision notes
    notes = _generate_notes(
        pressure_balance, roll_angle, fatigue_signal, steps, foot_type,
        heel_cushion, arch_support, medial_bias, lateral_bias, flexibility,
        fatigue_adj,
    )

    return {
        "heel_cushion_level": heel_cushion,
        "arch_support_level": arch_support,
        "medial_support_bias": medial_bias,
        "lateral_support_bias": lateral_bias,
        "flexibility_score": flexibility,
        "fatigue_adjustment": fatigue_adj,
        "next_revision_notes": notes,
        "mode": mode,
        "non_clinical_disclaimer": NON_CLINICAL_DISCLAIMER,
    }


def _generate_notes(
    pressure_balance, roll_angle, fatigue_signal, steps, foot_type,
    heel, arch, medial, lateral, flex, fatigue_adj,
) -> str:
    parts = []

    if pressure_balance < 0.7:
        parts.append("Heel-dominant pressure pattern — increased heel cushioning")
    elif pressure_balance > 1.5:
        parts.append("Forefoot-dominant pressure pattern — reduced heel cushioning, increased forefoot cushioning")
    else:
        parts.append("Balanced pressure distribution")

    if foot_type == "low_arch_geometric":
        parts.append("Low geometric arch — reduced arch support density")
    elif foot_type == "high_arch_geometric":
        parts.append("High geometric arch — increased arch support density")

    if abs(roll_angle) >= 3.0:
        direction = "medial" if roll_angle > 0 else "lateral"
        parts.append(f"Significant roll toward {direction} side ({roll_angle:.1f}°) — {direction} bias applied")

    if fatigue_signal > 8.0:
        parts.append(f"Fatigue signal {fatigue_signal:.1f}% — softened density and added arch support")

    if steps > 3000:
        parts.append("Long session — increased forefoot flexibility")

    if not parts:
        parts.append("Within baseline — no geometry changes needed")

    parts.append(
        f"Next: validate {heel=} {arch=} {medial=} {lateral=} {flex=} fadj={fatigue_adj} "
        "with coupon test before production"
    )
    return "; ".join(parts)

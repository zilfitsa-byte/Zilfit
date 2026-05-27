#!/usr/bin/env python3
"""Parametric Geometry Profile Generator — converts runtime session into explicit geometry config.

Input: runtime session JSON
Output: geometry profile JSON containing heel cup, arch curve, flex channels,
        lattice density map, wall strengths, print orientation, comfort/support priorities.

All values are engineering design parameters. No mesh generation.
"""

import json
import math
from typing import Dict, Optional


def _clamp(v: float, lo: float, hi: float) -> float:
    return max(lo, min(hi, v))


def _sigmoid(x: float) -> float:
    return 1.0 / (1.0 + math.exp(-x))


def generate_geometry_profile(session: dict) -> dict:
    """Generate a full geometry profile from a runtime session record.

    Args:
        session: Dict matching zilfit_session_schema_v1.json.

    Returns:
        Dict with all geometry parameters for CAD / slicing.
    """
    features = session.get("geometric_features", {})
    adaptive = session.get("adaptive_geometry", {})
    capsule = session.get("capsule_analysis", {})
    clf = session.get("classification", {})
    pp = session.get("print_profile", {})

    # Extract key values
    foot_length = features.get("foot_length_mm", 260)
    foot_width = features.get("foot_width_mm", 80)
    heel_width = features.get("heel_width_mm", 60)
    arch_height_geo = features.get("arch_height_geometric_mm", 15)

    heel_level = adaptive.get("heel_cushion_level", 3)
    arch_level = adaptive.get("arch_support_level", 3)
    medial_bias = adaptive.get("medial_support_bias", 50)
    lateral_bias = adaptive.get("lateral_support_bias", 50)
    flex_score = adaptive.get("flexibility_score", 3)
    fatigue_adj = adaptive.get("fatigue_adjustment", 0)

    pressure_balance = capsule.get("pressure_balance", 1.0)
    roll_angle = capsule.get("roll_angle_deg", 0)
    foot_type = clf.get("predicted_class", "normal")

    # -----------------------------------------------------------------------
    # Heel Cup
    # -----------------------------------------------------------------------
    heel_cup_depth = _clamp(8 + heel_level * 2, 8, 20)
    if fatigue_adj > 15:
        heel_cup_depth = _clamp(heel_cup_depth + 2, 8, 20)
    heel_cup_radius = heel_width * 0.45
    heel_cup_wall_angle_deg = 75
    heel_cup_fillet_radius = 15.0

    # -----------------------------------------------------------------------
    # Arch Support
    # -----------------------------------------------------------------------
    arch_curve_height = arch_height_geo * 0.7 * (arch_level / 3.0)
    if foot_type == "low_arch_geometric":
        arch_curve_height *= 0.6
    elif foot_type == "high_arch_geometric":
        arch_curve_height *= 1.3
    arch_contact_length = foot_length * 0.15
    arch_curve_radius = foot_length * 0.4

    # -----------------------------------------------------------------------
    # Medial / Lateral Walls
    # -----------------------------------------------------------------------
    medial_strength = 1 + (medial_bias / 25.0)
    lateral_strength = 1 + (lateral_bias / 25.0)

    base_thickness = 2.0
    medial_thickness = base_thickness + (medial_strength * 0.8)
    lateral_thickness = base_thickness + (lateral_strength * 0.8)
    wall_height = 15.0
    wall_rim_thickness = 1.5

    # -----------------------------------------------------------------------
    # Forefoot Flex Channels
    # -----------------------------------------------------------------------
    flex_channel_count = flex_score
    forefoot_length = foot_length * 0.25
    flex_channel_depth = 1.5 + (flex_score * 0.5)
    flex_channel_spacing = forefoot_length / (flex_channel_count + 1) if flex_channel_count > 0 else 0

    # -----------------------------------------------------------------------
    # Lattice Density Map (zone-level)
    # -----------------------------------------------------------------------
    density_zones = pp.get("density_zones", {})
    heel_density = density_zones.get("heel", 0.33)
    arch_density = density_zones.get("arch", 0.32)
    midfoot_density = density_zones.get("midfoot", 0.28)
    forefoot_density = density_zones.get("forefoot", 0.32)
    toes_density = density_zones.get("toes", 0.26)

    # Apply fatigue softening
    if fatigue_adj > 0:
        soften = 1.0 - (fatigue_adj / 200.0)
        heel_density = round(heel_density * soften, 3)
        arch_density = round(arch_density * soften, 3)
        midfoot_density = round(midfoot_density * soften, 3)
        forefoot_density = round(forefoot_density * soften, 3)
        toes_density = round(toes_density * soften, 3)

    # Cell sizes per zone (tighter = higher density)
    cell_sizes = {
        "heel": round(_clamp(8.0 - heel_density * 10, 4.0, 8.0), 2),
        "arch": round(_clamp(8.0 - arch_density * 10, 4.0, 8.0), 2),
        "midfoot": round(_clamp(10.0 - midfoot_density * 12, 5.0, 10.0), 2),
        "forefoot": round(_clamp(8.0 - forefoot_density * 10, 4.0, 8.0), 2),
        "toes": round(_clamp(10.0 - toes_density * 12, 5.0, 10.0), 2),
    }

    # Density transitions (gradient caps)
    transitions = []
    zone_order = ["heel", "arch", "midfoot", "forefoot", "toes"]
    for i in range(len(zone_order) - 1):
        a = zone_order[i]
        b = zone_order[i + 1]
        d_a = density_zones.get(a, 0.3)
        d_b = density_zones.get(b, 0.3)
        diff = abs(d_a - d_b)
        transitions.append({
            "from_zone": a,
            "to_zone": b,
            "density_diff": round(diff, 3),
            "blend_length_mm": 5.0 if diff > 0.05 else 0,
            "transition_type": "sigmoid" if diff > 0.05 else "step",
        })

    # -----------------------------------------------------------------------
    # Print Orientation
    # -----------------------------------------------------------------------
    part_height = heel_cup_depth + arch_curve_height + 10  # rough
    total_layers = int(part_height / 0.11)
    print_orientation = "heel_down_toes_up_vertical"

    # -----------------------------------------------------------------------
    # Skin Contact
    # -----------------------------------------------------------------------
    skin_thickness_mm = 1.5
    skin_transition_mm = 3.0
    layer_height_mm = 0.11

    # -----------------------------------------------------------------------
    # Comfort vs Support
    # -----------------------------------------------------------------------
    comfort_priority = 50
    support_priority = 50

    if 0.8 <= pressure_balance <= 1.3 and capsule.get("fatigue_signal_pct", 0) < 5:
        comfort_priority += 20
        support_priority -= 20
    if abs(roll_angle) > 8 or capsule.get("fatigue_signal_pct", 0) > 15:
        support_priority += 20
        comfort_priority -= 20

    comfort_priority = int(_clamp(comfort_priority, 0, 100))
    support_priority = int(_clamp(support_priority, 0, 100))

    # -----------------------------------------------------------------------
    # Outsole
    # -----------------------------------------------------------------------
    outsole_flex_score = flex_score
    outsole_pad_thickness = 3.0
    outsole_contact_zones = ["heel_strike", "lateral_midfoot", "met_heads", "hallux"]

    # -----------------------------------------------------------------------
    # Assemble Profile
    # -----------------------------------------------------------------------
    profile = {
        "profile_id": f"GP-{session.get('session_id', 'UNKNOWN')[-12:]}",
        "source_session": session.get("session_id", ""),
        "generated_utc": session.get("generated_utc", ""),
        "heel_cup": {
            "depth_mm": round(heel_cup_depth, 1),
            "radius_mm": round(heel_cup_radius, 1),
            "wall_angle_deg": heel_cup_wall_angle_deg,
            "fillet_radius_mm": heel_cup_fillet_radius,
        },
        "arch_curve": {
            "height_mm": round(arch_curve_height, 1),
            "contact_length_mm": round(arch_contact_length, 1),
            "longitudinal_radius_mm": round(arch_curve_radius, 1),
        },
        "forefoot_flex": {
            "channel_count": flex_channel_count,
            "channel_depth_mm": round(flex_channel_depth, 1),
            "channel_spacing_mm": round(flex_channel_spacing, 1),
        },
        "walls": {
            "medial": {
                "strength_index": round(medial_strength, 2),
                "thickness_mm": round(medial_thickness, 1),
            },
            "lateral": {
                "strength_index": round(lateral_strength, 2),
                "thickness_mm": round(lateral_thickness, 1),
            },
            "height_mm": wall_height,
            "rim_thickness_mm": wall_rim_thickness,
        },
        "lattice_density_map": {
            "heel": heel_density,
            "arch": arch_density,
            "midfoot": midfoot_density,
            "forefoot": forefoot_density,
            "toes": toes_density,
        },
        "lattice_cell_sizes_mm": cell_sizes,
        "density_transitions": transitions,
        "outsole": {
            "flex_score": outsole_flex_score,
            "pad_thickness_mm": outsole_pad_thickness,
            "contact_zones": outsole_contact_zones,
        },
        "print_strategy": {
            "orientation": print_orientation,
            "layer_height_mm": layer_height_mm,
            "total_layers": total_layers,
            "skin_thickness_mm": skin_thickness_mm,
            "skin_transition_mm": skin_transition_mm,
        },
        "priority_balance": {
            "comfort_priority": comfort_priority,
            "support_priority": support_priority,
            "balance_type": "comfort_dominant" if comfort_priority > 60 else (
                "support_dominant" if support_priority > 60 else "balanced"
            ),
        },
        "manufacturing_constraints": {
            "min_wall_thickness_mm": 0.6,
            "max_overhang_deg": 45,
            "min_cell_size_mm": 3.0,
            "max_cell_size_mm": 12.0,
            "min_density": 0.10,
            "max_density": 0.50,
            "process": "MJF",
            "material": pp.get("material", "TPU_75A_80A"),
        },
        "non_clinical_disclaimer": (
            "All geometry dimensions are engineering values derived from sensor "
            "metrics and classification outputs. No medical or therapeutic "
            "function is claimed. For engineering evaluation only."
        ),
    }

    return profile

#!/usr/bin/env python3
"""Lattice Engine V2 — adaptive 5-zone lattice map from geometry profile.

Produces lattice_outputs/LATTICE_PROFILE_NNN.json containing:
  - Per-zone density, cell_size, stiffness, flex, energy_return
  - Support mode presets (comfort, balanced, sport, recovery)
  - Pressure distribution map
  - Smart Capsule sensor cavity coordinates
  - Density transition protocol
"""

import json
from datetime import datetime, timezone
from typing import Dict, List, Optional, Tuple

ZONE_NAMES = ["heel_impact", "arch_bridge", "midfoot_stabilisation",
              "forefoot_propulsion", "toe_release"]

# Map from lattice zone names to geometry profile zone keys
ZONE_TO_PROFILE_KEY = {
    "heel_impact": "heel",
    "arch_bridge": "arch",
    "midfoot_stabilisation": "midfoot",
    "forefoot_propulsion": "forefoot",
    "toe_release": "toes",
}

ZONE_Y_BOUNDS = {
    "heel_impact": (0.0, 0.20),
    "arch_bridge": (0.20, 0.40),
    "midfoot_stabilisation": (0.40, 0.55),
    "forefoot_propulsion": (0.55, 0.80),
    "toe_release": (0.80, 1.00),
}

SUPPORT_PRESETS = {
    "comfort": {
        "density_shift": -0.03,
        "medial_bias_shift": -10,
        "lateral_bias_shift": 5,
        "description": "Softer density, less corrective medial bias",
    },
    "balanced": {
        "density_shift": 0.0,
        "medial_bias_shift": 0,
        "lateral_bias_shift": 0,
        "description": "Default adaptive output from geometry profile",
    },
    "sport": {
        "density_shift": 0.02,
        "medial_bias_shift": 10,
        "lateral_bias_shift": 5,
        "description": "Firmer density, increased medial support",
    },
    "recovery": {
        "density_shift": -0.02,
        "medial_bias_shift": 5,
        "lateral_bias_shift": -5,
        "description": "Soft density with stability bias for fatigued gait",
    },
}

# Sensor cavity coordinates (fractional XY, depth in mm)
SENSOR_CAVITIES = [
    {
        "id": "heel_sensor",
        "y_frac": 0.08,
        "x_frac": 0.0,
        "diameter_mm": 10.0,
        "depth_mm": 8.0,
        "purpose": "Pressure + IMU",
    },
    {
        "id": "arch_sensor",
        "y_frac": 0.30,
        "x_frac": 0.40,
        "diameter_mm": 10.0,
        "depth_mm": 8.0,
        "purpose": "Pressure + temperature",
    },
    {
        "id": "forefoot_sensor",
        "y_frac": 0.65,
        "x_frac": -0.20,
        "diameter_mm": 10.0,
        "depth_mm": 8.0,
        "purpose": "Pressure + future vibration",
    },
]

NON_CLINICAL_DISCLAIMER = (
    "The Lattice Engine produces engineering density and stiffness "
    "parameters for structural optimisation. Zones are named by anatomic "
    "region for geometric reference only. No therapeutic, medical, or "
    "treatment function is claimed."
)


def _clamp(v: float, lo: float, hi: float) -> float:
    return float(max(lo, min(hi, v)))


def generate_lattice_profile(geometry_profile: dict, preset: str = "balanced") -> dict:
    """Generate a complete lattice map from a geometry profile.

    Args:
        geometry_profile: Dict from geometry_outputs/GEOMETRY_PROFILE_*.json.
        preset: One of "comfort", "balanced", "sport", "recovery".

    Returns:
        Lattice profile dict ready for JSON export.
    """
    if preset not in SUPPORT_PRESETS:
        raise ValueError(f"Unknown preset '{preset}'. Choose from: {list(SUPPORT_PRESETS)}")

    ps = SUPPORT_PRESETS[preset]
    density_map = geometry_profile.get("lattice_density_map", {})
    cell_sizes = geometry_profile.get("lattice_cell_sizes_mm", {})
    priority = geometry_profile.get("priority_balance", {})
    profile_id = geometry_profile.get("profile_id", "GP-unknown")

    zones_out = {}

    for zone in ZONE_NAMES:
        # Base density from geometry profile (use mapped key)
        profile_key = ZONE_TO_PROFILE_KEY.get(zone, zone)
        base_density = density_map.get(profile_key, 0.28)

        # Apply comfort/support shift
        comfort = priority.get("comfort_priority", 50)
        support = priority.get("support_priority", 50)

        if comfort > 60:
            base_density -= 0.02
        elif support > 60:
            base_density += 0.02

        # Apply preset shift
        density = _clamp(base_density + ps["density_shift"], 0.10, 0.50)

        # Cell size: inverse of density
        cell = _clamp(10.5 - density * 15.0, 3.0, 12.0)

        # Stiffness
        stiffness = int(_clamp(round(density * 20.0), 1, 10))

        # Flex: inverse of stiffness, bonus for forefoot/toes
        flex = 11 - stiffness
        if zone in ("forefoot_propulsion", "toe_release"):
            flex += 1
        flex = int(_clamp(flex, 1, 10))

        # Energy return: density-dependent with zone bonus
        zone_bonus = 2 if zone in ("heel_impact", "forefoot_propulsion") else (
            1 if zone == "arch_bridge" else 0
        )
        energy = int(_clamp(round(density * 18.0 + zone_bonus), 1, 10))

        y_lo, y_hi = ZONE_Y_BOUNDS[zone]

        zones_out[zone] = {
            "density": round(density, 3),
            "cell_size_mm": round(cell, 2),
            "stiffness_score": stiffness,
            "flex_score": flex,
            "energy_return_score": energy,
            "y_fraction_range": [y_lo, y_hi],
        }

    # Density transitions
    transitions = geometry_profile.get("density_transitions", [])

    # Compute medial/lateral wall biases after preset shift
    walls = geometry_profile.get("walls", {})
    medial_raw = walls.get("medial", {}).get("strength_index", 3.0)
    lateral_raw = walls.get("lateral", {}).get("strength_index", 2.0)
    medial_bias = int(_clamp(50 + (medial_raw - 3.0) * 25.0 + ps["medial_bias_shift"], 0, 100))
    lateral_bias = int(_clamp(50 + (lateral_raw - 3.0) * 25.0 + ps["lateral_bias_shift"], 0, 100))

    # Pressure distribution map (5×5 grid)
    pressure_map = _build_pressure_map(density_map)

    # Sensor cavity coordinates in mm (scale by foot dimensions)
    foot_length = 265.0
    foot_width = 80.0
    cavities_mm = []
    for cav in SENSOR_CAVITIES:
        cavities_mm.append({
            **cav,
            "x_mm": round(cav["x_frac"] * foot_width * 0.5, 1),
            "y_mm": round(cav["y_frac"] * foot_length, 1),
        })

    lattice_profile = {
        "profile_id": f"LP-{profile_id.split('-', 1)[-1] if '-' in profile_id else profile_id}",
        "source_geometry_profile": profile_id,
        "generated_utc": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "support_preset": preset,
        "preset_description": ps["description"],
        "zones": zones_out,
        "density_transitions": transitions,
        "wall_biases": {
            "medial_pct": medial_bias,
            "lateral_pct": lateral_bias,
        },
        "pressure_distribution_grid": pressure_map,
        "sensor_cavities": cavities_mm,
        "comfort_support_ratio": {
            "comfort": geometry_profile.get("priority_balance", {}).get("comfort_priority", 50),
            "support": geometry_profile.get("priority_balance", {}).get("support_priority", 50),
        },
        "non_clinical_disclaimer": NON_CLINICAL_DISCLAIMER,
    }

    return lattice_profile


def _build_pressure_map(density_map: dict) -> list:
    """Build a 5×5 coarse pressure distribution grid."""
    import math
    grid = []
    zone_y = {
        "heel": 0.10, "arch": 0.30, "midfoot": 0.48,
        "forefoot": 0.65, "toes": 0.88,
    }
    zone_x = {
        "heel": 0.0, "arch": 0.3, "midfoot": 0.0,
        "forefoot": 0.0, "toes": 0.0,
    }

    for yi in range(5):
        row = []
        y_frac = (yi + 0.5) / 5.0
        for xi in range(5):
            x_frac = (xi - 2.0) / 3.0
            pressure = 0.0
            for zone_key, (center_y, center_x) in ((k, (zone_y[k], zone_x[k])) for k in density_map):
                dy = (y_frac - center_y) / 0.12
                dx = (x_frac - center_x) / 0.20
                pressure += density_map[zone_key] * 100 * \
                    math.exp(-(dy**2 + dx**2))
            row.append(round(pressure, 1))
        grid.append(row)

    return grid

#!/usr/bin/env python3
"""Shoe Architecture Generator V1 — converts geometry + lattice profiles into a full modular footwear specification.

Input:
  - Geometry profile JSON (geometry_outputs/GEOMETRY_PROFILE_*.json)
  - Lattice profile JSON (lattice_outputs/LATTICE_PROFILE_*.json)

Output:
  - Shoe architecture JSON (shoe_outputs/SHOE_ARCH_*.json)
    containing layer stack, shell zones, outsole segmentation,
    capsule cavity, weight model, flexibility map, manufacturing modes,
    and future assembly sequence.

Modes: comfort | sport | recovery | balanced
"""

import json
import math
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Optional, Tuple

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

PA11_DENSITY_G_CM3 = 1.04
TPU_RUBBER_DENSITY_G_CM3 = 1.20
PA12_DENSITY_G_CM3 = 1.01

FOOT_LENGTH_REF_MM = 265.0  # EU42
FOOT_WIDTH_REF_MM = 80.0

CAPSULE_DIMS = {
    "length_mm": 45.0,
    "width_mm": 25.0,
    "height_mm": 12.0,
    "volume_cm3": 13.5,
    "weight_g": 28.0,
    "x_offset_mm": 15.0,  # medial from centreline
    "y_frac_start": 0.30,
    "y_frac_end": 0.45,
    "clearance_mm": 2.0,
}

# Layer stack: per-zone lattice core thickness by preset (mm)
LATTICE_THICKNESS = {
    "heel_impact":       {"comfort": 28.0, "sport": 22.0, "recovery": 28.0, "balanced": 24.0},
    "arch_bridge":       {"comfort": 24.0, "sport": 20.0, "recovery": 26.0, "balanced": 22.0},
    "midfoot_stab":      {"comfort": 22.0, "sport": 18.0, "recovery": 22.0, "balanced": 20.0},
    "forefoot_prop":     {"comfort": 24.0, "sport": 20.0, "recovery": 24.0, "balanced": 22.0},
    "toe_release":       {"comfort": 18.0, "sport": 16.0, "recovery": 18.0, "balanced": 17.0},
}

LINER_THICKNESS = {"comfort": 5.0, "sport": 4.0, "recovery": 6.0, "balanced": 5.0}
SKIN_THICKNESS_MM = 1.5
SENSOR_PLANE_THICKNESS_MM = 2.5
OUTSOLE_THICKNESS_MM = 3.0

NON_CLINICAL_DISCLAIMER = (
    "This shoe architecture specification contains engineering design parameters "
    "for prototype manufacturing evaluation. No medical, therapeutic, diagnostic, "
    "or corrective function is claimed. For engineering assessment only."
)

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _clamp(v: float, lo: float, hi: float) -> float:
    return max(lo, min(hi, v))


def _load_json(path: Path) -> dict:
    with open(path) as f:
        return json.load(f)


# ---------------------------------------------------------------------------
# Shell zones
# ---------------------------------------------------------------------------

def _build_shell_zones(foot_length: float, foot_width: float, preset: str) -> dict:
    return {
        "heel_counter": {
            "y_fraction_range": [0.0, 0.20],
            "thickness_mm": 2.0,
            "material": "PA11 (MJF)",
            "features": ["heel_cup_integration", "achilles_relief", "outsole_bonding_surface"],
        },
        "midfoot_chassis": {
            "y_fraction_range": [0.20, 0.55],
            "thickness_mm": 2.0,
            "material": "PA11 (MJF)",
            "features": ["capsule_access_door_medial", "locating_ribs", "vent_windows"],
        },
        "forefoot_cage": {
            "y_fraction_range": [0.55, 0.80],
            "thickness_mm": 1.5,
            "material": "PA11 (MJF)",
            "features": ["flex_segmentation_lines", "upper_bonding_flange"],
        },
        "toe_cap": {
            "y_fraction_range": [0.80, 1.00],
            "thickness_mm": 1.5,
            "material": "PA11 (MJF)",
            "features": ["reinforced_perforated", "bumper_ridge"],
        },
    }


# ---------------------------------------------------------------------------
# Outsole segmentation
# ---------------------------------------------------------------------------

def _build_outsole(foot_length: float, preset: str) -> dict:
    return {
        "pads": [
            {
                "id": "heel_strike",
                "y_fraction_range": [0.0, 0.18],
                "width_mm": 55.0,
                "length_mm": round(foot_length * 0.18, 1),
                "thickness_mm": OUTSOLE_THICKNESS_MM,
                "material": "TPU rubber Shore 60A",
                "tread_pattern": "wave",
            },
            {
                "id": "lateral_midfoot",
                "y_fraction_range": [0.35, 0.50],
                "width_mm": 25.0,
                "length_mm": round(foot_length * 0.15, 1),
                "thickness_mm": OUTSOLE_THICKNESS_MM,
                "material": "TPU rubber Shore 60A",
                "tread_pattern": "wave",
            },
            {
                "id": "met_heads",
                "y_fraction_range": [0.60, 0.78],
                "width_mm": 65.0,
                "length_mm": round(foot_length * 0.18, 1),
                "thickness_mm": OUTSOLE_THICKNESS_MM,
                "material": "TPU rubber Shore 60A",
                "tread_pattern": "wave",
            },
            {
                "id": "hallux",
                "y_fraction_range": [0.82, 0.98],
                "width_mm": 30.0,
                "length_mm": round(foot_length * 0.16, 1),
                "thickness_mm": OUTSOLE_THICKNESS_MM,
                "material": "TPU rubber Shore 60A",
                "tread_pattern": "wave",
            },
        ],
        "flex_gaps": [
            {"id": "midfoot_gap", "y_fraction": 0.50, "gap_mm": 5.0},
            {"id": "metatarsal_gap", "y_fraction": 0.78, "gap_mm": 4.0},
        ],
    }


# ---------------------------------------------------------------------------
# Layer stack
# ---------------------------------------------------------------------------

def _build_layer_stack(preset: str, lattice_profile: dict) -> dict:
    """Compute the full layer stack with per-zone lattice thickness."""
    lattice_thick = LATTICE_THICKNESS
    heel_thick = lattice_thick["heel_impact"][preset]
    forefoot_thick = lattice_thick["forefoot_prop"][preset]

    layers = [
        {"layer": "L1", "name": "Removable Liner", "thickness_mm": LINER_THICKNESS[preset],
         "material": "EVA foam (Shore 35C) + TPU lattice backing", "printable": False},
        {"layer": "L2", "name": "Sensor Plane", "thickness_mm": SENSOR_PLANE_THICKNESS_MM,
         "material": "PA12 housings + coin-cell BLE nodes", "printable": "housings_only"},
        {"layer": "L3", "name": "Skin Top", "thickness_mm": SKIN_THICKNESS_MM,
         "material": "PA11", "printable": True},
        {"layer": "L4", "name": "Lattice Core", "thickness_mm": heel_thick,
         "material": "PA11 (MJF), gyroid TPMS", "printable": True,
         "zone_thicknesses_mm": {z: lattice_thick[z][preset] for z in lattice_thick}},
        {"layer": "L5", "name": "Skin Bottom", "thickness_mm": SKIN_THICKNESS_MM,
         "material": "PA11", "printable": True},
        {"layer": "L6", "name": "Outsole Pads", "thickness_mm": OUTSOLE_THICKNESS_MM,
         "material": "TPU rubber Shore 60A", "printable": False},
    ]

    total = sum(
        (l["thickness_mm"] if not isinstance(l["thickness_mm"], dict) else l["thickness_mm"])
        if l["layer"] != "L4" else heel_thick
        for l in layers
    )

    return {
        "layers": layers,
        "zone_thickness_summary_mm": {z: lattice_thick[z][preset] for z in lattice_thick},
        "heel_stack_mm": total,
        "forefoot_stack_mm": total - heel_thick + forefoot_thick,
        "heel_to_toe_drop_mm": heel_thick - forefoot_thick,
    }


# ---------------------------------------------------------------------------
# Capsule cavity
# ---------------------------------------------------------------------------

def _build_capsule_cavity(foot_length: float, foot_width: float) -> dict:
    return {
        "dimensions_mm": {
            "length": CAPSULE_DIMS["length_mm"],
            "width": CAPSULE_DIMS["width_mm"],
            "height": CAPSULE_DIMS["height_mm"],
        },
        "volume_cm3": CAPSULE_DIMS["volume_cm3"],
        "position": {
            "y_fraction_start": CAPSULE_DIMS["y_frac_start"],
            "y_fraction_end": CAPSULE_DIMS["y_frac_end"],
            "x_offset_mm": CAPSULE_DIMS["x_offset_mm"],
            "x_description": "medial from centreline",
        },
        "clearance_gap_mm": CAPSULE_DIMS["clearance_mm"],
        "access": {
            "type": "slide_open_door",
            "location": "medial_midfoot_outer_shell",
            "tool_required": False,
        },
        "electronics": {
            "mcu": "ESP32-C3-MINI-1 (preferred) or nRF52840",
            "ble_version": "5.0",
            "battery": "Li-Po 180 mAh, 3.7V",
            "battery_capacity_mah": 180,
            "charge_connector": "USB-C",
            "charge_in_shoe": False,
            "runtime_hours_1hz": 36,
        },
    }


# ---------------------------------------------------------------------------
# Weight model
# ---------------------------------------------------------------------------

def _build_weight_model(foot_length: float, foot_width: float, preset: str,
                         lattice_profile: dict) -> dict:
    """Estimate component weights using approximate volumes and material densities."""
    # Shell volume estimate: perimeter * height * thickness
    shell_perimeter_mm = 2 * (foot_length + foot_width) * 1.3  # rough
    shell_volume_cm3 = (shell_perimeter_mm * 40.0 * 1.8) / 1000.0  # height 40mm, thick 1.8mm
    shell_weight = round(shell_volume_cm3 * PA11_DENSITY_G_CM3, 1)

    # Lattice core: foot area * heel thickness * avg density
    foot_area_cm2 = (foot_length * foot_width * 0.75) / 100.0
    avg_density = sum(
        z.get("density", 0.28) for z in lattice_profile.get("zones", {}).values()
    ) / max(len(lattice_profile.get("zones", {})), 1)
    heel_thick = LATTICE_THICKNESS["heel_impact"][preset]
    lattice_volume_cm3 = foot_area_cm2 * (heel_thick / 10.0) * avg_density
    lattice_weight = round(lattice_volume_cm3 * PA11_DENSITY_G_CM3, 1)

    # Outsole: pad area * thickness * density
    pad_area_cm2 = (foot_length * foot_width * 0.45) / 100.0
    outsole_volume_cm3 = pad_area_cm2 * (OUTSOLE_THICKNESS_MM / 10.0)
    outsole_weight = round(outsole_volume_cm3 * TPU_RUBBER_DENSITY_G_CM3, 1)

    capsule_weight = CAPSULE_DIMS["weight_g"]
    liner_weight = 32.0 if preset in ("balanced", "comfort") else (
        28.0 if preset == "sport" else 35.0
    )

    total = round(shell_weight + lattice_weight + capsule_weight + outsole_weight + liner_weight, 1)

    return {
        "shell_g": shell_weight,
        "lattice_core_g": lattice_weight,
        "smart_capsule_g": capsule_weight,
        "outsole_pads_g": outsole_weight,
        "removable_liner_g": liner_weight,
        "total_g": total,
        "reference_size": "EU42",
        "tolerance_pct": 15,
    }


# ---------------------------------------------------------------------------
# Flexibility map
# ---------------------------------------------------------------------------

def _build_flexibility_map(foot_length: float) -> dict:
    return [
        {
            "zone": "midfoot_hinge",
            "y_fraction_range": [0.40, 0.55],
            "mechanism": "lower density lattice + thinner core",
            "flex_score": 7,
        },
        {
            "zone": "metatarsal_flex",
            "y_fraction_range": [0.65, 0.75],
            "mechanism": "flex channels in liner + lattice groove",
            "flex_score": 8,
        },
        {
            "zone": "toe_roll",
            "y_fraction_range": [0.80, 1.00],
            "mechanism": "natural toe spring + thin lattice",
            "flex_score": 9,
        },
    ]


# ---------------------------------------------------------------------------
# Manufacturing modes
# ---------------------------------------------------------------------------

def _build_manufacturing_modes() -> dict:
    return {
        "production": {
            "mjf": {
                "process": "HP Multi Jet Fusion",
                "material": "PA11",
                "min_wall_mm": 0.6,
                "min_cell_mm": 3.0,
                "batch_size": "100–1000 pairs",
                "status": "production_ready",
            },
        },
        "low_volume": {
            "sls": {
                "process": "Selective Laser Sintering",
                "material": "PA12",
                "min_wall_mm": 0.3,
                "min_cell_mm": 2.5,
                "batch_size": "10–100 pairs",
                "status": "prototype_ready",
            },
        },
        "future": {
            "hybrid_molded_shell": {
                "process": "Injection-moulded TPU chassis",
                "material": "TPU + textile overmould",
                "target_volume": ">10,000 pairs/year",
                "status": "planned_v2",
            },
            "textile_upper_integration": {
                "process": "Knit-to-shape + heat-stake bonding",
                "material": "TPU-coated polyester mesh",
                "target_volume": ">10,000 pairs/year",
                "status": "planned_v2",
            },
        },
    }


# ---------------------------------------------------------------------------
# Assembly sequence
# ---------------------------------------------------------------------------

def _build_assembly_sequence() -> list:
    return [
        {"station": 1, "name": "Shell arrival",
         "action": "Outer shell arrives pre-assembled (textile upper + PA11 chassis + door)"},
        {"station": 2, "name": "Lattice core QC",
         "action": "Lattice core arrives from printer; check density map and cell integrity"},
        {"station": 3, "name": "Capsule insertion",
         "action": "Snap-fit smart capsule into medial cavity; BLE pairing test with sensor nodes"},
        {"station": 4, "name": "Sensor node placement",
         "action": "Place pressure/IMU/temp nodes into heel, arch, forefoot cavities; activation check via BLE scan"},
        {"station": 5, "name": "Core + shell assembly",
         "action": "Drop lattice core into outer shell; verify locating ribs seated"},
        {"station": 6, "name": "Liner snap",
         "action": "3-pin alignment, press liner to seat"},
        {"station": 7, "name": "Outsole bonding",
         "action": "Heat-press TPU pads onto lattice bottom; peel test 1 per batch"},
        {"station": 8, "name": "Final QC",
         "action": "Weight check, visual inspection, BLE comm test, manual flex test"},
    ]


# ---------------------------------------------------------------------------
# Preset variants
# ---------------------------------------------------------------------------

def _build_preset_variants(foot_length: float, foot_width: float) -> dict:
    variants = {}
    for preset in ("comfort", "sport", "recovery", "balanced"):
        heel = LATTICE_THICKNESS["heel_impact"][preset]
        forefoot = LATTICE_THICKNESS["forefoot_prop"][preset]
        liner = LINER_THICKNESS[preset]
        total = liner + SENSOR_PLANE_THICKNESS_MM + SKIN_THICKNESS_MM * 2 + heel + OUTSOLE_THICKNESS_MM

        variants[preset] = {
            "heel_stack_mm": total,
            "forefoot_stack_mm": total - heel + forefoot,
            "heel_to_toe_drop_mm": heel - forefoot,
            "liner_thickness_mm": liner,
            "lattice_heel_thickness_mm": heel,
        }
    return variants


# ---------------------------------------------------------------------------
# Core generator
# ---------------------------------------------------------------------------

def generate_shoe_architecture(
    geometry_profile: dict,
    lattice_profile: dict,
    preset: str = "balanced",
) -> dict:
    """Generate a full modular footwear architecture specification.

    Args:
        geometry_profile: Dict from geometry_outputs/GEOMETRY_PROFILE_*.json.
        lattice_profile: Dict from lattice_outputs/LATTICE_PROFILE_*.json.
        preset: One of "comfort", "sport", "recovery", "balanced".

    Returns:
        Shoe architecture dict ready for JSON export.
    """
    if preset not in ("comfort", "sport", "recovery", "balanced"):
        raise ValueError(f"Unknown preset '{preset}'. Choose from: comfort, sport, recovery, balanced")

    gp_id = geometry_profile.get("profile_id", "GP-unknown")
    lp_id = lattice_profile.get("profile_id", "LP-unknown")

    # Derive foot dimensions from profile (fallback to reference)
    heel_data = geometry_profile.get("heel_cup", {})
    foot_length = heel_data.get("radius_mm", 26.1) / 0.45 * 2  # radius = heel_width * 0.45
    foot_length = _clamp(foot_length, 200, 320) if foot_length > 50 else FOOT_LENGTH_REF_MM
    if foot_length < 100:
        foot_length = FOOT_LENGTH_REF_MM

    foot_width = heel_data.get("radius_mm", 26.1) * 2 / 0.75
    foot_width = _clamp(foot_width, 60, 110) if foot_width > 20 else FOOT_WIDTH_REF_MM
    if foot_width < 30:
        foot_width = FOOT_WIDTH_REF_MM

    shell_zones = _build_shell_zones(foot_length, foot_width, preset)
    outsole = _build_outsole(foot_length, preset)
    layer_stack = _build_layer_stack(preset, lattice_profile)
    capsule_cavity = _build_capsule_cavity(foot_length, foot_width)
    weight_model = _build_weight_model(foot_length, foot_width, preset, lattice_profile)
    flexibility_map = _build_flexibility_map(foot_length)
    manufacturing_modes = _build_manufacturing_modes()
    assembly_sequence = _build_assembly_sequence()
    preset_variants = _build_preset_variants(foot_length, foot_width)

    return {
        "architecture_id": "SA-001",
        "generated_utc": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "source_geometry_profile": gp_id,
        "source_lattice_profile": lp_id,
        "preset": preset,
        "foot_reference": {
            "length_mm": round(foot_length, 1),
            "width_mm": round(foot_width, 1),
            "size_approx": "EU42",
        },
        "shell_zones": shell_zones,
        "outsole_segmentation": outsole,
        "capsule_cavity": capsule_cavity,
        "layer_stack": layer_stack,
        "total_stack_thickness_mm": layer_stack["heel_stack_mm"],
        "heel_to_toe_drop_mm": layer_stack["heel_to_toe_drop_mm"],
        "preset_variants": preset_variants,
        "weight_model": weight_model,
        "flexibility_map": flexibility_map,
        "manufacturing_modes": manufacturing_modes,
        "assembly_sequence": assembly_sequence,
        "non_clinical_disclaimer": NON_CLINICAL_DISCLAIMER,
    }


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def main():
    import argparse

    parser = argparse.ArgumentParser(
        description="Generate modular footwear architecture from geometry + lattice profiles."
    )
    parser.add_argument(
        "--geometry",
        type=Path,
        default=ROOT / "geometry_outputs" / "GEOMETRY_PROFILE_001.json",
        help="Path to geometry profile JSON",
    )
    parser.add_argument(
        "--lattice",
        type=Path,
        default=ROOT / "lattice_outputs" / "LATTICE_PROFILE_001.json",
        help="Path to lattice profile JSON",
    )
    parser.add_argument(
        "--preset",
        choices=["comfort", "sport", "recovery", "balanced"],
        default="balanced",
        help="Support/comfort preset mode",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=None,
        help="Output path for architecture JSON (default: shoe_outputs/SHOE_ARCH_001.json)",
    )
    args = parser.parse_args()

    # Load inputs
    geo = _load_json(args.geometry)
    lat = _load_json(args.lattice)

    # Generate
    arch = generate_shoe_architecture(geo, lat, args.preset)

    # Write output
    out_path = args.output or (ROOT / "shoe_outputs" / "SHOE_ARCH_001.json")
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with open(out_path, "w") as f:
        json.dump(arch, f, indent=2)

    # Summary
    ls = arch["layer_stack"]
    wm = arch["weight_model"]
    cc = arch["capsule_cavity"]
    fm = arch["flexibility_map"]
    aseq = arch["assembly_sequence"]

    print("=" * 60)
    print(f"  ZILFIT Shoe Architecture V1 — Preset: {args.preset}")
    print("=" * 60)
    print(f"  Output: {out_path}")
    print(f"  Source geometry:  {arch['source_geometry_profile']}")
    print(f"  Source lattice:   {arch['source_lattice_profile']}")
    print()
    print(f"  Foot reference: {arch['foot_reference']['length_mm']}mm × {arch['foot_reference']['width_mm']}mm (~EU42)")
    print()
    print("  ── Layer Stack ──")
    for layer in ls["layers"]:
        thick = layer["thickness_mm"]
        if isinstance(thick, dict):
            thick = f"{thick.get('heel_impact', '—')}mm (heel)"
        else:
            thick = f"{thick}mm"
        print(f"  {layer['layer']:3s} {layer['name']:<22s} {thick:>12s}  [{layer['material'][:40]}]")
    print(f"  {'':3s} {'TOTAL':<22s} {ls['heel_stack_mm']:>12.1f}mm (heel)")
    print()
    print(f"  Total shoe stack thickness:   {ls['heel_stack_mm']} mm")
    print(f"  Heel-to-toe drop:             {ls['heel_to_toe_drop_mm']} mm")
    print(f"  Forefoot stack:               {ls['forefoot_stack_mm']} mm")
    print()
    print("  ── Weight Model (EU42) ──")
    print(f"  Outer shell:          {wm['shell_g']:>6.1f} g")
    print(f"  Lattice core:         {wm['lattice_core_g']:>6.1f} g")
    print(f"  Smart capsule:        {wm['smart_capsule_g']:>6.1f} g")
    print(f"  Outsole pads:         {wm['outsole_pads_g']:>6.1f} g")
    print(f"  Removable liner:      {wm['removable_liner_g']:>6.1f} g")
    print(f"  ─────────────────────────────")
    print(f"  Estimated total weight:  {wm['total_g']:.1f} g")
    print()
    print(f"  Capsule cavity volume:  {cc['volume_cm3']} cm³")
    print(f"  Capsule cavity dims:    {cc['dimensions_mm']['length']}×{cc['dimensions_mm']['width']}×{cc['dimensions_mm']['height']} mm")
    print()
    print("  ── Flexibility Map ──")
    for fz in fm:
        y0, y1 = fz["y_fraction_range"]
        print(f"  {fz['zone']:<22s} Y={y0:.2f}–{y1:.2f}  flex={fz['flex_score']}  ({fz['mechanism']})")
    print()
    print("  ── Modular Assembly Summary ──")
    for st in aseq:
        print(f"  Station {st['station']}: {st['name']}")
        print(f"           {st['action']}")
    print()
    print(f"  → {len(aseq)} stations, zero permanent adhesives (except outsole heat-press)")
    print(f"  → All electronic modules user-removable without tools")
    print(f"  → Preset variants available: comfort, sport, recovery, balanced")
    print()

    # Preset comparison
    print("  ── Preset Comparison ──")
    print(f"  {'Preset':<12s} {'Heel Stack':>12s} {'Drop':>8s} {'Liner':>7s} {'Lattice':>9s}")
    print(f"  {'─'*12} {'─'*12} {'─'*8} {'─'*7} {'─'*9}")
    for p, v in arch["preset_variants"].items():
        print(f"  {p:<12s} {v['heel_stack_mm']:>8.1f} mm {v['heel_to_toe_drop_mm']:>5.0f} mm {v['liner_thickness_mm']:>4.0f} mm {v['lattice_heel_thickness_mm']:>6.0f} mm")

    print()
    print("  Done.")

    return 0


if __name__ == "__main__":
    sys.exit(main())

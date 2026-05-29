#!/usr/bin/env python3
"""Generate STL insole with adaptive lattice profile from latest geometry profile.

Loads newest geometry_outputs/GEOMETRY_PROFILE_*.json
Runs lattice engine → lattice_outputs/LATTICE_PROFILE_NNN.json
Runs STL generator → stl_outputs/ZILFIT_INSOLE_V1.stl (with lattice metadata)

Usage:
    python3 tools/run_stl_demo.py [--preset balanced]
"""

import argparse
import json
import os
import sys
from glob import glob
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from tools.lattice_engine import generate_lattice_profile
from tools.stl_insole_generator import generate_insole_stl


def find_latest_profile(pattern: str) -> str | None:
    files = sorted(glob(pattern))
    return files[-1] if files else None


def main():
    parser = argparse.ArgumentParser(description="ZILFIT STL + lattice demo")
    parser.add_argument("--preset", default="balanced",
                        choices=["comfort", "balanced", "sport", "recovery"],
                        help="Support mode preset (default: balanced)")
    args = parser.parse_args()

    # Load geometry profile
    geom_pattern = str(ROOT / "geometry_outputs" / "GEOMETRY_PROFILE_*.json")
    geom_path = find_latest_profile(geom_pattern)
    if not geom_path:
        print("ERROR: No geometry profile found in geometry_outputs/", file=sys.stderr)
        sys.exit(1)

    print(f"Geometry profile: {geom_path}")
    with open(geom_path, "r") as f:
        geom = json.load(f)

    # Generate lattice profile
    print(f"Lattice preset: {args.preset}")
    lattice = generate_lattice_profile(geom, preset=args.preset)

    lattice_dir = ROOT / "lattice_outputs"
    lattice_dir.mkdir(parents=True, exist_ok=True)
    existing = sorted(glob(str(lattice_dir / "LATTICE_PROFILE_*.json")))
    next_num = len(existing) + 1
    lattice_path = lattice_dir / f"LATTICE_PROFILE_{next_num:03d}.json"
    with open(lattice_path, "w") as f:
        json.dump(lattice, f, indent=2)
    print(f"Lattice profile: {lattice_path}")

    # Print zone table
    print("\n  Lattice Zone Table:")
    print(f"  {'Zone':<28} {'Density':>7} {'Cell(mm)':>8} {'Stiff':>5} {'Flex':>5} {'Energy':>6}")
    print(f"  {'-'*28} {'-'*7} {'-'*8} {'-'*5} {'-'*5} {'-'*6}")
    for zname, zdata in lattice["zones"].items():
        print(f"  {zname:<28} {zdata['density']:>7.3f} {zdata['cell_size_mm']:>8.2f} {zdata['stiffness_score']:>5} {zdata['flex_score']:>5} {zdata['energy_return_score']:>6}")

    # Pressure distribution map
    pm = lattice["pressure_distribution_grid"]
    print(f"\n  Pressure Distribution Map (5x5):")
    for row in pm:
        cells = " ".join(f"{v:6.1f}" for v in row)
        print(f"  [{cells} ]")

    # Sensor cavities
    print(f"\n  Sensor Cavity Coordinates (mm):")
    for cav in lattice["sensor_cavities"]:
        print(f"  {cav['id']}: X={cav['x_mm']:+.1f} Y={cav['y_mm']:.1f} d={cav['diameter_mm']}mm×{cav['depth_mm']}mm  [{cav['purpose']}]")

    # Comfort/support ratio
    cs = lattice["comfort_support_ratio"]
    print(f"\n  Comfort/Support Ratio: C={cs['comfort']} S={cs['support']} (preset={args.preset})")

    # Generate STL
    stl_dir = ROOT / "stl_outputs"
    stl_dir.mkdir(parents=True, exist_ok=True)
    stl_path = str(stl_dir / "ZILFIT_INSOLE_V1.stl")

    print()
    stats = generate_insole_stl(geom, stl_path, lattice_profile=lattice)

    print(f"\n  STL Generated:")
    print(f"  Path: {stats['path']}")
    print(f"  Triangles: {stats['triangle_count']:,}")
    print(f"  Watertight: {stats['watertight']}")
    print(f"  File size: {stats['file_size_kb']} KB")
    print(f"  Dimensions: {stats['dimensions_mm']['length']}×{stats['dimensions_mm']['width']}×{stats['dimensions_mm']['height']} mm")

    # Show lattice metadata from STL stats
    lm = stats.get("lattice_metadata", {})
    if lm.get("source") != "none":
        print(f"\n  Lattice metadata injected into STL:")
        print(f"  Source: {lm['source']}")
        print(f"  Preset: {lm['support_preset']}")
        print(f"  Zone count: {len(lm.get('zones', {}))}")
        print(f"  Wall biases: medial={lm.get('wall_biases', {}).get('medial_pct')}% lateral={lm.get('wall_biases', {}).get('lateral_pct')}%")
        print(f"  Cavity reservations: {len(lm.get('sensor_cavities_mm', []))}")


if __name__ == "__main__":
    main()

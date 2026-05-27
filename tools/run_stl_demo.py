#!/usr/bin/env python3
"""Generate STL insole from latest geometry profile.

Loads newest geometry_outputs/GEOMETRY_PROFILE_*.json and exports
stl_outputs/ZILFIT_INSOLE_V1.stl.
"""

import json
import os
import sys
from glob import glob
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from tools.stl_insole_generator import generate_insole_stl


def find_latest_profile() -> str | None:
    pattern = str(ROOT / "geometry_outputs" / "GEOMETRY_PROFILE_*.json")
    files = sorted(glob(pattern))
    return files[-1] if files else None


def main():
    profile_path = find_latest_profile()
    if not profile_path:
        print("ERROR: No geometry profile found in geometry_outputs/", file=sys.stderr)
        sys.exit(1)

    print(f"Profile: {profile_path}")
    with open(profile_path, "r") as f:
        profile = json.load(f)

    print(f"Profile ID: {profile['profile_id']}")
    print(f"Heel cup: {profile['heel_cup']['depth_mm']}mm")
    print(f"Arch curve: {profile['arch_curve']['height_mm']}mm")
    print(f"Flex channels: {profile['forefoot_flex']['channel_count']}")

    output_dir = ROOT / "stl_outputs"
    output_dir.mkdir(parents=True, exist_ok=True)
    output_path = str(output_dir / "ZILFIT_INSOLE_V1.stl")

    print()
    stats = generate_insole_stl(profile, output_path)

    print(f"\nSTL Generated:")
    print(f"  Path: {stats['path']}")
    print(f"  Triangles: {stats['triangle_count']:,}")
    print(f"  Vertices: {stats['vertex_count']:,}")
    print(f"  Watertight: {stats['watertight']}")
    print(f"  File size: {stats['file_size_kb']} KB")
    print(f"  Bounding box (mm):")
    for axis, (lo, hi) in stats["bounding_box_mm"].items():
        print(f"    {axis}: {lo} → {hi}")
    print(f"  Dimensions: {stats['dimensions_mm']['length']}×{stats['dimensions_mm']['width']}×{stats['dimensions_mm']['height']} mm")


if __name__ == "__main__":
    main()

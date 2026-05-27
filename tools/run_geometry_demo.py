#!/usr/bin/env python3
"""Generate geometry profile from the latest runtime session output.

Loads the newest runtime_outputs/ZILFIT_RUNTIME_*.json and produces
geometry_outputs/GEOMETRY_PROFILE_001.json.
"""

import json
import os
import sys
from glob import glob
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from tools.geometry_profile_generator import generate_geometry_profile


def find_latest_runtime() -> str | None:
    pattern = str(ROOT / "runtime_outputs" / "ZILFIT_RUNTIME_*.json")
    files = sorted(glob(pattern))
    return files[-1] if files else None


def main():
    runtime_path = find_latest_runtime()
    if not runtime_path:
        print("ERROR: No runtime session found in runtime_outputs/", file=sys.stderr)
        sys.exit(1)

    print(f"Loading: {runtime_path}")
    with open(runtime_path, "r") as f:
        session = json.load(f)

    print(f"Session: {session['session_id']}")
    print(f"Foot type: {session['classification']['predicted_class']}")

    profile = generate_geometry_profile(session)

    output_dir = ROOT / "geometry_outputs"
    output_dir.mkdir(parents=True, exist_ok=True)

    # Find next profile number
    existing = sorted(glob(str(output_dir / "GEOMETRY_PROFILE_*.json")))
    next_num = len(existing) + 1
    output_path = output_dir / f"GEOMETRY_PROFILE_{next_num:03d}.json"

    with open(output_path, "w") as f:
        json.dump(profile, f, indent=2)

    size = output_path.stat().st_size
    print(f"\nGeometry profile generated:")
    print(f"  Heel cup: {profile['heel_cup']['depth_mm']}mm depth, "
          f"{profile['heel_cup']['radius_mm']}mm radius")
    print(f"  Arch curve: {profile['arch_curve']['height_mm']}mm height, "
          f"{profile['arch_curve']['longitudinal_radius_mm']}mm radius")
    print(f"  Flex channels: {profile['forefoot_flex']['channel_count']}, "
          f"{profile['forefoot_flex']['channel_depth_mm']}mm depth")
    print(f"  Walls: medial={profile['walls']['medial']['thickness_mm']}mm, "
          f"lateral={profile['walls']['lateral']['thickness_mm']}mm")
    print(f"  Density map: {profile['lattice_density_map']}")
    print(f"  Cell sizes: {profile['lattice_cell_sizes_mm']}")
    print(f"  Transitions: {len(profile['density_transitions'])} zone boundaries")
    print(f"  Priority: {profile['priority_balance']['balance_type']} "
          f"(C={profile['priority_balance']['comfort_priority']} "
          f"S={profile['priority_balance']['support_priority']})")
    print(f"\nWritten: {output_path} ({size} bytes)")


if __name__ == "__main__":
    main()

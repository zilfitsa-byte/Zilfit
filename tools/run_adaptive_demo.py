#!/usr/bin/env python3
"""Run the Adaptive Geometry Engine demo across 5 sessions.

Reads sample_data/adaptive_sessions.json and outputs
adaptive_reports/demo_report.json.
"""

import json
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from tools.adaptive_geometry_rules import compute_geometry


def main():
    input_path = ROOT / "sample_data" / "adaptive_sessions.json"
    output_dir = ROOT / "adaptive_reports"
    output_path = output_dir / "demo_report.json"

    with open(input_path, "r") as f:
        data = json.load(f)

    sessions = data["sessions"]
    results = []

    for s in sessions:
        sid = s["session_id"]
        mode = s.get("mode", "private_tester")
        overrides = s.get("doctor_overrides") if mode == "doctor_override" else None

        geom = compute_geometry(
            pressure_balance=s["pressure_balance"],
            roll_angle=s["roll_angle"],
            fatigue_signal=s["fatigue_signal"],
            steps=s["steps"],
            foot_type=s["foot_type"],
            mode=mode,
            doctor_overrides=overrides,
        )

        entry = {
            "session_id": sid,
            "inputs": {
                "pressure_balance": s["pressure_balance"],
                "roll_angle": s["roll_angle"],
                "fatigue_signal": s["fatigue_signal"],
                "steps": s["steps"],
                "foot_type": s["foot_type"],
                "mode": mode,
            },
            "geometry_outputs": geom,
        }
        results.append(entry)
        print(f"  {sid} [{mode}]: heel={geom['heel_cushion_level']} "
              f"arch={geom['arch_support_level']} medial={geom['medial_support_bias']} "
              f"lateral={geom['lateral_support_bias']} flex={geom['flexibility_score']} "
              f"fadj={geom['fatigue_adjustment']}")

    output_dir.mkdir(parents=True, exist_ok=True)

    from datetime import datetime, timezone
    summary = {
        "demo_title": "ZILFIT Adaptive Geometry Engine — Demo Report",
        "session_count": len(results),
        "generated_utc": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "sessions": results,
    }

    with open(output_path, "w") as f:
        json.dump(summary, f, indent=2)

    print(f"\nDemo report written: {output_path} ({os.path.getsize(output_path)} bytes)")


if __name__ == "__main__":
    main()

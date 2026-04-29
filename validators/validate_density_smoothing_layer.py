#!/usr/bin/env python3
import json
import sys
from pathlib import Path

MAX_JUMP = 15.0
ALLOWED_WALLS = (0.5, 0.6, 0.7)

def fail(msg):
    print(f"VALIDATION_FAILED: {msg}")
    sys.exit(1)

def wall_from_density(density):
    if density <= 30:
        return 0.5
    if density <= 55:
        return 0.6
    return 0.7

def smooth_density_map(data, max_jump=MAX_JUMP):
    if data.get("schema_version") != "v1":
        fail("input schema_version must equal v1")

    zones = data.get("zone_outputs", [])
    if len(zones) < 2:
        fail("zone_outputs must contain at least 2 zones")

    smoothed = []
    previous_density = None

    for zone in zones:
        original = float(zone["density_pct"])
        new_density = original
        smoothing_applied = False
        smoothing_reason = "none"

        if previous_density is not None:
            delta = new_density - previous_density
            if abs(delta) > max_jump:
                smoothing_applied = True
                smoothing_reason = "adjacent_density_jump_above_limit"
                if delta > 0:
                    new_density = previous_density + max_jump
                else:
                    new_density = previous_density - max_jump

        new_density = round(new_density, 2)
        t_wall = wall_from_density(new_density)

        failure_flags = []
        if t_wall < 0.5:
            failure_flags.append("wall_thickness_below_physical_min")

        if previous_density is not None and abs(new_density - previous_density) > max_jump:
            failure_flags.append("adjacent_density_jump_above_limit_after_smoothing")

        rec = dict(zone)
        rec["original_density_pct"] = original
        rec["smoothed_density_pct"] = new_density
        rec["density_pct"] = new_density
        rec["density_delta_from_original"] = round(new_density - original, 2)
        rec["smoothing_applied"] = smoothing_applied
        rec["smoothing_reason"] = smoothing_reason
        rec["t_wall_mm"] = t_wall
        rec["failure_flags"] = failure_flags
        rec["baseline_comparison"] = {
            "baseline_wall_mm": 0.6,
            "delta_from_baseline_mm": round(t_wall - 0.6, 3)
        }

        smoothed.append(rec)
        previous_density = new_density

    out = dict(data)
    out["schema_version"] = "v1"
    out["smoothing_layer"] = "zilfit_density_smoothing_layer_v1"
    out["zone_outputs"] = smoothed
    out["model_status"] = "smoothed_simulation_ready"
    return out

def validate_smoothed_output(data):
    zones = data.get("zone_outputs", [])
    if not zones:
        fail("missing zone_outputs")

    prev = None
    for z in zones:
        density = float(z["density_pct"])
        t_wall = z.get("t_wall_mm")

        if t_wall not in ALLOWED_WALLS:
            fail(f"invalid t_wall_mm in {z.get('zone_id')}")

        if "baseline_comparison" not in z:
            fail(f"missing baseline_comparison in {z.get('zone_id')}")

        if "smoothed_density_pct" not in z:
            fail(f"missing smoothed_density_pct in {z.get('zone_id')}")

        if prev is not None and abs(density - prev) > MAX_JUMP:
            fail(f"adjacent density jump still above limit near {z.get('zone_id')}")

        prev = density

    print("DENSITY_SMOOTHING_OUTPUT_VALIDATION_PASS")

def main():
    if len(sys.argv) < 3:
        fail("usage: validate_density_smoothing_layer.py input.json output.json")

    in_path = Path(sys.argv[1])
    out_path = Path(sys.argv[2])

    data = json.loads(in_path.read_text(encoding="utf-8"))
    smoothed = smooth_density_map(data)
    out_path.write_text(json.dumps(smoothed, ensure_ascii=False, indent=2), encoding="utf-8")

    validate_smoothed_output(smoothed)
    print("DENSITY_SMOOTHING_OUTPUT_CREATED")
    print(out_path)

if __name__ == "__main__":
    main()

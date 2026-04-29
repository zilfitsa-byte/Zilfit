#!/usr/bin/env python3
import json
import sys
from pathlib import Path

def fail(msg):
    print(f"VALIDATION_FAILED: {msg}")
    sys.exit(1)

def clamp(x, lo, hi):
    return max(lo, min(hi, x))

def calc_p_norm(zone_load, min_load, max_load):
    if max_load == min_load:
        return 0.5
    return clamp((zone_load - min_load) / (max_load - min_load), 0.0, 1.0)

def calc_density(p_norm, floor, ceiling):
    return clamp(floor + (ceiling - floor) * p_norm, floor, ceiling)

def wall_from_density(density):
    if density <= 30:
        return 0.5
    if density <= 55:
        return 0.6
    return 0.7

def validate_density_record(rec):
    for key in ("density_pct", "source", "confidence", "validation_status"):
        if key not in rec:
            fail(f"missing required density field: {key}")

    if not isinstance(rec["confidence"], (int, float)):
        fail("confidence must be numeric")

    if not (0 <= rec["confidence"] <= 1):
        fail("confidence must be between 0 and 1")

    if rec["validation_status"] not in ("simulation", "prototype", "production"):
        fail("validation_status must be simulation/prototype/production")

    if rec.get("t_wall_mm", 0) < 0.5:
        fail("t_wall_mm must be >= 0.5")

def validate_payload(data):
    if data.get("schema_version") != "v1":
        fail("schema_version must equal v1")

    baseline = data.get("gyroid_wall_thickness_baseline_mm")
    if baseline != 0.6:
        fail("gyroid_wall_thickness_baseline_mm must equal 0.6")

    variants = data.get("physical_wall_variants_mm", [])
    if variants != [0.5, 0.6, 0.7]:
        fail("physical_wall_variants_mm must equal [0.5, 0.6, 0.7]")

    if 0.3 not in data.get("simulation_reference_only_mm", []):
        fail("0.3 must be simulation_reference_only")

    rules = data.get("failure_rules", {})
    if rules.get("fail_if_wall_thickness_below_mm") != 0.5:
        fail("physical min wall rule must be 0.5mm")

    print("FORMULA_SAFETY_LAYER_VALIDATION_PASS")

def self_tests():
    assert calc_p_norm(10, 10, 10) == 0.5
    assert calc_p_norm(5, 10, 20) == 0.0
    assert calc_p_norm(25, 10, 20) == 1.0
    assert calc_density(0.5, 20, 60) == 40
    assert wall_from_density(25) == 0.5
    assert wall_from_density(40) == 0.6
    assert wall_from_density(60) == 0.7
    print("FORMULA_SELF_TESTS_PASS")

def main():
    if len(sys.argv) < 2:
        fail("missing input json path")
    data = json.loads(Path(sys.argv[1]).read_text(encoding="utf-8"))
    validate_payload(data)
    self_tests()

if __name__ == "__main__":
    main()

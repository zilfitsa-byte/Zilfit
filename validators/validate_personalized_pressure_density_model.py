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

def validate_model_config(config):
    if config.get("schema_version") != "v1":
        fail("schema_version must equal v1")

    if config.get("module_id") != "zilfit_personalized_pressure_density_model":
        fail("module_id mismatch")

    zones = config.get("foot_zones", [])
    if len(zones) != 7:
        fail("foot_zones must contain exactly 7 engineering zones")

    zone_ids = [z.get("zone_id") for z in zones]
    if len(set(zone_ids)) != len(zone_ids):
        fail("duplicate zone_id detected")

    for z in zones:
        if not (0 < z.get("contact_fraction", 0) < 1):
            fail(f"invalid contact_fraction for {z.get('zone_id')}")
        if z.get("gait_phase_factor", 0) <= 0:
            fail(f"invalid gait_phase_factor for {z.get('zone_id')}")

    profiles = config.get("profile_density_bounds", {})
    required_profiles = ["CALM", "FEMME", "FOCUS", "VITAL", "BALANCE"]
    for p in required_profiles:
        if p not in profiles:
            fail(f"missing profile bounds: {p}")
        floor = profiles[p].get("density_floor_pct")
        ceiling = profiles[p].get("density_ceiling_pct")
        if floor is None or ceiling is None:
            fail(f"missing density floor/ceiling for {p}")
        if not (10 <= floor < ceiling <= 80):
            fail(f"invalid density bounds for {p}")

    print("PERSONALIZED_MODEL_CONFIG_VALIDATION_PASS")

def validate_subject(subject, config):
    rules = config["personalization_inputs"]

    for key, spec in rules.items():
        if spec.get("required") and key not in subject:
            fail(f"missing personalization input: {key}")

    for key in ["body_weight_kg", "foot_length_mm", "foot_width_mm", "left_right_balance"]:
        value = subject[key]
        spec = rules[key]
        if not (spec["min"] <= value <= spec["max"]):
            fail(f"{key} outside allowed range")

    if subject["arch_height_category"] not in rules["arch_height_category"]["allowed"]:
        fail("arch_height_category not allowed")

    if subject["profile_target"] not in rules["profile_target"]["allowed"]:
        fail("profile_target not allowed")

def generate_personalized_map(subject, config):
    validate_subject(subject, config)

    profile = subject["profile_target"]
    bounds = config["profile_density_bounds"][profile]
    floor = bounds["density_floor_pct"]
    ceiling = bounds["density_ceiling_pct"]

    weight_force = subject["body_weight_kg"] * 9.81
    asym = subject["left_right_balance"]

    raw = []
    for z in config["foot_zones"]:
        asym_factor = 1.0
        if z["zone_id"] == "Z06":
            asym_factor = 1.0 + max(asym, 0) * 0.12
        elif z["zone_id"] == "Z07":
            asym_factor = 1.0 + max(-asym, 0) * 0.12

        zone_load = weight_force * z["contact_fraction"] * z["gait_phase_factor"] * asym_factor
        raw.append((z, zone_load))

    loads = [x[1] for x in raw]
    min_load = min(loads)
    max_load = max(loads)

    output = []
    prev_density = None
    for z, load in raw:
        p_norm = calc_p_norm(load, min_load, max_load)
        density = calc_density(p_norm, floor, ceiling)
        t_wall = wall_from_density(density)

        failure_flags = []
        smoothing_flag = False

        if t_wall < 0.5:
            failure_flags.append("wall_thickness_below_physical_min")

        if prev_density is not None and abs(density - prev_density) > config["failure_rules"]["max_adjacent_density_jump_pct"]:
            failure_flags.append("adjacent_density_jump_above_limit")
            smoothing_flag = True

        rec = {
            "zone_id": z["zone_id"],
            "zone_name": z["name"],
            "zone_load_N": round(load, 3),
            "P_norm": round(p_norm, 4),
            "density_pct": round(density, 2),
            "t_wall_mm": t_wall,
            "impact_damping_priority": round(p_norm, 4),
            "softness_priority": round(1 - p_norm, 4),
            "source": "formula",
            "confidence": 0.35,
            "validation_status": "simulation",
            "smoothing_flag": smoothing_flag,
            "failure_flags": failure_flags,
            "baseline_comparison": {
                "baseline_wall_mm": 0.6,
                "delta_from_baseline_mm": round(t_wall - 0.6, 3)
            }
        }
        output.append(rec)
        prev_density = density

    return {
        "schema_version": "v1",
        "subject_id": subject.get("subject_id", "anonymous"),
        "profile_target": profile,
        "profile_priority": bounds.get("priority"),
        "personalization_inputs": subject,
        "zone_outputs": output,
        "model_status": "simulation_ready"
    }

def self_tests(config):
    subjects = [
        {
            "subject_id": "light_user",
            "body_weight_kg": 50,
            "foot_length_mm": 245,
            "foot_width_mm": 88,
            "arch_height_category": "medium",
            "profile_target": "CALM",
            "left_right_balance": 0.0
        },
        {
            "subject_id": "heavy_user",
            "body_weight_kg": 95,
            "foot_length_mm": 285,
            "foot_width_mm": 112,
            "arch_height_category": "low",
            "profile_target": "VITAL",
            "left_right_balance": 0.2
        },
        {
            "subject_id": "lateral_shift_user",
            "body_weight_kg": 72,
            "foot_length_mm": 265,
            "foot_width_mm": 100,
            "arch_height_category": "high",
            "profile_target": "BALANCE",
            "left_right_balance": -0.5
        },
        {
            "subject_id": "focus_user",
            "body_weight_kg": 68,
            "foot_length_mm": 260,
            "foot_width_mm": 96,
            "arch_height_category": "medium",
            "profile_target": "FOCUS",
            "left_right_balance": 0.1
        }
    ]

    for s in subjects:
        result = generate_personalized_map(s, config)
        zones = result["zone_outputs"]
        if len(zones) != 7:
            fail("generated map must contain 7 zones")

        for z in zones:
            if not (0 <= z["P_norm"] <= 1):
                fail("P_norm outside 0..1")
            if z["t_wall_mm"] not in (0.5, 0.6, 0.7):
                fail("invalid t_wall_mm")
            for key in ["source", "confidence", "validation_status", "baseline_comparison"]:
                if key not in z:
                    fail(f"missing required output key: {key}")

    print("PERSONALIZED_MODEL_SELF_TESTS_PASS")

def main():
    if len(sys.argv) < 2:
        fail("missing model json path")

    config = json.loads(Path(sys.argv[1]).read_text(encoding="utf-8"))
    validate_model_config(config)
    self_tests(config)

    sample = {
        "subject_id": "sample_001",
        "body_weight_kg": 70,
        "foot_length_mm": 265,
        "foot_width_mm": 98,
        "arch_height_category": "medium",
        "profile_target": "BALANCE",
        "left_right_balance": 0.15
    }

    out = generate_personalized_map(sample, config)
    out_path = Path("parameters/sample_personalized_pressure_density_output_v1.json")
    out_path.write_text(json.dumps(out, ensure_ascii=False, indent=2), encoding="utf-8")
    print("PERSONALIZED_SAMPLE_OUTPUT_CREATED")
    print(out_path)

if __name__ == "__main__":
    main()

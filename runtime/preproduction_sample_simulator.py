#!/usr/bin/env python3
import json
import re
import sys
from datetime import datetime, timezone
from pathlib import Path

G = 9.80665
BOUNDARY = "Engineering/research simulation only. No approved medical, diagnostic, therapeutic, clinical, or psychological treatment claim."

FORBIDDEN_RE = re.compile(
    r"\b(treat|treats|treatment|cure|cures|diagnose|diagnoses|diagnostic|therapeutic|clinical|medical grade|pain reduction|heals|healing|disease|patient outcome|regulates hormones|hormone regulation|corrects gait|fixes gait)\b",
    re.IGNORECASE,
)

USAGE_PEAK_FACTORS = {
    "daily": 1.25,
    "work": 1.35,
    "standing_long": 1.20,
    "sport": 1.65,
}

VALID_FIT_PREFERENCES = {"soft", "balanced", "firm"}


def load_json(path):
    return json.loads(Path(path).read_text(encoding="utf-8"))


def flatten_strings(value):
    if isinstance(value, str):
        yield value
    elif isinstance(value, dict):
        for v in value.values():
            yield from flatten_strings(v)
    elif isinstance(value, list):
        for v in value:
            yield from flatten_strings(v)


def blocked_claim_hits(data):
    hits = []
    for text in flatten_strings(data):
        for m in FORBIDDEN_RE.finditer(text):
            hits.append({"term": m.group(0), "source_text": text[:220]})
    return hits


def clamp(v, lo, hi):
    return max(lo, min(hi, v))


def wall_from_density(density_pct):
    if density_pct <= 30:
        return 0.5
    if density_pct <= 55:
        return 0.6
    return 0.7


def validate_customer(c):
    height_cm = c.get("height_cm")
    weight_kg = c.get("weight_kg")
    shoe_size = c.get("shoe_size")
    foot_length_mm = c.get("foot_length_mm")
    foot_width_mm = c.get("foot_width_mm")
    usage_mode = c.get("usage_mode", "daily")
    fit_preference = c.get("fit_preference", "balanced")

    errors = []
    if height_cm is None or not (120 <= float(height_cm) <= 230):
        errors.append("height_cm must be within 120..230")
    if weight_kg is None or not (35 <= float(weight_kg) <= 180):
        errors.append("weight_kg must be within 35..180")
    if shoe_size is None or not (30 <= int(shoe_size) <= 52):
        errors.append("shoe_size must be within 30..52")
    if foot_length_mm is None or not (180 <= float(foot_length_mm) <= 340):
        errors.append("foot_length_mm must be within 180..340")
    if foot_width_mm is None or not (60 <= float(foot_width_mm) <= 140):
        errors.append("foot_width_mm must be within 60..140")
    if usage_mode not in USAGE_PEAK_FACTORS:
        errors.append(f"usage_mode must be one of {sorted(USAGE_PEAK_FACTORS)}")
    if fit_preference not in VALID_FIT_PREFERENCES:
        errors.append(f"fit_preference must be one of {sorted(VALID_FIT_PREFERENCES)}")

    if errors:
        raise ValueError("; ".join(errors))

    height_m = float(height_cm) / 100.0
    weight_kg = float(weight_kg)
    body_force_n = weight_kg * G
    peak_load_n = body_force_n * USAGE_PEAK_FACTORS[usage_mode]

    return {
        "height_cm": float(height_cm),
        "height_m": round(height_m, 4),
        "weight_kg": weight_kg,
        "shoe_size": int(shoe_size),
        "foot_length_mm": float(foot_length_mm),
        "foot_width_mm": float(foot_width_mm),
        "usage_mode": usage_mode,
        "fit_preference": fit_preference,
        "bmi_engineering_index": round(weight_kg / (height_m * height_m), 3),
        "body_force_n": round(body_force_n, 3),
        "estimated_peak_load_n": round(peak_load_n, 3),
        "fit_fingerprint": f"ZFP-{int(float(height_cm))}-{int(weight_kg)}-{int(shoe_size)}-{int(float(foot_length_mm))}-{int(float(foot_width_mm))}-{usage_mode}",
    }


def density_bias(customer, zone):
    name = zone["name"]
    bias = 0.0

    if customer["weight_kg"] >= 90 and name in {"heel", "midfoot", "medial_edge", "lateral_edge"}:
        bias += 5.0
    if customer["weight_kg"] >= 110:
        bias += 3.0
    if customer["foot_width_mm"] > 110 and name in {"forefoot", "metatarsal", "lateral_edge"}:
        bias += 3.0
    if customer["foot_width_mm"] < 90 and name in {"forefoot", "toe"}:
        bias -= 2.0
    if customer["usage_mode"] == "sport" and name in {"forefoot", "metatarsal", "toe"}:
        bias += 5.0
    if customer["usage_mode"] == "standing_long" and name in {"heel", "midfoot"}:
        bias += 4.0
    if customer["fit_preference"] == "soft":
        bias -= 3.0
    if customer["fit_preference"] == "firm":
        bias += 3.0

    return bias


def blocked_report(input_data, hits, reason):
    return {
        "schema_version": "v1",
        "project": "ZILFIT",
        "report_type": "preproduction_sample_simulation",
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "sample_id": input_data.get("sample_id", "sample_unknown") if isinstance(input_data, dict) else "sample_unknown",
        "edition": input_data.get("edition", "unknown") if isinstance(input_data, dict) else "unknown",
        "customer_measurement_profile": None,
        "zone_outputs": [],
        "simulation_metrics": {},
        "manufacturing_decision": {
            "status": "blocked",
            "allowed_next_step": "remove_blocked_language_or_fix_input",
            "recommended_sample_count": 0,
            "reason": reason,
        },
        "review_packet": {
            "review_required": True,
            "review_questions": ["Which input wording or measurement should be corrected before engineering simulation?"],
        },
        "blocked_claims": hits,
        "boundary": BOUNDARY,
    }


def simulate(input_data):
    param = load_json("parameters/zilfit_personalized_pressure_density_model_v1.json")
    edition = input_data.get("edition")
    bounds = param["profile_density_bounds"].get(edition)
    if not bounds:
        raise ValueError(f"unknown edition: {edition}")

    customer = validate_customer(input_data.get("customer", {}))
    zones = (
        param.get("foot_zone_model")
        or param.get("zones")
        or param.get("foot_zones")
        or param.get("pressure_zones")
    )
    if not zones:
        raise ValueError("missing foot zone model in personalized pressure-density parameters")

    peak_load_n = customer["estimated_peak_load_n"]
    floor = float(bounds["density_floor_pct"])
    ceiling = float(bounds["density_ceiling_pct"])
    max_jump = float(param["failure_rules"]["max_adjacent_density_jump_pct"])

    outputs = []
    for zone in zones:
        zone_load_n = peak_load_n * float(zone["contact_fraction"]) * float(zone["gait_phase_factor"])
        p_norm = zone_load_n / peak_load_n
        base_density = floor + (ceiling - floor) * min(1.0, p_norm * 5.0)
        density = clamp(base_density + density_bias(customer, zone), floor, ceiling)

        item = {
            "zone_id": zone["zone_id"],
            "zone_name": zone["name"],
            "zone_load_N": round(zone_load_n, 3),
            "P_norm": round(p_norm, 5),
            "density_pct": round(density, 2),
            "t_wall_mm": wall_from_density(density),
            "source": "preproduction_sample_simulator_v1",
            "confidence": 0.72,
            "validation_status": "simulation",
            "failure_flags": [],
            "baseline_comparison": {
                "profile_floor_pct": floor,
                "profile_ceiling_pct": ceiling,
                "priority": bounds["priority"],
            },
        }

        if outputs:
            prev = float(outputs[-1]["density_pct"])
            jump = float(item["density_pct"]) - prev
            if abs(jump) > max_jump:
                adjusted = prev + max_jump if jump > 0 else prev - max_jump
                adjusted = clamp(adjusted, floor, ceiling)
                item["density_pct"] = round(adjusted, 2)
                item["t_wall_mm"] = wall_from_density(adjusted)
                item["failure_flags"].append("density_smoothed_to_adjacent_jump_limit")

        outputs.append(item)

    jumps = [abs(float(outputs[i]["density_pct"]) - float(outputs[i - 1]["density_pct"])) for i in range(1, len(outputs))]
    density_jump_max_pct = round(max(jumps), 2) if jumps else 0.0
    peak_zone = max(outputs, key=lambda z: float(z["zone_load_N"]))

    score = 100
    if density_jump_max_pct > max_jump:
        score -= 35
    if any(float(z["t_wall_mm"]) < 0.5 for z in outputs):
        score -= 30
    if any(z["failure_flags"] for z in outputs):
        score -= 5
    score = max(0, score)

    if score >= 90:
        status = "sample_ready"
    elif score >= 70:
        status = "needs_revision"
    else:
        status = "blocked"

    return {
        "schema_version": "v1",
        "project": "ZILFIT",
        "report_type": "preproduction_sample_simulation",
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "sample_id": input_data.get("sample_id", "sample_unknown"),
        "edition": edition,
        "customer_measurement_profile": customer,
        "zone_outputs": outputs,
        "simulation_metrics": {
            "total_zone_load_N": round(sum(float(z["zone_load_N"]) for z in outputs), 3),
            "peak_pressure_zone": {
                "zone_id": peak_zone["zone_id"],
                "zone_name": peak_zone["zone_name"],
                "zone_load_N": peak_zone["zone_load_N"],
                "density_pct": peak_zone["density_pct"],
                "t_wall_mm": peak_zone["t_wall_mm"],
            },
            "density_jump_max_pct": density_jump_max_pct,
            "manufacturing_readiness_score": score,
        },
        "manufacturing_decision": {
            "status": status,
            "allowed_next_step": "limited_engineering_sample_review" if status == "sample_ready" else "revise_before_sample",
            "recommended_sample_count": 5 if status == "sample_ready" else 0,
        },
        "review_packet": {
            "review_required": True,
            "review_questions": [
                "Are the zone loads and density transitions reasonable for a first physical sample?",
                "Should density or wall thickness be adjusted before printing?",
                "Which objective wear-test measurements should be collected?"
            ],
        },
        "blocked_claims": [],
        "boundary": BOUNDARY,
    }


def main():
    if len(sys.argv) != 3:
        print("Usage: preproduction_sample_simulator.py input.json output.json")
        return 2

    input_path = Path(sys.argv[1])
    output_path = Path(sys.argv[2])

    try:
        data = load_json(input_path)
    except Exception as e:
        report = blocked_report({}, [{"error": str(e)}], "invalid_input_json")
    else:
        hits = blocked_claim_hits(data)
        if hits:
            report = blocked_report(data, hits, "blocked_claim_language_detected")
        else:
            try:
                report = simulate(data)
            except Exception as e:
                report = blocked_report(data, [{"error": str(e)}], "simulation_input_failed")

    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    print(f"PREPRODUCTION_SAMPLE_STATUS={report['manufacturing_decision']['status']}")
    print(f"PREPRODUCTION_SAMPLE_REPORT={output_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

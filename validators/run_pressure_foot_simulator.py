#!/usr/bin/env python3
import json
import sys
from pathlib import Path

ALLOWED_WALLS = {0.5, 0.6, 0.7}
MAX_JUMP = 15.0

PROHIBITED_TERMS = [
    "diagnosis", "treatment", "therapeutic", "medical", "pain",
    "healing", "hormone", "organ", "disease", "cure",
    "يعالج", "علاج", "تشخيص", "ألم", "هرمون", "عضو", "شفاء"
]

def fail(msg):
    print(f"SIMULATION_FAILED: {msg}")
    sys.exit(1)

def load_json(path):
    p = Path(path)
    if not p.exists():
        fail(f"missing file: {path}")
    return json.loads(p.read_text(encoding="utf-8"))

def has_medical_language(obj):
    text = json.dumps(obj, ensure_ascii=False).lower()
    found = []
    for term in PROHIBITED_TERMS:
        if term.lower() in text:
            found.append(term)
    return found

def adjacent_jumps(zones):
    jumps = []
    prev = None
    for z in zones:
        density = float(z["density_pct"])
        if prev is not None:
            jumps.append(abs(density - prev))
        prev = density
    return jumps

def score_from_max_jump(max_jump):
    if max_jump <= 5:
        return 100
    if max_jump <= 10:
        return 85
    if max_jump <= 15:
        return 70
    return max(0, 70 - (max_jump - 15) * 4)

def score_medial_lateral(zones):
    by_id = {z["zone_id"]: z for z in zones}
    medial = by_id.get("Z06", {}).get("density_pct")
    lateral = by_id.get("Z07", {}).get("density_pct")
    if medial is None or lateral is None:
        return 50
    diff = abs(float(medial) - float(lateral))
    return max(0, round(100 - diff * 5, 2))

def score_damping(zones):
    values = [float(z.get("impact_damping_priority", 0)) for z in zones]
    if not values:
        return 0
    avg = sum(values) / len(values)
    return round(100 * avg, 2)

def score_comfort(zones):
    values = [float(z.get("softness_priority", 0)) for z in zones]
    if not values:
        return 0
    avg = sum(values) / len(values)
    return round(100 * avg, 2)

def manufacturing_score(zones, max_jump):
    score = 100
    for z in zones:
        if float(z.get("t_wall_mm", 0)) not in ALLOWED_WALLS:
            score -= 30
        if "baseline_comparison" not in z:
            score -= 15
        if z.get("failure_flags"):
            score -= 10
    if max_jump > MAX_JUMP:
        score -= 30
    return max(0, round(score, 2))

def failure_risk_score(zones, max_jump, prohibited_found):
    risk = 0
    if max_jump > MAX_JUMP:
        risk += 35
    for z in zones:
        if float(z.get("t_wall_mm", 0)) not in ALLOWED_WALLS:
            risk += 25
        if "baseline_comparison" not in z:
            risk += 10
        if z.get("failure_flags"):
            risk += 8
    if prohibited_found:
        risk += 40
    return min(100, risk)

def summarize_map(label, data):
    zones = data.get("zone_outputs", [])
    if len(zones) != 7:
        fail(f"{label}: expected 7 zones")

    loads = [float(z.get("zone_load_N", 0)) for z in zones]
    densities = [float(z.get("density_pct", 0)) for z in zones]
    jumps = adjacent_jumps(zones)
    max_jump = max(jumps) if jumps else 0

    peak_zone = max(zones, key=lambda z: float(z.get("zone_load_N", 0)))

    prohibited = has_medical_language(data)

    mfg = manufacturing_score(zones, max_jump)
    risk = failure_risk_score(zones, max_jump, prohibited)

    result = {
        "label": label,
        "subject_id": data.get("subject_id"),
        "profile_target": data.get("profile_target"),
        "model_status": data.get("model_status"),
        "total_zone_load_N": round(sum(loads), 3),
        "peak_pressure_zone": {
            "zone_id": peak_zone.get("zone_id"),
            "zone_name": peak_zone.get("zone_name"),
            "zone_load_N": peak_zone.get("zone_load_N"),
            "density_pct": peak_zone.get("density_pct"),
            "t_wall_mm": peak_zone.get("t_wall_mm")
        },
        "density_min_pct": round(min(densities), 2),
        "density_max_pct": round(max(densities), 2),
        "density_jump_max_pct": round(max_jump, 2),
        "heel_to_toe_transition_score": round(score_from_max_jump(max_jump), 2),
        "medial_lateral_balance_score": score_medial_lateral(zones),
        "damping_distribution_score": score_damping(zones),
        "comfort_distribution_score": score_comfort(zones),
        "manufacturing_readiness_score": mfg,
        "failure_risk_score": risk,
        "prohibited_language_found": prohibited,
        "pass_fail": {
            "density_jump_pass": max_jump <= MAX_JUMP,
            "manufacturing_ready_pass": mfg >= 70,
            "failure_risk_pass": risk <= 35,
            "non_medical_language_pass": not prohibited
        }
    }
    return result

def compare(original, smoothed):
    return {
        "density_jump_delta_pct": round(original["density_jump_max_pct"] - smoothed["density_jump_max_pct"], 2),
        "manufacturing_readiness_delta": round(smoothed["manufacturing_readiness_score"] - original["manufacturing_readiness_score"], 2),
        "failure_risk_delta": round(original["failure_risk_score"] - smoothed["failure_risk_score"], 2),
        "smoothing_effective": smoothed["density_jump_max_pct"] <= 15 and smoothed["density_jump_max_pct"] <= original["density_jump_max_pct"]
    }

def main():
    config = load_json("parameters/zilfit_pressure_foot_simulator_v1.json")
    original = load_json(config["input_files"]["original_map"])
    smoothed = load_json(config["input_files"]["smoothed_map"])

    original_summary = summarize_map("original_personalized_map", original)
    smoothed_summary = summarize_map("smoothed_personalized_map", smoothed)
    comparison = compare(original_summary, smoothed_summary)

    overall_pass = all([
        smoothed_summary["pass_fail"]["density_jump_pass"],
        smoothed_summary["pass_fail"]["manufacturing_ready_pass"],
        smoothed_summary["pass_fail"]["failure_risk_pass"],
        smoothed_summary["pass_fail"]["non_medical_language_pass"]
    ])

    report = {
        "schema_version": "v1",
        "module_id": "zilfit_pressure_foot_simulator_report",
        "project": "ZILFIT",
        "test_id": "first_pressure_foot_simulation_case_001",
        "status": "PASS" if overall_pass else "FAIL",
        "review_target": "claude_final_review",
        "original_summary": original_summary,
        "smoothed_summary": smoothed_summary,
        "comparison": comparison,
        "engineering_verdict": {
            "ready_for_claude_review": True,
            "ready_for_pressure_simulator_iteration_2": overall_pass,
            "ready_for_coupon_test": False,
            "ready_for_physical_prototype": False,
            "reason": "simulation-only first pass; requires external review and later coupon validation"
        }
    }

    out_json = Path("simulation_reports/pressure_foot_simulator_case_001_report_v1.json")
    out_md = Path("simulation_reports/pressure_foot_simulator_case_001_summary_v1.md")

    out_json.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")

    md = f"""# ZILFIT Pressure Foot Simulator — Case 001 Summary

## Status
{report["status"]}

## Profile
{smoothed_summary["profile_target"]}

## Subject
{smoothed_summary["subject_id"]}

## Main Result
- Original max density jump: {original_summary["density_jump_max_pct"]}%
- Smoothed max density jump: {smoothed_summary["density_jump_max_pct"]}%
- Smoothing effective: {comparison["smoothing_effective"]}
- Manufacturing readiness score: {smoothed_summary["manufacturing_readiness_score"]}
- Failure risk score: {smoothed_summary["failure_risk_score"]}
- Non-medical language pass: {smoothed_summary["pass_fail"]["non_medical_language_pass"]}

## Peak Pressure Zone
- Zone: {smoothed_summary["peak_pressure_zone"]["zone_id"]} / {smoothed_summary["peak_pressure_zone"]["zone_name"]}
- Load N: {smoothed_summary["peak_pressure_zone"]["zone_load_N"]}
- Density %: {smoothed_summary["peak_pressure_zone"]["density_pct"]}
- Wall mm: {smoothed_summary["peak_pressure_zone"]["t_wall_mm"]}

## Engineering Verdict
- Ready for Claude final review: YES
- Ready for simulator iteration 2: {"YES" if overall_pass else "NO"}
- Ready for coupon test: NO
- Ready for physical prototype: NO

## Boundary
This report is for footwear pressure-density engineering review only. It makes no medical, diagnostic, treatment, pain, hormone, organ, disease, or therapeutic claims.
"""
    out_md.write_text(md, encoding="utf-8")

    print("PRESSURE_FOOT_SIMULATOR_REPORT_PASS" if overall_pass else "PRESSURE_FOOT_SIMULATOR_REPORT_FAIL")
    print(out_json)
    print(out_md)

if __name__ == "__main__":
    main()

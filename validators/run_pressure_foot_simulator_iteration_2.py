#!/usr/bin/env python3
import json
from pathlib import Path

ALLOWED_WALLS = {0.5, 0.6, 0.7}
MAX_JUMP = 15.0

ZONES = [
    ("Z01", "heel"),
    ("Z02", "arch_midfoot"),
    ("Z03", "metatarsal"),
    ("Z04", "forefoot"),
    ("Z05", "toe"),
    ("Z06", "medial_edge"),
    ("Z07", "lateral_edge"),
]

CASES = [
    {
        "case_id": "simulator_iteration_2_case_001",
        "sample_type": "balanced sample",
        "profile_target": "BALANCE",
        "density_floor_pct": 21,
        "density_ceiling_pct": 56,
        "loads": [187.0, 93.0, 126.0, 118.0, 62.0, 71.0, 70.0],
    },
    {
        "case_id": "simulator_iteration_2_case_002",
        "sample_type": "high heel-load sample",
        "profile_target": "CALM",
        "density_floor_pct": 20,
        "density_ceiling_pct": 52,
        "loads": [250.0, 84.0, 92.0, 88.0, 45.0, 62.0, 58.0],
    },
    {
        "case_id": "simulator_iteration_2_case_003",
        "sample_type": "high forefoot/metatarsal-load sample",
        "profile_target": "FOCUS",
        "density_floor_pct": 22,
        "density_ceiling_pct": 58,
        "loads": [110.0, 70.0, 225.0, 207.0, 98.0, 76.0, 72.0],
    },
]


def clamp(v, lo, hi):
    return max(lo, min(hi, v))


def density_to_wall(d):
    if d <= 30:
        return 0.5
    if d <= 55:
        return 0.6
    return 0.7


def smooth_densities(raw):
    out = [round(raw[0], 2)]
    for value in raw[1:]:
        prev = out[-1]
        if abs(value - prev) <= MAX_JUMP:
            out.append(round(value, 2))
        elif value > prev:
            out.append(round(prev + MAX_JUMP, 2))
        else:
            out.append(round(prev - MAX_JUMP, 2))
    return out


def max_adjacent_jump(values):
    return max(abs(values[i] - values[i - 1]) for i in range(1, len(values)))


def build_case(case):
    loads = case["loads"]
    min_load = min(loads)
    max_load = max(loads)
    denom = max_load - min_load

    raw_densities = []
    p_norms = []
    for load in loads:
        p_norm = 0.5 if denom == 0 else clamp((load - min_load) / denom, 0.0, 1.0)
        p_norms.append(round(p_norm, 6))
        density = clamp(
            case["density_floor_pct"] + (case["density_ceiling_pct"] - case["density_floor_pct"]) * p_norm,
            case["density_floor_pct"],
            case["density_ceiling_pct"],
        )
        raw_densities.append(round(density, 2))

    smoothed = smooth_densities(raw_densities)

    zone_outputs = []
    for i, (zone_id, zone_name) in enumerate(ZONES):
        d = smoothed[i]
        zone_outputs.append(
            {
                "zone_id": zone_id,
                "zone_name": zone_name,
                "zone_load_N": loads[i],
                "P_norm": p_norms[i],
                "raw_density_pct": raw_densities[i],
                "density_pct": d,
                "t_wall_mm": density_to_wall(d),
                "smoothing_applied": raw_densities[i] != d,
            }
        )

    peak = max(zone_outputs, key=lambda z: z["zone_load_N"])
    max_jump = round(max_adjacent_jump([z["density_pct"] for z in zone_outputs]), 2)

    checks = {
        "density_in_allowed_range": all(
            case["density_floor_pct"] <= z["density_pct"] <= case["density_ceiling_pct"] for z in zone_outputs
        ),
        "wall_thickness_allowed_set": all(z["t_wall_mm"] in ALLOWED_WALLS for z in zone_outputs),
        "adjacent_density_jump_within_threshold": max_jump <= MAX_JUMP,
        "valid_p_norm_no_division_by_zero": all(0.0 <= z["P_norm"] <= 1.0 for z in zone_outputs),
        "peak_pressure_zone_detected": bool(peak["zone_id"]),
    }
    checks["all_checks_pass"] = all(checks.values())

    return {
        "schema_version": "v1",
        "module_id": "zilfit_pressure_foot_simulator_iteration_2",
        "project": "ZILFIT",
        "case_id": case["case_id"],
        "sample_type": case["sample_type"],
        "profile_target": case["profile_target"],
        "density_bounds_pct": {
            "floor": case["density_floor_pct"],
            "ceiling": case["density_ceiling_pct"],
        },
        "max_adjacent_density_jump_allowed_pct": MAX_JUMP,
        "peak_pressure_zone": {
            "zone_id": peak["zone_id"],
            "zone_name": peak["zone_name"],
            "zone_load_N": peak["zone_load_N"],
        },
        "max_adjacent_density_jump_pct": max_jump,
        "pass_fail_flags": checks,
        "zone_outputs": zone_outputs,
        "boundary": "Footwear pressure-density engineering only. No clinical or therapeutic claims.",
    }


def main():
    report_dir = Path("simulation_reports")
    report_dir.mkdir(parents=True, exist_ok=True)

    generated = []
    for case in CASES:
        payload = build_case(case)
        out = report_dir / f"{case['case_id']}.json"
        out.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
        generated.append(payload)

    all_pass = all(c["pass_fail_flags"]["all_checks_pass"] for c in generated)
    summary = [
        "# ZILFIT Simulator Iteration 2 Summary",
        "",
        f"Overall status: {'PASS' if all_pass else 'FAIL'}",
        "",
        "| Case | Sample | Peak Zone | Max Jump % | All Checks Pass |",
        "|---|---|---|---:|---|",
    ]

    for c in generated:
        summary.append(
            f"| {c['case_id']} | {c['sample_type']} | {c['peak_pressure_zone']['zone_id']} ({c['peak_pressure_zone']['zone_name']}) | {c['max_adjacent_density_jump_pct']} | {c['pass_fail_flags']['all_checks_pass']} |"
        )

    summary.extend([
        "",
        "Boundary: Footwear pressure-density engineering only. No medical, diagnostic, treatment, disease, organ, hormone, therapeutic, or pain claims.",
    ])

    (report_dir / "simulator_iteration_2_summary.md").write_text("\n".join(summary) + "\n", encoding="utf-8")
    print("SIMULATOR_ITERATION_2_PASS" if all_pass else "SIMULATOR_ITERATION_2_FAIL")


if __name__ == "__main__":
    main()

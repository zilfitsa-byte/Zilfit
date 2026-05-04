"""
ZILFIT Sample Readiness Engine v1

Converts computed LiveFit scan output into an early physical sample
readiness decision for engineering sampling.

Engineering simulation only.
No medical, diagnostic, therapeutic, clinical, treatment, pain, disease, or cure claims.
"""

import json
import sys
import os

BOUNDARY = (
    "Engineering simulation only. "
    "No medical, diagnostic, therapeutic, clinical, treatment, pain, disease, or cure claims."
)

VALID_LENGTH_MM = (180, 340)
VALID_WIDTH_MM = (60, 130)
VALID_ARCH_INDEX = (0.0, 1.0)


def emit(result, exit_code):
    print(json.dumps(result, indent=2))
    sys.exit(exit_code)


def load_json(path):
    if not os.path.isfile(path):
        emit({
            "status": "error",
            "error": f"File not found: {path}",
            "boundary": BOUNDARY,
        }, 1)

    with open(path) as f:
        try:
            return json.load(f)
        except json.JSONDecodeError as e:
            emit({
                "status": "error",
                "error": f"Invalid JSON: {e}",
                "boundary": BOUNDARY,
            }, 1)


def in_range(value, bounds):
    return isinstance(value, (int, float)) and bounds[0] <= value <= bounds[1]


def compute_sample_readiness(payload):
    notes = []

    confidence = payload.get("computed_confidence")
    decision = payload.get("computed_decision_status")
    measurements = payload.get("measurements", {})

    length = measurements.get("estimated_foot_length_mm")
    width = measurements.get("estimated_foot_width_mm")
    arch = measurements.get("estimated_arch_index")

    if not isinstance(confidence, (int, float)):
        return "needs_rescan", ["missing or invalid computed_confidence"]

    if decision not in {"pass", "review_required", "rejected"}:
        return "needs_rescan", ["missing or invalid computed_decision_status"]

    if not in_range(length, VALID_LENGTH_MM):
        notes.append("estimated_foot_length_mm outside engineering range")

    if not in_range(width, VALID_WIDTH_MM):
        notes.append("estimated_foot_width_mm outside engineering range")

    if not in_range(arch, VALID_ARCH_INDEX):
        notes.append("estimated_arch_index outside engineering range")

    if decision == "rejected":
        notes.append("computed_decision_status is rejected")
        return "needs_rescan", notes

    if notes:
        return "manual_review", notes

    if decision == "review_required":
        notes.append("computed_decision_status is review_required")
        return "manual_review", notes

    return "sample_ready", ["computed scan output is ready for early engineering sample grouping"]


def run(path):
    payload = load_json(path)
    status, notes = compute_sample_readiness(payload)

    emit({
        "readiness_type": "zilfit_sample_readiness",
        "schema_version": "1",
        "sample_readiness_status": status,
        "computed_confidence": payload.get("computed_confidence"),
        "computed_decision_status": payload.get("computed_decision_status"),
        "measurements": payload.get("measurements", {}),
        "readiness_notes": notes,
        "boundary": BOUNDARY,
    }, 0 if status in {"sample_ready", "manual_review"} else 1)


if __name__ == "__main__":
    if len(sys.argv) != 2:
        emit({
            "status": "error",
            "error": "Usage: python3 compute_z_livefit_sample_readiness_v1.py <computed_scan_output.json>",
            "boundary": BOUNDARY,
        }, 1)

    run(sys.argv[1])

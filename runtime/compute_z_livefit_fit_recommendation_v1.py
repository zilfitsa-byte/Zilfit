"""
ZILFIT Fit Recommendation Engine v1

Transforms LiveFit engineering measurements into non-medical footwear fit
recommendation bands for early product sampling.

Engineering simulation only.
No medical, diagnostic, therapeutic, clinical, treatment, pain, disease, or cure claims.
"""

import json
import sys
import os

BOUNDARY = (
    "Engineering simulation only. "
    "No medical, diagnostic, therapeutic, clinical, treatment, "
    "pain, disease, or cure claims."
)

FORBIDDEN_TERMS = [
    "treat", "treatment", "cure", "diagnose", "diagnosis", "diagnostic",
    "medical", "clinical", "therapeutic", "pain reduction", "correct gait",
    "fix gait", "hormone", "disease", "patient outcome", "healing", "patient",
    "pain",
]


def emit(result, exit_code=0):
    print(json.dumps(result, indent=2))
    sys.exit(exit_code)


def load_json(path):
    if not os.path.isfile(path):
        emit({"status": "error", "error": f"File not found: {path}", "boundary": BOUNDARY}, 1)

    with open(path) as f:
        try:
            return json.load(f)
        except json.JSONDecodeError as e:
            emit({"status": "error", "error": f"Invalid JSON: {e}", "boundary": BOUNDARY}, 1)


def check_forbidden(payload):
    # Do not scan safety boundary/notes because they intentionally contain
    # forbidden medical terms as disclaimers. Scan only user/input payload fields.
    cleaned = dict(payload)
    cleaned.pop("boundary", None)
    cleaned.pop("engineering_notes", None)
    cleaned.pop("notes", None)
    text = json.dumps(cleaned).lower()
    return [term for term in FORBIDDEN_TERMS if term in text]


def extract_measurements(payload):
    measurements = payload.get("measurements", payload)

    required = [
        "estimated_foot_length_mm",
        "estimated_foot_width_mm",
        "estimated_arch_index",
    ]

    missing = [field for field in required if field not in measurements]
    if missing:
        emit({
            "status": "rejected",
            "reason": "missing_measurements",
            "missing": missing,
            "boundary": BOUNDARY,
        }, 1)

    return measurements


def size_band(length_mm):
    if length_mm < 240:
        return "sample_small"
    if length_mm < 270:
        return "sample_medium"
    if length_mm <= 305:
        return "sample_large"
    return "outside_current_sample_range"


def width_category(width_mm):
    if width_mm < 85:
        return "narrow"
    if width_mm <= 102:
        return "standard"
    if width_mm <= 112:
        return "wide"
    return "extra_wide"


def arch_support_category(arch_index):
    if arch_index < 0.28:
        return "low_arch_band"
    if arch_index <= 0.55:
        return "mid_arch_band"
    return "high_arch_band"


def sample_readiness(length_mm, width_mm, arch_index, confidence):
    if confidence is not None and confidence < 0.75:
        return "review_required"

    if not (220 <= length_mm <= 305):
        return "review_required"

    if not (70 <= width_mm <= 120):
        return "review_required"

    if not (0.0 <= arch_index <= 1.0):
        return "review_required"

    return "sample_candidate"


def recommend(payload):
    found = check_forbidden(payload)
    if found:
        emit({
            "status": "rejected",
            "reason": "forbidden_terms_detected",
            "forbidden_terms_found": found,
            "boundary": BOUNDARY,
        }, 1)

    measurements = extract_measurements(payload)

    length = float(measurements["estimated_foot_length_mm"])
    width = float(measurements["estimated_foot_width_mm"])
    arch = float(measurements["estimated_arch_index"])

    confidence = payload.get("computed_confidence")
    if confidence is not None:
        confidence = float(confidence)

    recommendation = {
        "recommendation_type": "zilfit_fit_recommendation",
        "schema_version": "1",
        "fit_status": sample_readiness(length, width, arch, confidence),
        "recommended_size_band": size_band(length),
        "width_category": width_category(width),
        "arch_support_category": arch_support_category(arch),
        "input_measurements": {
            "estimated_foot_length_mm": length,
            "estimated_foot_width_mm": width,
            "estimated_arch_index": arch,
        },
        "confidence_context": {
            "computed_confidence": confidence,
            "computed_decision_status": payload.get("computed_decision_status"),
        },
        "engineering_notes": [
            "Recommendation is for early engineering sample grouping only.",
            "No medical, diagnostic, therapeutic, clinical, treatment, pain, disease, or cure claims.",
        ],
        "boundary": BOUNDARY,
    }

    emit(recommendation, 0)


if __name__ == "__main__":
    if len(sys.argv) != 2:
        emit({
            "status": "error",
            "error": "Usage: python3 compute_z_livefit_fit_recommendation_v1.py <profile_or_auto_output.json>",
            "boundary": BOUNDARY,
        }, 1)

    recommend(load_json(sys.argv[1]))

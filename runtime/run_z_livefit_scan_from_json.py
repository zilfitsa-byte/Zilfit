"""
ZILFIT LiveFit Scan — JSON Runtime Simulator
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

REQUIRED_FIELDS = [
    "report_type",
    "manual_photo_capture",
    "hardware_required",
    "stream_ready",
    "foot_detected",
    "floor_plane_anchor",
    "stable_frame_count",
    "lighting_quality",
    "occlusion_detected",
    "optional_depth_sensor",
    "estimated_foot_length_mm",
    "estimated_foot_width_mm",
    "estimated_arch_index",
    "scan_confidence",
    "decision_status",
]

FORBIDDEN_TERMS = [
    "treat", "treatment", "cure", "diagnose", "diagnosis", "diagnostic",
    "medical", "clinical", "therapeutic", "pain reduction", "correct gait",
    "fix gait", "hormone", "disease", "patient outcome", "healing",
]


def load_profile(path):
    if not os.path.isfile(path):
        return None, f"File not found: {path}"
    with open(path, "r") as f:
        try:
            data = json.load(f)
        except json.JSONDecodeError as e:
            return None, f"Invalid JSON: {e}"
    return data, None


def check_forbidden(profile):
    text = json.dumps(profile).lower()
    found = [t for t in FORBIDDEN_TERMS if t in text]
    return found


def validate_hard_constraints(profile):
    errors = []
    if profile.get("report_type") != "livefit_scan_profile":
        errors.append("report_type must be livefit_scan_profile")
    if profile.get("manual_photo_capture") is not False:
        errors.append("manual_photo_capture must be false")
    if profile.get("hardware_required") is not False:
        errors.append("hardware_required must be false")
    for field in REQUIRED_FIELDS:
        if field not in profile:
            errors.append(f"Missing required field: {field}")
    return errors


def compute_decision(profile):
    if not profile.get("foot_detected", False):
        return "rejected", "foot_detected is false"
    confidence = profile.get("scan_confidence", 0.0)
    if confidence >= 0.85:
        return "pass", None
    elif confidence >= 0.75:
        return "review_required", "scan_confidence in review band 0.75-0.84"
    else:
        return "rejected", f"scan_confidence {confidence} below 0.75"


def run(path):
    profile, load_error = load_profile(path)
    if load_error:
        result = {
            "status": "error",
            "error": load_error,
            "boundary": BOUNDARY,
        }
        print(json.dumps(result, indent=2))
        sys.exit(1)

    forbidden = check_forbidden(profile)
    if forbidden:
        result = {
            "status": "rejected",
            "reason": "forbidden_terms_detected",
            "forbidden_terms_found": forbidden,
            "boundary": BOUNDARY,
        }
        print(json.dumps(result, indent=2))
        sys.exit(1)

    hard_errors = validate_hard_constraints(profile)
    if hard_errors:
        result = {
            "status": "rejected",
            "reason": "hard_constraint_violation",
            "errors": hard_errors,
            "boundary": BOUNDARY,
        }
        print(json.dumps(result, indent=2))
        sys.exit(1)

    expected_decision, reason = compute_decision(profile)
    declared_decision = profile.get("decision_status")
    decision_match = declared_decision == expected_decision

    quality_flags = {
        "stream_ready": profile.get("stream_ready"),
        "foot_detected": profile.get("foot_detected"),
        "floor_plane_anchor": profile.get("floor_plane_anchor"),
        "stable_frame_count": profile.get("stable_frame_count"),
        "lighting_quality": profile.get("lighting_quality"),
        "occlusion_detected": profile.get("occlusion_detected"),
        "optional_depth_sensor": profile.get("optional_depth_sensor"),
    }

    measurements = {
        "estimated_foot_length_mm": profile.get("estimated_foot_length_mm"),
        "estimated_foot_width_mm": profile.get("estimated_foot_width_mm"),
        "estimated_arch_index": profile.get("estimated_arch_index"),
    }

    result = {
        "report_type": profile.get("report_type"),
        "scan_confidence": profile.get("scan_confidence"),
        "declared_decision_status": declared_decision,
        "computed_decision_status": expected_decision,
        "decision_match": decision_match,
        "decision_reason": reason,
        "measurements": measurements,
        "quality_flags": quality_flags,
        "boundary": BOUNDARY,
    }

    exit_code = 0 if decision_match else 1
    print(json.dumps(result, indent=2))
    sys.exit(exit_code)


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print(json.dumps({
            "status": "error",
            "error": "Usage: python3 run_z_livefit_scan_from_json.py <profile.json>",
            "boundary": BOUNDARY,
        }, indent=2))
        sys.exit(1)
    run(sys.argv[1])

"""
ZILFIT LiveFit Scan — Auto Stream Runner v2
Derives scan_confidence from signal fields using the deterministic
compute_z_livefit_stream_confidence_v2 formula.
scan_confidence and decision_status do not need to be declared in input.
Engineering simulation only.
No medical, diagnostic, therapeutic, clinical, treatment, pain, disease, or cure claims.
"""

import json
import sys
import os

_HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, _HERE)
from compute_z_livefit_stream_confidence_v2 import compute_confidence, compute_decision

BOUNDARY = (
    "Engineering simulation only. "
    "No medical, diagnostic, therapeutic, clinical, treatment, "
    "pain, disease, or cure claims."
)

REQUIRED_FIELDS = [
    "report_type",
    "schema_version",
    "manual_photo_capture",
    "hardware_required",
    "stream_ready",
    "foot_detected",
    "floor_plane_anchor",
    "stable_frame_count",
    "lighting_quality",
    "occlusion_detected",
    "optional_depth_sensor",
    "camera_angle_quality",
    "motion_blur_score",
    "scale_anchor_confidence",
    "frame_consistency_score",
    "estimated_foot_length_mm",
    "estimated_foot_width_mm",
    "estimated_arch_index",
]

FORBIDDEN_TERMS = [
    "treat", "treatment", "cure", "diagnose", "diagnosis", "diagnostic",
    "medical", "clinical", "therapeutic", "pain reduction", "correct gait",
    "fix gait", "hormone", "disease", "patient outcome", "healing", "patient",
    "pain",
]


def emit(result, exit_code):
    print(json.dumps(result, indent=2))
    sys.exit(exit_code)


def load_profile(path):
    if not os.path.isfile(path):
        emit({"status": "error", "error": f"File not found: {path}",
              "boundary": BOUNDARY}, 1)
    with open(path) as f:
        try:
            return json.load(f)
        except json.JSONDecodeError as e:
            emit({"status": "error", "error": f"Invalid JSON: {e}",
                  "boundary": BOUNDARY}, 1)


def check_forbidden(profile):
    text = json.dumps(profile).lower()
    return [t for t in FORBIDDEN_TERMS if t in text]


def validate_hard_constraints(profile):
    errors = []
    if profile.get("report_type") != "livefit_scan_profile":
        errors.append("report_type must be livefit_scan_profile")
    if str(profile.get("schema_version")) != "2":
        errors.append("schema_version must be 2")
    if profile.get("manual_photo_capture") is not False:
        errors.append("manual_photo_capture must be false")
    if profile.get("hardware_required") is not False:
        errors.append("hardware_required must be false")
    missing = [f for f in REQUIRED_FIELDS if f not in profile]
    if missing:
        errors.append(f"Missing required fields: {missing}")
    return errors


def run(path):
    profile = load_profile(path)

    found = check_forbidden(profile)
    if found:
        emit({
            "status": "rejected",
            "reason": "forbidden_terms_detected",
            "forbidden_terms_found": found,
            "boundary": BOUNDARY,
        }, 1)

    errors = validate_hard_constraints(profile)
    if errors:
        emit({
            "status": "rejected",
            "reason": "hard_constraint_violation",
            "errors": errors,
            "boundary": BOUNDARY,
        }, 1)

    conf_result = compute_confidence(
        frame_consistency_score=profile["frame_consistency_score"],
        scale_anchor_confidence=profile["scale_anchor_confidence"],
        motion_blur_score=profile["motion_blur_score"],
        stable_frame_count=profile["stable_frame_count"],
        camera_angle_quality=profile["camera_angle_quality"],
    )

    computed_confidence = conf_result["computed_confidence"]

    decision, reason = compute_decision(
        confidence=computed_confidence,
        foot_detected=profile["foot_detected"],
        stream_ready=profile["stream_ready"],
    )

    emit({
        "report_type": profile["report_type"],
        "schema_version": profile["schema_version"],
        "computed_confidence": computed_confidence,
        "computed_decision_status": decision,
        "decision_reason": reason,
        "signal_contributions": conf_result["signal_contributions"],
        "angle_score": conf_result["angle_score"],
        "stable_frame_normalized": conf_result["stable_frame_normalized"],
        "motion_blur_inverted": conf_result["motion_blur_inverted"],
        "measurements": {
            "estimated_foot_length_mm": profile["estimated_foot_length_mm"],
            "estimated_foot_width_mm": profile["estimated_foot_width_mm"],
            "estimated_arch_index": profile["estimated_arch_index"],
        },
        "quality_flags": {
            "stream_ready": profile["stream_ready"],
            "foot_detected": profile["foot_detected"],
            "floor_plane_anchor": profile["floor_plane_anchor"],
            "lighting_quality": profile["lighting_quality"],
            "occlusion_detected": profile["occlusion_detected"],
            "optional_depth_sensor": profile["optional_depth_sensor"],
        },
        "boundary": BOUNDARY,
    }, 0)


if __name__ == "__main__":
    if len(sys.argv) != 2:
        emit({
            "status": "error",
            "error": "Usage: python3 run_z_livefit_stream_scan_v2_auto.py <profile.json>",
            "boundary": BOUNDARY,
        }, 1)
    run(sys.argv[1])

"""
ZILFIT LiveFit Scan — Stream Runtime Simulator v2
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
    "scan_confidence",
    "decision_status",
]

FORBIDDEN_TERMS = [
    "treat", "treatment", "cure", "diagnose", "diagnosis", "diagnostic",
    "medical", "clinical", "therapeutic", "pain reduction", "correct gait",
    "fix gait", "hormone", "disease", "patient outcome", "healing",
]


def emit(result, exit_code):
    print(json.dumps(result, indent=2))
    sys.exit(exit_code)


def load_profile(path):
    if not os.path.isfile(path):
        emit({"status": "error", "error": f"File not found: {path}", "boundary": BOUNDARY}, 1)
    with open(path) as f:
        try:
            return json.load(f)
        except json.JSONDecodeError as e:
            emit({"status": "error", "error": f"Invalid JSON: {e}", "boundary": BOUNDARY}, 1)


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
        errors.append("manual_photo_capture must be false — live stream only")
    if profile.get("hardware_required") is not False:
        errors.append("hardware_required must be false")
    missing = [f for f in REQUIRED_FIELDS if f not in profile]
    if missing:
        errors.append(f"Missing required fields: {missing}")
    return errors


def compute_stream_flags(profile):
    """
    Evaluate per-signal quality flags from stream fields.
    Returns a dict of flag name -> pass/warn/fail and a list of active warnings.
    """
    flags = {}
    warnings = []

    if not profile.get("stream_ready", False):
        flags["stream_ready"] = "fail"
        warnings.append("stream_ready is false")
    else:
        flags["stream_ready"] = "pass"

    if not profile.get("foot_detected", False):
        flags["foot_detected"] = "fail"
        warnings.append("foot_detected is false — scan unusable")
    else:
        flags["foot_detected"] = "pass"

    frame_count = profile.get("stable_frame_count", 0)
    if frame_count >= 10:
        flags["stable_frame_count"] = "pass"
    elif frame_count >= 5:
        flags["stable_frame_count"] = "warn"
        warnings.append(f"stable_frame_count {frame_count} is in review band (5-9)")
    else:
        flags["stable_frame_count"] = "fail"
        warnings.append(f"stable_frame_count {frame_count} is below minimum (5)")

    blur = profile.get("motion_blur_score", 1.0)
    if blur <= 0.2:
        flags["motion_blur_score"] = "pass"
    elif blur <= 0.5:
        flags["motion_blur_score"] = "warn"
        warnings.append(f"motion_blur_score {blur} is elevated")
    else:
        flags["motion_blur_score"] = "fail"
        warnings.append(f"motion_blur_score {blur} exceeds acceptable threshold")

    scale_conf = profile.get("scale_anchor_confidence", 0.0)
    if scale_conf >= 0.80:
        flags["scale_anchor_confidence"] = "pass"
    elif scale_conf >= 0.60:
        flags["scale_anchor_confidence"] = "warn"
        warnings.append(f"scale_anchor_confidence {scale_conf} is in review band")
    else:
        flags["scale_anchor_confidence"] = "fail"
        warnings.append(f"scale_anchor_confidence {scale_conf} is too low")

    frame_cons = profile.get("frame_consistency_score", 0.0)
    if frame_cons >= 0.80:
        flags["frame_consistency_score"] = "pass"
    elif frame_cons >= 0.60:
        flags["frame_consistency_score"] = "warn"
        warnings.append(f"frame_consistency_score {frame_cons} is in review band")
    else:
        flags["frame_consistency_score"] = "fail"
        warnings.append(f"frame_consistency_score {frame_cons} is too low")

    angle = profile.get("camera_angle_quality", "poor")
    if angle == "optimal":
        flags["camera_angle_quality"] = "pass"
    elif angle == "acceptable":
        flags["camera_angle_quality"] = "warn"
        warnings.append("camera_angle_quality is acceptable — not optimal")
    else:
        flags["camera_angle_quality"] = "fail"
        warnings.append("camera_angle_quality is poor")

    lighting = profile.get("lighting_quality", "poor")
    if lighting == "good":
        flags["lighting_quality"] = "pass"
    elif lighting == "acceptable":
        flags["lighting_quality"] = "warn"
        warnings.append("lighting_quality is acceptable — not ideal")
    else:
        flags["lighting_quality"] = "fail"
        warnings.append("lighting_quality is poor")

    if profile.get("occlusion_detected", False):
        flags["occlusion_detected"] = "warn"
        warnings.append("occlusion_detected is true")
    else:
        flags["occlusion_detected"] = "pass"

    return flags, warnings


def compute_decision(profile):
    if not profile.get("foot_detected", False):
        return "rejected", "foot_detected is false"
    if not profile.get("stream_ready", False):
        return "rejected", "stream_ready is false"
    confidence = profile.get("scan_confidence", 0.0)
    if confidence >= 0.85:
        return "pass", None
    elif confidence >= 0.75:
        return "review_required", f"scan_confidence {confidence} in review band 0.75-0.84"
    else:
        return "rejected", f"scan_confidence {confidence} below 0.75"


def run(path):
    profile = load_profile(path)

    forbidden = check_forbidden(profile)
    if forbidden:
        emit({
            "status": "rejected",
            "reason": "forbidden_terms_detected",
            "forbidden_terms_found": forbidden,
            "boundary": BOUNDARY,
        }, 1)

    hard_errors = validate_hard_constraints(profile)
    if hard_errors:
        emit({
            "status": "rejected",
            "reason": "hard_constraint_violation",
            "errors": hard_errors,
            "boundary": BOUNDARY,
        }, 1)

    stream_flags, warnings = compute_stream_flags(profile)
    expected_decision, reason = compute_decision(profile)
    declared_decision = profile.get("decision_status")
    decision_match = declared_decision == expected_decision

    result = {
        "report_type": profile.get("report_type"),
        "schema_version": profile.get("schema_version"),
        "scan_confidence": profile.get("scan_confidence"),
        "declared_decision_status": declared_decision,
        "computed_decision_status": expected_decision,
        "decision_match": decision_match,
        "decision_reason": reason,
        "stream_quality_flags": stream_flags,
        "stream_warnings": warnings,
        "measurements": {
            "estimated_foot_length_mm": profile.get("estimated_foot_length_mm"),
            "estimated_foot_width_mm": profile.get("estimated_foot_width_mm"),
            "estimated_arch_index": profile.get("estimated_arch_index"),
        },
        "boundary": BOUNDARY,
    }

    emit(result, 0 if decision_match else 1)


if __name__ == "__main__":
    if len(sys.argv) != 2:
        emit({
            "status": "error",
            "error": "Usage: python3 run_z_livefit_stream_scan_v2.py <profile.json>",
            "boundary": BOUNDARY,
        }, 1)
    run(sys.argv[1])

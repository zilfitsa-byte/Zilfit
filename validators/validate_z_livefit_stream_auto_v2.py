"""
ZILFIT LiveFit Scan Stream Auto Validator v2
Accepts signal-only profile. Computes confidence and decision internally.
Does not require scan_confidence or decision_status in input.
Engineering simulation only.
No medical, diagnostic, therapeutic, clinical, treatment, pain, disease, or cure claims.
"""

import json
import sys
import os

_HERE = os.path.dirname(os.path.abspath(__file__))
_RUNTIME = os.path.join(os.path.dirname(_HERE), "runtime")
sys.path.insert(0, _RUNTIME)
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

VALID_LIGHTING = {"good", "acceptable", "poor"}
VALID_ANGLE = {"optimal", "acceptable", "poor"}


def fail(reason, errors=None):
    out = {"validation": "FAIL", "reason": reason, "boundary": BOUNDARY}
    if errors:
        out["errors"] = errors
    print(json.dumps(out, indent=2))
    sys.exit(1)


def ok(computed_confidence, computed_decision, notes=None):
    out = {
        "validation": "PASS",
        "computed_confidence": computed_confidence,
        "computed_decision_status": computed_decision,
        "boundary": BOUNDARY,
    }
    if notes:
        out["notes"] = notes
    print(json.dumps(out, indent=2))
    sys.exit(0)


def load(path):
    if not os.path.isfile(path):
        fail(f"File not found: {path}")
    with open(path) as f:
        try:
            return json.load(f)
        except json.JSONDecodeError as e:
            fail(f"Invalid JSON: {e}")


def check_forbidden(profile):
    text = json.dumps(profile).lower()
    return [t for t in FORBIDDEN_TERMS if t in text]


def major_quality_fail(profile):
    failures = []
    if profile.get("stable_frame_count", 0) < 5:
        failures.append(
            f"stable_frame_count {profile.get('stable_frame_count')} < 5"
        )
    if profile.get("motion_blur_score", 1.0) > 0.70:
        failures.append(
            f"motion_blur_score {profile.get('motion_blur_score')} > 0.70"
        )
    if profile.get("scale_anchor_confidence", 0.0) < 0.50:
        failures.append(
            f"scale_anchor_confidence {profile.get('scale_anchor_confidence')} < 0.50"
        )
    if profile.get("frame_consistency_score", 0.0) < 0.50:
        failures.append(
            f"frame_consistency_score {profile.get('frame_consistency_score')} < 0.50"
        )
    if profile.get("camera_angle_quality") == "poor":
        failures.append("camera_angle_quality is poor")
    return failures


def validate(path):
    profile = load(path)

    # Forbidden terms
    found = check_forbidden(profile)
    if found:
        fail("forbidden_terms_detected", found)

    # Required fields
    missing = [f for f in REQUIRED_FIELDS if f not in profile]
    if missing:
        fail("missing_required_fields", missing)

    errors = []

    # Hard constraints
    if profile.get("report_type") != "livefit_scan_profile":
        errors.append("report_type must be livefit_scan_profile")
    if str(profile.get("schema_version")) != "2":
        errors.append("schema_version must be 2")
    if profile.get("manual_photo_capture") is not False:
        errors.append("manual_photo_capture must be false")
    if profile.get("hardware_required") is not False:
        errors.append("hardware_required must be false")

    # Boolean fields
    for f in ("stream_ready", "foot_detected", "floor_plane_anchor",
              "occlusion_detected", "optional_depth_sensor"):
        if not isinstance(profile.get(f), bool):
            errors.append(f"{f} must be boolean")

    # Integer fields
    if not isinstance(profile.get("stable_frame_count"), int):
        errors.append("stable_frame_count must be integer")
    elif profile["stable_frame_count"] < 0:
        errors.append("stable_frame_count must be >= 0")

    # Enum fields
    if profile.get("lighting_quality") not in VALID_LIGHTING:
        errors.append(f"lighting_quality must be one of {VALID_LIGHTING}")
    if profile.get("camera_angle_quality") not in VALID_ANGLE:
        errors.append(f"camera_angle_quality must be one of {VALID_ANGLE}")

    # Numeric range fields
    for score_field in ("motion_blur_score", "scale_anchor_confidence",
                        "frame_consistency_score", "estimated_arch_index"):
        val = profile.get(score_field)
        if not isinstance(val, (int, float)) or not (0.0 <= val <= 1.0):
            errors.append(f"{score_field} must be a number between 0.0 and 1.0")

    for mm_field in ("estimated_foot_length_mm", "estimated_foot_width_mm"):
        val = profile.get(mm_field)
        if not isinstance(val, (int, float)):
            errors.append(f"{mm_field} must be a number")

    if errors:
        fail("field_validation_errors", errors)

    # Major quality gate
    mq_fails = major_quality_fail(profile)

    # Compute confidence and decision
    conf_result = compute_confidence(
        frame_consistency_score=profile["frame_consistency_score"],
        scale_anchor_confidence=profile["scale_anchor_confidence"],
        motion_blur_score=profile["motion_blur_score"],
        stable_frame_count=profile["stable_frame_count"],
        camera_angle_quality=profile["camera_angle_quality"],
    )
    computed_conf = conf_result["computed_confidence"]
    decision, reason = compute_decision(
        confidence=computed_conf,
        foot_detected=profile["foot_detected"],
        stream_ready=profile["stream_ready"],
    )

    # Major quality failures override to rejected
    if mq_fails and decision != "rejected":
        fail(
            "major_quality_gate_fail",
            mq_fails
        )

    notes = []
    if reason:
        notes.append(reason)
    if mq_fails:
        notes.extend(mq_fails)

    ok(computed_conf, decision, notes if notes else None)


if __name__ == "__main__":
    if len(sys.argv) != 2:
        fail("Usage: python3 validate_z_livefit_stream_auto_v2.py <profile.json>")
    validate(sys.argv[1])

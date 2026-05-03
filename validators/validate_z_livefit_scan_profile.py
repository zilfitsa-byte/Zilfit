"""
ZILFIT LiveFit Scan Profile Validator
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

VALID_LIGHTING = {"good", "acceptable", "poor"}
VALID_DECISIONS = {"pass", "review_required", "rejected"}


def fail(reason, errors=None):
    out = {"validation": "FAIL", "reason": reason, "boundary": BOUNDARY}
    if errors:
        out["errors"] = errors
    print(json.dumps(out, indent=2))
    sys.exit(1)


def ok(notes=None):
    out = {"validation": "PASS", "boundary": BOUNDARY}
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

    if profile.get("manual_photo_capture") is not False:
        errors.append("manual_photo_capture must be false — live stream only")

    if profile.get("hardware_required") is not False:
        errors.append("hardware_required must be false")

    # Field types
    if not isinstance(profile.get("stream_ready"), bool):
        errors.append("stream_ready must be boolean")

    if not isinstance(profile.get("foot_detected"), bool):
        errors.append("foot_detected must be boolean")

    if not isinstance(profile.get("floor_plane_anchor"), bool):
        errors.append("floor_plane_anchor must be boolean")

    if not isinstance(profile.get("stable_frame_count"), int):
        errors.append("stable_frame_count must be integer")
    elif profile["stable_frame_count"] < 0:
        errors.append("stable_frame_count must be >= 0")

    if profile.get("lighting_quality") not in VALID_LIGHTING:
        errors.append(f"lighting_quality must be one of {VALID_LIGHTING}")

    if not isinstance(profile.get("occlusion_detected"), bool):
        errors.append("occlusion_detected must be boolean")

    if not isinstance(profile.get("optional_depth_sensor"), bool):
        errors.append("optional_depth_sensor must be boolean")

    for mm_field in ("estimated_foot_length_mm", "estimated_foot_width_mm"):
        val = profile.get(mm_field)
        if not isinstance(val, (int, float)):
            errors.append(f"{mm_field} must be a number")

    arch = profile.get("estimated_arch_index")
    if not isinstance(arch, (int, float)) or not (0.0 <= arch <= 1.0):
        errors.append("estimated_arch_index must be a number between 0.0 and 1.0")

    conf = profile.get("scan_confidence")
    if not isinstance(conf, (int, float)) or not (0.0 <= conf <= 1.0):
        errors.append("scan_confidence must be a number between 0.0 and 1.0")

    if profile.get("decision_status") not in VALID_DECISIONS:
        errors.append(f"decision_status must be one of {VALID_DECISIONS}")

    if errors:
        fail("field_validation_errors", errors)

    # Decision consistency
    foot_detected = profile["foot_detected"]
    confidence = profile["scan_confidence"]
    declared = profile["decision_status"]

    if not foot_detected:
        if declared != "rejected":
            fail(
                "decision_inconsistency",
                ["foot_detected is false — decision_status must be rejected"]
            )
    else:
        if confidence >= 0.85:
            expected = "pass"
        elif confidence >= 0.75:
            expected = "review_required"
        else:
            expected = "rejected"

        if declared != expected:
            fail(
                "decision_inconsistency",
                [f"scan_confidence {confidence} requires decision_status={expected}, got {declared}"]
            )

    ok()


if __name__ == "__main__":
    if len(sys.argv) != 2:
        fail("Usage: python3 validate_z_livefit_scan_profile.py <profile.json>")
    validate(sys.argv[1])

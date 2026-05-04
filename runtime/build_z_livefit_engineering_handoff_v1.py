"""
ZILFIT LiveFit — Engineering Handoff Builder v1
Combines scan confidence, sample readiness, and fit recommendation
into one engineering handoff JSON for early physical sampling.
Engineering simulation only.
No medical, diagnostic, therapeutic, clinical, treatment, pain, disease, or cure claims.
"""

import json
import sys
import os

_HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, _HERE)

from compute_z_livefit_stream_confidence_v2 import compute_confidence, compute_decision
from compute_z_livefit_sample_readiness_v1 import compute_sample_readiness
from compute_z_livefit_fit_recommendation_v1 import recommend

BOUNDARY = (
    "Engineering simulation only. "
    "No medical, diagnostic, therapeutic, clinical, treatment, "
    "pain, disease, or cure claims."
)

HANDOFF_VERSION = "1"

REQUIRED_FIELDS = [
    "report_type", "schema_version", "manual_photo_capture", "hardware_required",
    "stream_ready", "foot_detected", "floor_plane_anchor", "stable_frame_count",
    "lighting_quality", "occlusion_detected", "optional_depth_sensor",
    "camera_angle_quality", "motion_blur_score", "scale_anchor_confidence",
    "frame_consistency_score", "estimated_foot_length_mm",
    "estimated_foot_width_mm", "estimated_arch_index",
]

FORBIDDEN_TERMS = [
    "treat", "treatment", "cure", "diagnose", "diagnosis", "diagnostic",
    "medical", "clinical", "therapeutic", "pain reduction", "correct gait",
    "fix gait", "hormone", "disease", "patient outcome", "healing", "patient",
    "pain",
]


def emit(result, code):
    print(json.dumps(result, indent=2))
    sys.exit(code)


def load(path):
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


def check_required(profile):
    return [f for f in REQUIRED_FIELDS if f not in profile]


def run(path):
    profile = load(path)

    found = check_forbidden(profile)
    if found:
        emit({"status": "rejected", "reason": "forbidden_terms_detected",
              "forbidden_terms_found": found, "boundary": BOUNDARY}, 1)

    missing = check_required(profile)
    if missing:
        emit({"status": "rejected", "reason": "hard_constraint_violation",
              "errors": [f"Missing required fields: {missing}"],
              "boundary": BOUNDARY}, 1)

    if profile.get("manual_photo_capture") is not False:
        emit({"status": "rejected", "reason": "hard_constraint_violation",
              "errors": ["manual_photo_capture must be false"],
              "boundary": BOUNDARY}, 1)

    if profile.get("hardware_required") is not False:
        emit({"status": "rejected", "reason": "hard_constraint_violation",
              "errors": ["hardware_required must be false"],
              "boundary": BOUNDARY}, 1)

    # Step 1: confidence
    conf_result = compute_confidence(
        frame_consistency_score=profile["frame_consistency_score"],
        scale_anchor_confidence=profile["scale_anchor_confidence"],
        motion_blur_score=profile["motion_blur_score"],
        stable_frame_count=profile["stable_frame_count"],
        camera_angle_quality=profile["camera_angle_quality"],
    )
    computed_confidence = conf_result["computed_confidence"]
    decision, decision_reason = compute_decision(
        confidence=computed_confidence,
        foot_detected=profile["foot_detected"],
        stream_ready=profile["stream_ready"],
    )

    measurements = {
        "estimated_foot_length_mm": profile["estimated_foot_length_mm"],
        "estimated_foot_width_mm": profile["estimated_foot_width_mm"],
        "estimated_arch_index": profile["estimated_arch_index"],
    }

    # Step 2: sample readiness
    scan_output = {
        "computed_confidence": computed_confidence,
        "computed_decision_status": decision,
        "measurements": measurements,
    }
    readiness_status, readiness_notes = compute_sample_readiness(scan_output)

    # Step 3: fit recommendation
    import subprocess, tempfile, json as _json
    fit_payload = {
        "computed_confidence": computed_confidence,
        "computed_decision_status": decision,
        "measurements": measurements,
        "sample_readiness_status": readiness_status,
    }
    with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as tf:
        _json.dump(fit_payload, tf)
        tf_path = tf.name
    try:
        fit_proc = subprocess.run(
            [sys.executable,
             os.path.join(_HERE, "compute_z_livefit_fit_recommendation_v1.py"),
             tf_path],
            capture_output=True, text=True
        )
        fit = _json.loads(fit_proc.stdout)
    except Exception as e:
        fit = {"status": "error", "error": str(e)}
    finally:
        os.unlink(tf_path)

    emit({
        "handoff_version": HANDOFF_VERSION,
        "report_type": profile.get("report_type"),
        "schema_version": profile.get("schema_version"),
        "computed_confidence": computed_confidence,
        "computed_decision_status": decision,
        "decision_reason": decision_reason,
        "sample_readiness_status": readiness_status,
        "readiness_reason": readiness_notes,
        "fit_recommendation": fit,
        "measurements": measurements,
        "signal_contributions": conf_result["signal_contributions"],
        "boundary": BOUNDARY,
    }, 0)


if __name__ == "__main__":
    if len(sys.argv) != 2:
        emit({"status": "error",
              "error": "Usage: python3 build_z_livefit_engineering_handoff_v1.py <profile.json>",
              "boundary": BOUNDARY}, 1)
    run(sys.argv[1])

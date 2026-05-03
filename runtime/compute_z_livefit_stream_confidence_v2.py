"""
ZILFIT LiveFit Scan — Stream Confidence Computation Module v2
Deterministic formula deriving scan_confidence from v2 stream signal fields.
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

ANGLE_MAP = {
    "optimal": 1.0,
    "acceptable": 0.6,
    "poor": 0.0,
}

WEIGHTS = {
    "frame_consistency_score": 0.30,
    "scale_anchor_confidence": 0.25,
    "motion_blur_inverted": 0.20,
    "stable_frame_normalized": 0.15,
    "camera_angle_score": 0.10,
}

STABLE_FRAME_CAP = 20


def compute_confidence(
    frame_consistency_score,
    scale_anchor_confidence,
    motion_blur_score,
    stable_frame_count,
    camera_angle_quality,
):
    """
    Compute scan_confidence from v2 stream signal fields.

    Returns:
        dict with keys:
            computed_confidence (float, 0.0-1.0)
            angle_score (float)
            stable_frame_normalized (float)
            motion_blur_inverted (float)
            signal_contributions (dict)
    """
    angle_score = ANGLE_MAP.get(camera_angle_quality, 0.0)
    stable_norm = min(stable_frame_count / STABLE_FRAME_CAP, 1.0)
    blur_inv = 1.0 - motion_blur_score

    contributions = {
        "frame_consistency_score": round(
            WEIGHTS["frame_consistency_score"] * frame_consistency_score, 6
        ),
        "scale_anchor_confidence": round(
            WEIGHTS["scale_anchor_confidence"] * scale_anchor_confidence, 6
        ),
        "motion_blur_inverted": round(
            WEIGHTS["motion_blur_inverted"] * blur_inv, 6
        ),
        "stable_frame_normalized": round(
            WEIGHTS["stable_frame_normalized"] * stable_norm, 6
        ),
        "camera_angle_score": round(
            WEIGHTS["camera_angle_score"] * angle_score, 6
        ),
    }

    confidence = round(sum(contributions.values()), 6)

    return {
        "computed_confidence": confidence,
        "angle_score": angle_score,
        "stable_frame_normalized": round(stable_norm, 6),
        "motion_blur_inverted": round(blur_inv, 6),
        "signal_contributions": contributions,
    }


def compute_decision(confidence, foot_detected, stream_ready):
    """
    Derive decision_status from computed confidence and hard conditions.
    """
    if not stream_ready:
        return "rejected", "stream_ready is false"
    if not foot_detected:
        return "rejected", "foot_detected is false"
    if confidence >= 0.85:
        return "pass", None
    elif confidence >= 0.75:
        return "review_required", f"computed_confidence {confidence} in review band"
    else:
        return "rejected", f"computed_confidence {confidence} below 0.75"


def run_from_profile(path):
    if not os.path.isfile(path):
        print(json.dumps({
            "status": "error",
            "error": f"File not found: {path}",
            "boundary": BOUNDARY,
        }, indent=2))
        sys.exit(1)

    with open(path) as f:
        try:
            profile = json.load(f)
        except json.JSONDecodeError as e:
            print(json.dumps({
                "status": "error",
                "error": f"Invalid JSON: {e}",
                "boundary": BOUNDARY,
            }, indent=2))
            sys.exit(1)

    required = [
        "frame_consistency_score", "scale_anchor_confidence",
        "motion_blur_score", "stable_frame_count", "camera_angle_quality",
        "foot_detected", "stream_ready",
    ]
    missing = [f for f in required if f not in profile]
    if missing:
        print(json.dumps({
            "status": "error",
            "error": f"Missing required fields: {missing}",
            "boundary": BOUNDARY,
        }, indent=2))
        sys.exit(1)

    result = compute_confidence(
        frame_consistency_score=profile["frame_consistency_score"],
        scale_anchor_confidence=profile["scale_anchor_confidence"],
        motion_blur_score=profile["motion_blur_score"],
        stable_frame_count=profile["stable_frame_count"],
        camera_angle_quality=profile["camera_angle_quality"],
    )

    decision, reason = compute_decision(
        confidence=result["computed_confidence"],
        foot_detected=profile["foot_detected"],
        stream_ready=profile["stream_ready"],
    )

    declared = profile.get("scan_confidence")
    declared_decision = profile.get("decision_status")

    output = {
        "report_type": profile.get("report_type", "livefit_scan_profile"),
        "schema_version": profile.get("schema_version", "2"),
        "computed_confidence": result["computed_confidence"],
        "declared_confidence": declared,
        "confidence_delta": (
            round(result["computed_confidence"] - declared, 6)
            if declared is not None else None
        ),
        "computed_decision_status": decision,
        "declared_decision_status": declared_decision,
        "decision_reason": reason,
        "angle_score": result["angle_score"],
        "stable_frame_normalized": result["stable_frame_normalized"],
        "motion_blur_inverted": result["motion_blur_inverted"],
        "signal_contributions": result["signal_contributions"],
        "boundary": BOUNDARY,
    }

    print(json.dumps(output, indent=2))
    sys.exit(0)


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print(json.dumps({
            "status": "error",
            "error": "Usage: python3 compute_z_livefit_stream_confidence_v2.py <profile.json>",
            "boundary": BOUNDARY,
        }, indent=2))
        sys.exit(1)
    run_from_profile(sys.argv[1])

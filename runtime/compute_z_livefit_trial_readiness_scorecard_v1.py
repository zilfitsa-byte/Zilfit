"""
ZILFIT LiveFit — Trial Readiness Scorecard v1
Consumes engineering handoff JSON and outputs physical trial readiness decision.
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

SCORECARD_VERSION = "1"

REQUIRED_FIELDS = [
    "computed_confidence",
    "computed_decision_status",
    "sample_readiness_status",
    "fit_recommendation",
    "measurements",
    "boundary",
]

FORBIDDEN_TERMS = [
    "treat", "treatment", "cure", "diagnose", "diagnosis", "diagnostic",
    "medical", "clinical", "therapeutic", "pain reduction", "correct gait",
    "fix gait", "hormone", "disease", "patient outcome", "healing", "patient",
    "pain",
]

VALID_TRIAL_STATUSES = {
    "ready_for_physical_trial",
    "needs_fit_review",
    "needs_more_scan_quality",
    "blocked",
}


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


# Keys whose values are system-generated safety text — never scan these
SYSTEM_KEYS = {
    "boundary", "engineering_notes", "readiness_reason", "decision_reason",
    "confidence_context", "signal_contributions", "stream_warnings",
    "stream_quality_flags", "notes", "fit_recommendation",
}

def _strip_system_keys(obj):
    """Recursively remove system-generated keys before forbidden-term scan."""
    if isinstance(obj, dict):
        return {
            k: _strip_system_keys(v)
            for k, v in obj.items()
            if k not in SYSTEM_KEYS
        }
    if isinstance(obj, list):
        return [_strip_system_keys(i) for i in obj]
    return obj


def check_forbidden(payload):
    sanitised = _strip_system_keys(payload)
    text = json.dumps(sanitised).lower()
    return [t for t in FORBIDDEN_TERMS if t in text]


def compute_trial_readiness(handoff):
    confidence = handoff.get("computed_confidence", 0.0)
    decision = handoff.get("computed_decision_status", "")
    readiness = handoff.get("sample_readiness_status", "")
    fit_rec = handoff.get("fit_recommendation", {})
    fit_status = fit_rec.get("fit_status", "") if isinstance(fit_rec, dict) else ""

    # blocked: missing or invalid critical fields
    if not confidence or not decision or not readiness:
        return "blocked", "missing critical handoff fields"

    # needs_more_scan_quality: scan confidence too low or rescan required
    if confidence < 0.75:
        return "needs_more_scan_quality", f"computed_confidence {confidence} below 0.75"
    if readiness == "needs_rescan":
        return "needs_more_scan_quality", "sample_readiness_status is needs_rescan"

    # needs_fit_review: manual review required or borderline confidence
    if readiness == "manual_review":
        return "needs_fit_review", "sample_readiness_status is manual_review"
    if decision == "review_required":
        return "needs_fit_review", "computed_decision_status is review_required"
    if fit_status == "review_required":
        return "needs_fit_review", "fit_status is review_required"

    # ready_for_physical_trial: all gates pass
    if (readiness == "sample_ready"
            and decision == "pass"
            and fit_status == "sample_candidate"):
        return "ready_for_physical_trial", "all engineering gates passed"

    # fallback
    return "needs_fit_review", (
        f"unresolved state: readiness={readiness} "
        f"decision={decision} fit_status={fit_status}"
    )


def run(path):
    handoff = load(path)

    found = check_forbidden(handoff)
    if found:
        emit({
            "scorecard_version": SCORECARD_VERSION,
            "trial_readiness_status": "blocked",
            "readiness_reason": "forbidden_terms_detected",
            "forbidden_terms_found": found,
            "boundary": BOUNDARY,
        }, 1)

    missing = [f for f in REQUIRED_FIELDS if f not in handoff]
    if missing:
        emit({
            "scorecard_version": SCORECARD_VERSION,
            "trial_readiness_status": "blocked",
            "readiness_reason": f"missing required fields: {missing}",
            "boundary": BOUNDARY,
        }, 1)

    trial_status, reason = compute_trial_readiness(handoff)

    fit_rec = handoff.get("fit_recommendation", {})
    fit_status = fit_rec.get("fit_status", "") if isinstance(fit_rec, dict) else ""

    emit({
        "scorecard_version": SCORECARD_VERSION,
        "trial_readiness_status": trial_status,
        "readiness_reason": reason,
        "computed_confidence": handoff.get("computed_confidence"),
        "computed_decision_status": handoff.get("computed_decision_status"),
        "sample_readiness_status": handoff.get("sample_readiness_status"),
        "fit_status": fit_status,
        "measurements": handoff.get("measurements"),
        "boundary": BOUNDARY,
    }, 0)


if __name__ == "__main__":
    if len(sys.argv) != 2:
        emit({
            "status": "error",
            "error": "Usage: python3 compute_z_livefit_trial_readiness_scorecard_v1.py <handoff.json>",
            "boundary": BOUNDARY,
        }, 1)
    run(sys.argv[1])

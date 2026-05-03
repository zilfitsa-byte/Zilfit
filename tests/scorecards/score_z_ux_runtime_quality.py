#!/usr/bin/env python3
import json
import subprocess
import sys
from pathlib import Path
from datetime import datetime, timezone

FORBIDDEN_CLAIM_TERMS = [
    "treats disease",
    "treatment for",
    "cures pain",
    "diagnoses medical conditions",
    "diagnostic result",
    "prevents disease",
    "prevention of disease",
    "regulates hormones",
    "medical grade",
    "clinical result",
    "therapeutic effect",
    "pain reduction",
    "heals injury",
    "healing",
    "patient outcome",
]

SAFE_NEGATION_TERMS = [
    "no medical",
    "non-medical",
    "not medical",
    "no clinical",
    "non-clinical",
    "not clinical",
    "no diagnostic",
    "non-diagnostic",
    "not diagnostic",
    "no therapeutic",
    "non-therapeutic",
    "not therapeutic",
    "unsafe wording",
    "forbidden",
    "must not",
    "does not validate",
    "expected validator failure",
]

EXPECTED_SIGNAL_VALUES = [
    "v1",
    "z_ux_live_output_v1",
    "Z-Guide",
    "trigger_screen_id",
    "next_expected_action",
]

def fail(msg: str) -> None:
    print(f"SCORECARD_FAIL: {msg}")
    raise SystemExit(1)

def load_json(path: Path) -> dict:
    if not path.exists():
        fail(f"missing input: {path}")
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except Exception as e:
        fail(f"invalid json: {e}")
    if not isinstance(data, dict):
        fail("root must be a JSON object")
    return data

def flatten_strings(value):
    if isinstance(value, str):
        yield value
    elif isinstance(value, dict):
        for k, v in value.items():
            yield str(k)
            yield from flatten_strings(v)
    elif isinstance(value, list):
        for v in value:
            yield from flatten_strings(v)
    else:
        if value is not None:
            yield str(value)

def run_validator(input_path: Path) -> tuple[bool, str]:
    proc = subprocess.run(
        ["python3", "validators/validate_z_ux_live_output.py", str(input_path)],
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
    )
    return proc.returncode == 0, proc.stdout.strip()

def unsafe_claim_hits(all_text: str) -> list[str]:
    hits = []
    for term in FORBIDDEN_CLAIM_TERMS:
        if term in all_text:
            safe_context = any(safe in all_text for safe in SAFE_NEGATION_TERMS)
            if not safe_context:
                hits.append(term)
    return hits

def main() -> None:
    if len(sys.argv) < 2:
        fail("usage: score_z_ux_runtime_quality.py <live_output.json> [report_json]")

    input_path = Path(sys.argv[1])
    report_path = Path(sys.argv[2]) if len(sys.argv) > 2 else None

    data = load_json(input_path)
    validator_ok, validator_output = run_validator(input_path)

    all_values = list(flatten_strings(data))
    all_text = "\n".join(all_values).lower()

    checks = []
    score = 0

    root_ok = isinstance(data, dict) and bool(data)
    checks.append({
        "check": "json_root_object",
        "status": "pass" if root_ok else "fail",
        "points": 10 if root_ok else 0,
        "detail": "root JSON object present",
    })
    score += 10 if root_ok else 0

    checks.append({
        "check": "official_live_output_validator",
        "status": "pass" if validator_ok else "fail",
        "points": 40 if validator_ok else 0,
        "detail": validator_output,
    })
    score += 40 if validator_ok else 0

    found_signals = []
    missing_signals = []
    for expected in EXPECTED_SIGNAL_VALUES:
        if any(str(expected) == str(v) for v in all_values):
            found_signals.append(expected)
        else:
            missing_signals.append(expected)

    signal_points = 20 if not missing_signals else max(0, 20 - (4 * len(missing_signals)))
    checks.append({
        "check": "runtime_contract_signals",
        "status": "pass" if not missing_signals else "review_required",
        "points": signal_points,
        "detail": {
            "found": found_signals,
            "missing": missing_signals,
        },
    })
    score += signal_points

    hits = unsafe_claim_hits(all_text)
    claims_ok = not hits
    checks.append({
        "check": "non_medical_claim_safety",
        "status": "pass" if claims_ok else "fail",
        "points": 20 if claims_ok else 0,
        "detail": hits,
    })
    score += 20 if claims_ok else 0

    reproducible_identity = {
        "schema_version": data.get("schema_version"),
        "task_id": data.get("task_id"),
        "source_packet_name": data.get("source_packet_name"),
        "source_agent": data.get("source_agent"),
    }
    identity_ok = sum(v is not None for v in reproducible_identity.values()) >= 3
    checks.append({
        "check": "reproducible_identity_fields",
        "status": "pass" if identity_ok else "review_required",
        "points": 10 if identity_ok else 0,
        "detail": reproducible_identity,
    })
    score += 10 if identity_ok else 0

    status = "pass" if validator_ok and claims_ok and score >= 90 else "review_required"

    report = {
        "schema_version": "v1",
        "report_type": "z_ux_runtime_quality_scorecard",
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "input": str(input_path),
        "score": score,
        "max_score": 100,
        "status": status,
        "checks": checks,
        "boundary": "Engineering/runtime quality scorecard only. No medical, diagnostic, therapeutic, or clinical claims.",
    }

    print(f"Z_UX_RUNTIME_QUALITY_SCORE={score}")
    print(f"Z_UX_RUNTIME_QUALITY_STATUS={status}")

    if report_path:
        report_path.parent.mkdir(parents=True, exist_ok=True)
        report_path.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        print(f"WROTE_SCORECARD_REPORT={report_path}")

    if status != "pass":
        raise SystemExit(1)

if __name__ == "__main__":
    main()

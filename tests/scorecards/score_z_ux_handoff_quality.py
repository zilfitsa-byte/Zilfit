#!/usr/bin/env python3
import json
import re
import sys
from datetime import datetime, timezone
from pathlib import Path

FORBIDDEN_RE = re.compile(
    r"\b("
    r"treat|treats|treatment|cure|cures|diagnose|diagnoses|diagnostic|medical|"
    r"therapeutic|therapy|heals|healing|patient|clinical|pain reduction|"
    r"prevents disease|regulates hormones|psychological treatment|"
    r"يعالج|علاج|تشخيص|شفاء|ألم|هرمون|عضو|طبي|سريري"
    r")\b",
    re.IGNORECASE,
)

SAFE_BOUNDARY_PHRASES = [
    "no medical",
    "no diagnostic",
    "no therapeutic",
    "no clinical",
    "no approved",
    "engineering",
    "quality only",
    "simulation only",
]

REQUIRED_HINTS = ["action", "cta", "next", "routing", "screen"]


def fail(msg):
    print(f"HANDOFF_SCORECARD_FAIL: {msg}")
    raise SystemExit(1)


def load_json(path):
    p = Path(path)
    if not p.exists():
        fail(f"missing input: {path}")
    try:
        data = json.loads(p.read_text(encoding="utf-8"))
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
    elif value is not None:
        yield str(value)


def add_check(checks, name, ok, points, detail):
    checks.append({
        "check": name,
        "status": "pass" if ok else "fail",
        "points": points if ok else 0,
        "detail": detail,
    })
    return points if ok else 0


def main():
    if len(sys.argv) != 3:
        print("Usage: score_z_ux_handoff_quality.py <handoff_json> <report_json>")
        return 2

    input_path = Path(sys.argv[1])
    report_path = Path(sys.argv[2])
    data = load_json(input_path)

    checks = []
    score = 0

    text_values = list(flatten_strings(data))
    joined = json.dumps(data, ensure_ascii=False).lower()

    runtime_packet = data.get("runtime_packet", {}) if isinstance(data.get("runtime_packet"), dict) else {}
    live_output = data.get("live_output", {}) if isinstance(data.get("live_output"), dict) else {}

    schema_version = (
        data.get("schema_version")
        or runtime_packet.get("schema_version")
        or live_output.get("schema_version")
        or data.get("runtime_packet", {}).get("schema_version") if isinstance(data.get("runtime_packet"), dict) else None
    )

    task_id = (
        data.get("task_id")
        or runtime_packet.get("task_id")
        or live_output.get("task_id")
        or data.get("live_output", {}).get("task_id") if isinstance(data.get("live_output"), dict) else None
    )

    source_packet_name = (
        data.get("source_packet_name")
        or runtime_packet.get("packet_name")
        or runtime_packet.get("source_packet_name")
        or live_output.get("source_packet_name")
    )

    source_agent = (
        data.get("source_agent")
        or runtime_packet.get("source_agent")
        or live_output.get("source_agent")
    )

    root_ok = isinstance(data, dict) and bool(data)
    score += add_check(checks, "json_root_object", root_ok, 10, "root JSON object present")

    identity_ok = bool(schema_version) and bool(task_id) and bool(source_packet_name or source_agent)
    score += add_check(
        checks,
        "handoff_identity_contract",
        identity_ok,
        30,
        {
            "schema_version": schema_version,
            "task_id": task_id,
            "source_packet_name": source_packet_name,
            "source_agent": source_agent,
        },
    )

    utility_hits = [hint for hint in REQUIRED_HINTS if hint in joined]
    utility_ok = len(utility_hits) >= 3
    score += add_check(
        checks,
        "downstream_handoff_utility",
        utility_ok,
        25,
        {"hits": utility_hits},
    )

    raw_forbidden_hits = sorted({m.group(0).lower() for s in text_values for m in FORBIDDEN_RE.finditer(s)})
    boundary_is_safe = any(p in joined for p in SAFE_BOUNDARY_PHRASES)
    forbidden_hits = [] if boundary_is_safe else raw_forbidden_hits

    safety_ok = not forbidden_hits
    score += add_check(
        checks,
        "non_claim_language_safety",
        safety_ok,
        25,
        {
            "forbidden_hits": forbidden_hits,
            "raw_hits_ignored_when_safe_boundary_present": raw_forbidden_hits if boundary_is_safe else [],
            "safe_boundary_detected": boundary_is_safe,
        },
    )

    reproducible_ok = bool(task_id) and bool(source_agent or source_packet_name)
    score += add_check(
        checks,
        "reproducible_handoff_fields",
        reproducible_ok,
        10,
        {
            "task_id": task_id,
            "source_agent": source_agent,
            "source_packet_name": source_packet_name,
        },
    )

    status = "pass" if score >= 90 else "review_required" if score >= 70 else "fail"

    report = {
        "schema_version": "v1",
        "module": "z_ux_handoff_quality_scorecard",
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "input_file": str(input_path),
        "score": score,
        "max_score": 100,
        "status": status,
        "checks": checks,
        "boundary": "Engineering/runtime handoff quality scorecard only. No medical, diagnostic, therapeutic, clinical, or psychological treatment claim.",
    }

    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    print(f"Z_UX_HANDOFF_QUALITY_SCORE={score}")
    print(f"Z_UX_HANDOFF_QUALITY_STATUS={status}")
    print(f"WROTE_HANDOFF_SCORECARD_REPORT={report_path}")

    return 0 if status == "pass" else 1


if __name__ == "__main__":
    raise SystemExit(main())

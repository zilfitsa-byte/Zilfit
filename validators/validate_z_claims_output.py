#!/usr/bin/env python3
import json
import sys
from pathlib import Path

REQUIRED = [
    "agent_name",
    "task_id",
    "output_class",
    "confidence",
    "sources",
    "assumptions",
    "risks",
    "decision",
    "next_required_validation",
    "approved_for_use",
    "skills_used",
    "claim_status",
    "original_claim",
    "reason"
]

CLAIM_STATUSES = {
    "ALLOWED",
    "NEEDS_SOFTENING",
    "FORBIDDEN",
    "NEEDS_EVIDENCE"
}

DECISIONS = {
    "PASS",
    "FAIL",
    "CONDITIONAL_PASS",
    "BLOCK",
    "NEEDS_REVIEW"
}

def fail(msg: str) -> None:
    print(f"VALIDATION_FAIL: {msg}")
    sys.exit(1)

if len(sys.argv) != 2:
    fail("Usage: validate_z_claims_output.py file.json")

path = Path(sys.argv[1])
if not path.exists():
    fail(f"File not found: {path}")

try:
    data = json.loads(path.read_text(encoding="utf-8"))
except Exception as e:
    fail(f"Invalid JSON: {e}")

for key in REQUIRED:
    if key not in data:
        fail(f"Missing required field: {key}")

if data["agent_name"] != "Z-Claims":
    fail("agent_name must be Z-Claims")

if data["decision"] not in DECISIONS:
    fail("Invalid decision")

if data["claim_status"] not in CLAIM_STATUSES:
    fail("Invalid claim_status")

confidence = data["confidence"]
if not isinstance(confidence, (int, float)) or not (0 <= confidence <= 1):
    fail("confidence must be number between 0 and 1")

if not isinstance(data["skills_used"], list) or len(data["skills_used"]) == 0:
    fail("No skills applied")

for item in data["skills_used"]:
    if not isinstance(item, str) or not item.strip():
        fail("skills_used must contain non-empty strings only")

if data["claim_status"] in ["NEEDS_SOFTENING", "FORBIDDEN"] and not data.get("safer_rewrite"):
    fail("safer_rewrite required for NEEDS_SOFTENING or FORBIDDEN")

forbidden = [
    "treats disease",
    "cures pain",
    "prevents injury",
    "regulates hormones",
    "guarantees cortisol reduction",
    "diagnoses medical conditions"
]

text = json.dumps(data, ensure_ascii=False).lower()
for phrase in forbidden:
    if phrase in text and "safer_rewrite" not in data:
        fail(f"Forbidden claim detected without safe rewrite: {phrase}")

print("VALIDATION_PASS")

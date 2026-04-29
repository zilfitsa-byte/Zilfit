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
    "guidance_scope",
    "primary_user_goal",
    "live_behavior_mode",
    "fallback_rule"
]

VALID_OUTPUT_CLASSES = {"GUIDANCE", "FLOW_HELP", "SUPPORT_COPY", "CHECKOUT_HELP", "FOLLOWUP_PROMPT"}
VALID_DECISIONS = {"APPROVED", "NEEDS_REVIEW", "REJECTED"}

def fail(msg):
    print(f"VALIDATION_FAIL: {msg}")
    sys.exit(1)

if len(sys.argv) != 2:
    fail("Usage: validate_z_guide_output.py <json_file>")

p = Path(sys.argv[1])
if not p.exists():
    fail("File not found")

try:
    data = json.loads(p.read_text(encoding="utf-8"))
except Exception as e:
    fail(f"Invalid JSON: {e}")

for key in REQUIRED:
    if key not in data:
        fail(f"Missing required field: {key}")

if data["agent_name"] != "Z-Guide":
    fail("agent_name must be Z-Guide")

if data["output_class"] not in VALID_OUTPUT_CLASSES:
    fail("Invalid output_class")

if data["decision"] not in VALID_DECISIONS:
    fail("Invalid decision")

if not isinstance(data["confidence"], (int, float)):
    fail("confidence must be numeric")

if not (0 <= float(data["confidence"]) <= 1):
    fail("confidence must be between 0 and 1")

for key in ["sources", "assumptions", "risks", "skills_used", "guidance_scope"]:
    if not isinstance(data[key], list) or len(data[key]) == 0:
        fail(f"{key} must be a non-empty list")

if not isinstance(data["approved_for_use"], bool):
    fail("approved_for_use must be boolean")

for key in ["primary_user_goal", "live_behavior_mode", "fallback_rule", "next_required_validation"]:
    if not isinstance(data[key], str) or not data[key].strip():
        fail(f"{key} must be a non-empty string")

print("VALIDATION_PASS")

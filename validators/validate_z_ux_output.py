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
    "primary_user_goal",
    "flow_type",
    "screen_sequence",
    "friction_points",
    "ux_recommendation",
    "conversion_risk",
    "next_design_step"
]

def fail(msg):
    print(f"VALIDATION_FAIL: {msg}")
    sys.exit(1)

if len(sys.argv) != 2:
    fail("Usage: validate_z_ux_output.py file.json")

p = Path(sys.argv[1])
if not p.exists():
    fail(f"File not found: {p}")

data = json.loads(p.read_text(encoding="utf-8"))

for k in REQUIRED:
    if k not in data:
        fail(f"Missing required field: {k}")

if data["agent_name"] != "Z-UX":
    fail("agent_name must be Z-UX")

if not isinstance(data["skills_used"], list) or len(data["skills_used"]) == 0:
    fail("No skills applied")

if not isinstance(data["screen_sequence"], list) or len(data["screen_sequence"]) == 0:
    fail("screen_sequence must be a non-empty list")

if not isinstance(data["friction_points"], list):
    fail("friction_points must be a list")

print("VALIDATION_PASS")

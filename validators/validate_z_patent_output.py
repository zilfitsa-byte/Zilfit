#!/usr/bin/env python3
import json
import sys
from pathlib import Path

REQUIRED = [
    "agent_name","task_id","output_class","confidence","sources",
    "assumptions","risks","decision","next_required_validation",
    "approved_for_use","skills_used","novelty_assessment",
    "prior_art_risk","invention_boundary","filing_readiness"
]

def fail(msg):
    print(f"VALIDATION_FAIL: {msg}")
    sys.exit(1)

if len(sys.argv) != 2:
    fail("Usage: validate_z_patent_output.py file.json")

p = Path(sys.argv[1])
if not p.exists():
    fail(f"File not found: {p}")

data = json.loads(p.read_text(encoding="utf-8"))

for k in REQUIRED:
    if k not in data:
        fail(f"Missing required field: {k}")

if data["agent_name"] != "Z-Patent":
    fail("agent_name must be Z-Patent")

if not isinstance(data["skills_used"], list) or len(data["skills_used"]) == 0:
    fail("No skills applied")

print("VALIDATION_PASS")

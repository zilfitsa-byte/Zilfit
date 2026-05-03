#!/usr/bin/env bash
set -euo pipefail

TEST_NAME="$(basename "$0")"
trap 'rc=$?; echo "[FAIL] ${TEST_NAME}: line ${LINENO}"; exit $rc' ERR

REPO_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$REPO_ROOT"

TMP_DIR="$(mktemp -d)"
trap 'rm -rf "$TMP_DIR"' EXIT

INPUT="$TMP_DIR/preproduction_input.json"
OUTPUT="$TMP_DIR/preproduction_output.json"

cat > "$INPUT" <<'JSON'
{
  "schema_version": "v1",
  "sample_id": "sample_001",
  "edition": "BALANCE",
  "customer": {
    "height_cm": 178,
    "weight_kg": 82,
    "shoe_size": 43,
    "foot_length_mm": 272,
    "foot_width_mm": 101,
    "usage_mode": "daily",
    "fit_preference": "balanced"
  },
  "user_experience_research_hypothesis": {
    "target_feel": "stable midfoot transition",
    "claim_status": "engineering_research_only"
  }
}
JSON

python3 runtime/preproduction_sample_simulator.py "$INPUT" "$OUTPUT"

python3 - "$OUTPUT" <<'PY'
import json
import sys

data = json.load(open(sys.argv[1], encoding="utf-8"))

assert data["schema_version"] == "v1"
assert data["report_type"] == "preproduction_sample_simulation"
assert data["edition"] == "BALANCE"
assert data["customer_measurement_profile"]["fit_fingerprint"].startswith("ZFP-")
assert len(data["zone_outputs"]) == 7
assert data["simulation_metrics"]["manufacturing_readiness_score"] >= 70
assert data["manufacturing_decision"]["status"] in ("sample_ready", "needs_revision")
assert data["blocked_claims"] == []
assert "No approved medical" in data["boundary"]

required = {
    "zone_load_N",
    "P_norm",
    "density_pct",
    "t_wall_mm",
    "source",
    "confidence",
    "validation_status",
    "failure_flags",
    "baseline_comparison",
}

for zone in data["zone_outputs"]:
    missing = required - set(zone)
    assert not missing, missing
    assert 0.5 <= float(zone["t_wall_mm"]) <= 0.7

print("PREPRODUCTION_SAMPLE_SIMULATOR_TEST_PASS")
PY

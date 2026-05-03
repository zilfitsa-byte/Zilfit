#!/usr/bin/env bash
set -euo pipefail

TEST_NAME="$(basename "$0")"
trap 'rc=$?; echo "[FAIL] ${TEST_NAME}: line ${LINENO}"; exit $rc' ERR

REPO_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$REPO_ROOT"

TMP_DIR="$(mktemp -d)"
trap 'rm -rf "$TMP_DIR"' EXIT

INPUT="$TMP_DIR/bad_preproduction_input.json"
OUTPUT="$TMP_DIR/bad_preproduction_output.json"

cat > "$INPUT" <<'JSON'
{
  "schema_version": "v1",
  "sample_id": "bad_sample_001",
  "edition": "CALM",
  "customer": {
    "height_cm": 178,
    "weight_kg": 82,
    "shoe_size": 43,
    "foot_length_mm": 272,
    "foot_width_mm": 101,
    "usage_mode": "daily",
    "fit_preference": "balanced"
  },
  "unsafe_claim_example": "this product treats anxiety and corrects gait"
}
JSON

python3 runtime/preproduction_sample_simulator.py "$INPUT" "$OUTPUT"

python3 - "$OUTPUT" <<'PY'
import json
import sys

data = json.load(open(sys.argv[1], encoding="utf-8"))

assert data["manufacturing_decision"]["status"] == "blocked"
assert data["blocked_claims"]
assert data["manufacturing_decision"]["recommended_sample_count"] == 0
assert "No approved medical" in data["boundary"]

print("NEGATIVE_PREPRODUCTION_SAMPLE_CLAIMS_TEST_PASS")
PY

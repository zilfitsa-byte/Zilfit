#!/usr/bin/env bash
set -euo pipefail

TEST_NAME="$(basename "$0")"
trap 'rc=$?; echo "[FAIL] ${TEST_NAME}: line ${LINENO}"; exit $rc' ERR

REPO_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$REPO_ROOT"

TMP_DIR="$(mktemp -d)"
trap 'rm -rf "$TMP_DIR"' EXIT

LIVE_OUT="$TMP_DIR/z_ux_live_output_from_runtime_v1.json"
BAD_OUT="$TMP_DIR/bad_z_ux_live_output_from_runtime_v1.json"
REPORT_OUT="$TMP_DIR/bad_z_ux_runtime_quality_scorecard.json"

python3 tests/generate_z_ux_live_output_from_runtime.py "$LIVE_OUT" >/dev/null
python3 validators/validate_z_ux_live_output.py "$LIVE_OUT"

python3 - <<PY
import json
from pathlib import Path

src = Path("$LIVE_OUT")
dst = Path("$BAD_OUT")

data = json.loads(src.read_text(encoding="utf-8"))

# Inject an explicit unsafe medical/clinical claim into a temp-only copy.
data["regression_probe"] = {
    "unsafe_claim": "This output cures pain and provides a diagnostic result."
}

dst.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
PY

if python3 tests/scorecards/score_z_ux_runtime_quality.py "$BAD_OUT" "$REPORT_OUT"; then
  echo "EXPECTED scorecard failure for unsafe regression probe"
  exit 1
fi

python3 - <<PY
import json
from pathlib import Path

p = Path("$REPORT_OUT")
data = json.loads(p.read_text(encoding="utf-8"))

assert data["status"] == "review_required", data["status"]
assert data["score"] < 90, data["score"]

checks = {c["check"]: c for c in data["checks"]}
assert checks["non_medical_claim_safety"]["status"] == "fail", checks
assert checks["non_medical_claim_safety"]["detail"], checks["non_medical_claim_safety"]
PY

echo "NEGATIVE_Z_UX_RUNTIME_QUALITY_SCORECARD_TEST_PASS"

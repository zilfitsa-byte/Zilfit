#!/usr/bin/env bash
set -euo pipefail

TEST_NAME="$(basename "$0")"
trap 'rc=$?; echo "[FAIL] ${TEST_NAME}: line ${LINENO}"; exit $rc' ERR

REPO_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$REPO_ROOT"

TMP_DIR="$(mktemp -d)"
trap 'rm -rf "$TMP_DIR"' EXIT

LIVE_OUT="$TMP_DIR/z_ux_live_output_from_runtime_v1.json"
REPORT_OUT="$TMP_DIR/z_ux_runtime_quality_scorecard.json"

python3 tests/generate_z_ux_live_output_from_runtime.py "$LIVE_OUT" >/dev/null
python3 validators/validate_z_ux_live_output.py "$LIVE_OUT"
python3 tests/scorecards/score_z_ux_runtime_quality.py "$LIVE_OUT" "$REPORT_OUT"

python3 - <<PY
import json
from pathlib import Path

p = Path("$REPORT_OUT")
data = json.loads(p.read_text(encoding="utf-8"))

assert data["score"] >= 90, data["score"]
assert data["status"] == "pass", data["status"]
assert len(data["checks"]) == 5, data["checks"]
assert all(c["status"] in ("pass", "review_required") for c in data["checks"]), data["checks"]
assert "medical" in data["boundary"].lower()
PY

echo "Z_UX_RUNTIME_QUALITY_SCORECARD_TEST_PASS"

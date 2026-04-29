#!/usr/bin/env bash
set -e

TEST_NAME="$(basename "$0")"
trap 'rc=$?; echo "[FAIL] ${TEST_NAME}: line ${LINENO}"; exit $rc' ERR


REPO_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$REPO_ROOT" || exit 1

OUT="tests/z_ux_handoff_entrypoint_output_v1.json"

python3 runtime/emit_z_ux_handoff.py tests/z_ux_runtime_input_v1.json > "$OUT"

grep -q '"trigger_screen_id": "scan_capture_top"' "$OUT"
grep -q '"scan_processing_mode": "native"' "$OUT"
grep -q '"vision_supported": true' "$OUT"
grep -q '"routing_input": "trigger_screen_id"' "$OUT"
grep -q '"ui_screen": "scan_capture_top"' "$OUT"
grep -q '"ui_message": "Place your foot clearly in frame and capture the top view."' "$OUT"
grep -q '"primary_cta": "capture_top_view"' "$OUT"

echo "Z_UX_HANDOFF_ENTRYPOINT_TEST_PASS"

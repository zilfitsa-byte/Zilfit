#!/usr/bin/env bash
set -e

TEST_NAME="$(basename "$0")"
trap 'rc=$?; echo "[FAIL] ${TEST_NAME}: line ${LINENO}"; exit $rc' ERR


REPO_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$REPO_ROOT" || exit 1

OUT="tests/z_ux_runtime_packet_from_runtime_entrypoint_v1.json"

python3 runtime/emit_z_ux_runtime_packet.py \
  --trigger-stage scan_capture \
  --trigger-screen-id scan_capture_top \
  --prompt-text "Place your foot clearly in frame and capture the top view." \
  --next-expected-action capture_top_view \
  --guidance-type instruction \
  --user-goal-context daily_comfort \
  --safe-for-display true \
  --blocked-phrase-flag false \
  --confidence 0.97 \
  --scan-quality-context pending \
  --configured-image-input-mode auto \
  --supports-vision true \
  --out "$OUT" >/dev/null

python3 - <<'PY'
import json
from pathlib import Path

p = Path("tests/z_ux_runtime_packet_from_runtime_entrypoint_v1.json")
data = json.loads(p.read_text(encoding="utf-8"))

assert data["packet_name"] == "z_guide_z_ux_runtime_packet_v1"
assert data["trigger_stage"] == "scan_capture"
assert data["trigger_screen_id"] == "scan_capture_top"
assert data["prompt_text"] == "Place your foot clearly in frame and capture the top view."
assert data["next_expected_action"] == "capture_top_view"
assert data["scan_processing_mode"] == "native"
assert data["vision_supported"] is True
assert data["routing_input"] == "trigger_screen_id"

print("TEST_EMIT_Z_UX_RUNTIME_PACKET_PASS")
PY

#!/usr/bin/env bash
set -e

TEST_NAME="$(basename "$0")"
trap 'rc=$?; echo "[FAIL] ${TEST_NAME}: line ${LINENO}"; exit $rc' ERR


REPO_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$REPO_ROOT" || exit 1

python3 tests/test_scan_image_routing.py
python3 tests/test_z_ux_runtime_packet_builder.py
python3 tests/generate_z_ux_runtime_packet_json.py >/dev/null
python3 validators/validate_z_ux_runtime_packet.py tests/z_ux_runtime_packet_output_v1.json
Z_UX_LIVE_OUTPUT_TMP="$(mktemp)"
trap 'rm -f "$Z_UX_LIVE_OUTPUT_TMP"' EXIT
python3 tests/generate_z_ux_live_output_from_runtime.py "$Z_UX_LIVE_OUTPUT_TMP" >/dev/null
python3 validators/validate_z_ux_live_output.py "$Z_UX_LIVE_OUTPUT_TMP"
bash tests/test_emit_z_ux_runtime_packet.sh

echo "TEST_Z_UX_LIVE_OUTPUT_FULL_FLOW_PASS"

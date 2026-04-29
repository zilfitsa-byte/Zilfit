#!/usr/bin/env bash
set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/../../../.." && pwd)"
cd "$REPO_ROOT" || exit 1

echo "[1/7] routing test"
python3 tests/test_scan_image_routing.py

echo "[2/7] runtime packet builder test"
python3 tests/test_z_ux_runtime_packet_builder.py

echo "[3/7] runtime packet generation"
python3 tests/generate_z_ux_runtime_packet_json.py >/dev/null

echo "[4/7] runtime packet validation"
python3 validators/validate_z_ux_runtime_packet.py tests/z_ux_runtime_packet_output_v1.json

echo "[5/7] live output generation"
python3 tests/generate_z_ux_live_output_from_runtime.py >/dev/null

echo "[6/7] live output validation"
python3 validators/validate_z_ux_live_output.py tests/z_ux_live_output_from_runtime_v1.json

echo "[7/7] full readiness"
bash tests/test_handoff_readiness_full.sh

echo "RUN_V1_LOCAL_STACK_PASS"

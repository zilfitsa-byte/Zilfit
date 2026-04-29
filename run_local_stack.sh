#!/usr/bin/env bash
set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/." && pwd)"
cd "$REPO_ROOT" || exit 1

echo "[1/6] test routing"
python3 tests/test_scan_image_routing.py

echo "[2/6] test runtime packet builder"
python3 tests/test_z_ux_runtime_packet_builder.py

echo "[3/6] generate runtime packet"
python3 tests/generate_z_ux_runtime_packet_json.py >/dev/null

echo "[4/6] validate runtime packet"
python3 validators/validate_z_ux_runtime_packet.py tests/z_ux_runtime_packet_output_v1.json

echo "[5/6] generate live output"
python3 tests/generate_z_ux_live_output_from_runtime.py >/dev/null

echo "[6/6] validate live output"
python3 validators/validate_z_ux_live_output.py tests/z_ux_live_output_from_runtime_v1.json

echo "RUN_LOCAL_STACK_PASS"

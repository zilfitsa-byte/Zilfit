#!/usr/bin/env bash
set -e

TEST_NAME="$(basename "$0")"
trap 'rc=$?; echo "[FAIL] ${TEST_NAME}: line ${LINENO}"; exit $rc' ERR


cd /root/hermes/zilfit-ip-core || exit 1

python3 tests/generate_z_ux_runtime_packet_json.py >/dev/null
python3 validators/validate_z_ux_runtime_packet.py tests/z_ux_runtime_packet_output_v1.json

echo "TEST_VALIDATE_Z_UX_RUNTIME_PACKET_PASS"

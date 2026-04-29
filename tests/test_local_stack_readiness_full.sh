#!/usr/bin/env bash
set -e

TEST_NAME="$(basename "$0")"
trap 'rc=$?; echo "[FAIL] ${TEST_NAME}: line ${LINENO}"; exit $rc' ERR


cd /root/hermes/zilfit-ip-core || exit 1

python3 tests/test_scan_image_routing.py
python3 tests/test_z_ux_runtime_packet_builder.py
python3 tests/generate_z_ux_runtime_packet_json.py >/dev/null
python3 validators/validate_z_ux_runtime_packet.py tests/z_ux_runtime_packet_output_v1.json

bash tests/test_emit_z_ux_runtime_packet.sh
python3 tests/generate_z_ux_live_output_from_runtime.py >/dev/null
python3 validators/validate_z_ux_live_output.py tests/z_ux_live_output_from_runtime_v1.json

bash tests/test_z_ux_handoff_flow.sh
bash tests/test_emit_z_ux_handoff.sh
bash tests/test_run_z_ux_pipeline.sh
bash tests/test_run_local_handoff_gateway.sh

echo "LOCAL_STACK_READINESS_FULL_PASS"

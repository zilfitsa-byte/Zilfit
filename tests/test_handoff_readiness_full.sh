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
python3 tests/runtime_live_output_demo.py >/dev/null

grep -q 'Z-UX runtime packet validator created' docs/CURRENT_SYSTEM_STATE.md
grep -q 'Z-UX runtime packet validator tested' docs/CURRENT_SYSTEM_STATE.md
grep -q 'runtime entrypoint emitter created' docs/CURRENT_SYSTEM_STATE.md
grep -q 'runtime entrypoint emitter tested' docs/CURRENT_SYSTEM_STATE.md
grep -q 'runtime live output demo created' docs/CURRENT_SYSTEM_STATE.md
grep -q 'runtime live output demo tested' docs/CURRENT_SYSTEM_STATE.md

echo "HANDOFF_READINESS_FULL_PASS"

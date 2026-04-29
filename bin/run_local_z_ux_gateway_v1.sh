#!/usr/bin/env bash
set -e

cd /root/hermes/zilfit-ip-core || exit 1

IN="examples/runtime/reference_z_ux_runtime_input_v1.json"
OUT="examples/runtime/reference_local_handoff_gateway_output_v1.json"

python3 runtime/run_local_handoff_gateway.py "$IN" > "$OUT"

echo "LOCAL_Z_UX_GATEWAY_RUN_PASS"
echo "OUTPUT=$OUT"

# Local V1 Run

Main entrypoint:
bash bin/run_local_v1.sh

What it does:
1. Runs scan image routing tests
2. Runs runtime packet builder tests
3. Generates runtime packet JSON
4. Validates runtime packet JSON
5. Generates live output JSON
6. Validates live output JSON
7. Runs full readiness script

Important reference files:
- examples/runtime/reference_z_ux_runtime_input_v1.json
- examples/runtime/reference_z_ux_runtime_packet_output_v1.json
- examples/live_output/reference_z_ux_live_output_v1.json
- examples/runtime/reference_local_handoff_gateway_output_v1.json

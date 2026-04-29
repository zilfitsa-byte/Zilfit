# ZILFIT IP Core - Local Stack

## Purpose
Local end-to-end validation for:
- scan image routing
- Z-UX runtime packet building
- Z-UX runtime packet validation
- Z-UX live output building
- Z-UX live output validation
- local handoff gateway
- Z-UX pipeline

## Main files
- runtime/scan_image_routing.py
- runtime/z_ux_runtime_packet_builder.py
- runtime/emit_z_ux_runtime_packet.py
- runtime/z_ux_live_output_builder.py
- runtime/emit_z_ux_handoff.py
- runtime/run_z_ux_pipeline.py
- runtime/run_local_handoff_gateway.py

## Main validators
- validators/validate_z_ux_runtime_packet.py
- validators/validate_z_ux_live_output.py

## Main test scripts
- tests/test_scan_image_routing.py
- tests/test_z_ux_runtime_packet_builder.py
- tests/test_validate_z_ux_runtime_packet.sh
- tests/test_emit_z_ux_runtime_packet.sh
- tests/test_z_ux_live_output_full_flow.sh
- tests/test_z_ux_handoff_flow.sh
- tests/test_emit_z_ux_handoff.sh
- tests/test_run_z_ux_pipeline.sh
- tests/test_run_local_handoff_gateway.sh
- tests/test_local_stack_readiness_full.sh
- tests/test_handoff_readiness_full.sh

## One-command quick run
bash run_local_stack.sh

## Full readiness
bash tests/test_handoff_readiness_full.sh

## Expected success markers
- SCAN_IMAGE_ROUTING_TEST_PASS
- Z_UX_RUNTIME_PACKET_BUILDER_TEST_PASS
- Z_UX_RUNTIME_PACKET_VALIDATION_PASS
- TEST_EMIT_Z_UX_RUNTIME_PACKET_PASS
- Z_UX_LIVE_OUTPUT_VALIDATION_PASS
- Z_UX_HANDOFF_FLOW_TEST_PASS
- Z_UX_HANDOFF_FROM_JSON_TEST_PASS
- Z_UX_HANDOFF_ENTRYPOINT_TEST_PASS
- Z_UX_PIPELINE_TEST_PASS
- LOCAL_HANDOFF_GATEWAY_TEST_PASS
- HANDOFF_READINESS_FULL_PASS

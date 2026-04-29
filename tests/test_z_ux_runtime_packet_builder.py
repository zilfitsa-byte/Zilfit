#!/usr/bin/env python3
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from runtime.z_ux_runtime_packet_builder import build_z_ux_runtime_packet


data = build_z_ux_runtime_packet(
    trigger_stage="scan_capture",
    trigger_screen_id="scan_capture_top",
    prompt_text="Place your foot clearly in frame and capture the top view.",
    next_expected_action="capture_top_view",
    guidance_type="instruction",
    user_goal_context="daily_comfort",
    safe_for_display=True,
    blocked_phrase_flag=False,
    confidence=0.97,
    configured_image_input_mode="auto",
    model_capabilities={"supports_vision": True},
)

assert data["packet_name"] == "z_guide_z_ux_runtime_packet_v1"
assert data["schema_version"] == "v1"
assert data["source_agent"] == "Z-Guide"
assert data["target_agent"] == "Z-UX"

assert data["trigger_stage"] == "scan_capture"
assert data["trigger_screen_id"] == "scan_capture_top"
assert data["guidance_type"] == "instruction"
assert data["prompt_text"] == "Place your foot clearly in frame and capture the top view."
assert data["next_expected_action"] == "capture_top_view"
assert data["user_goal_context"] == "daily_comfort"

assert data["safe_for_display"] is True
assert data["blocked_phrase_flag"] is False
assert data["confidence"] == 0.97
assert data["scan_quality_context"] == "pending"

assert data["configured_image_input_mode"] == "auto"
assert data["model_capabilities"]["supports_vision"] is True

assert data["scan_processing_mode"] == "native"
assert data["vision_supported"] is True
assert data["routing_input"] == "trigger_screen_id"

print("Z_UX_RUNTIME_PACKET_BUILDER_TEST_PASS")

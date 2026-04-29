#!/usr/bin/env python3
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from runtime.scan_image_routing import build_scan_processing_context

p = Path("tests/z_guide_z_ux_runtime_packet_v1.json")
data = json.loads(p.read_text(encoding="utf-8"))

trigger_screen_id = data.get("trigger_screen_id")
model_caps = data.get("model_capabilities", {})
configured_mode = data.get("configured_image_input_mode", "auto")

routing = build_scan_processing_context(
    trigger_screen_id=trigger_screen_id,
    model_caps=model_caps,
    configured_mode=configured_mode,
)

print("===== RUNTIME HANDOFF DEMO =====")
print("incoming_packet:", data.get("packet_name"))
print("from_agent:", data.get("source_agent"))
print("to_agent:", data.get("target_agent"))
print()

display_status = "ALLOWED" if data.get("safe_for_display") else "BLOCKED"

print("display_status:", display_status)
print("trigger_stage:", data.get("trigger_stage"))
print("screen_id:", data.get("trigger_screen_id"))
print("ui_message:", data.get("prompt_text"))
print("guidance_type:", data.get("guidance_type"))
print("user_goal_context:", data.get("user_goal_context"))
print("next_action:", data.get("next_expected_action"))
print("scan_quality_context:", data.get("scan_quality_context"))
print()

print("configured_image_input_mode:", configured_mode)
print("vision_supported:", routing.get("vision_supported"))
print("scan_processing_mode:", routing.get("scan_processing_mode"))
print()

print("blocked_phrase_flag:", data.get("blocked_phrase_flag"))
print("confidence:", data.get("confidence"))
print("===== HANDOFF DEMO COMPLETE =====")

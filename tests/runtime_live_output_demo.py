#!/usr/bin/env python3
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from runtime.z_ux_runtime_packet_builder import build_z_ux_runtime_packet
from runtime.z_ux_live_output_builder import build_z_ux_live_output


def main() -> None:
    runtime_packet = build_z_ux_runtime_packet(
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

    live_output = build_z_ux_live_output(runtime_packet)

    print("===== RUNTIME LIVE OUTPUT DEMO =====")
    print("packet_name:", runtime_packet.get("packet_name"))
    print("task_id:", live_output.get("task_id"))
    print("source_packet_name:", live_output.get("source_packet_name"))
    print("trigger_screen_id:", live_output.get("trigger_screen_id"))
    print("ui_screen:", live_output.get("ui_screen"))
    print("ui_message:", live_output.get("ui_message"))
    print("primary_cta:", live_output.get("primary_cta"))
    print("scan_processing_mode:", live_output.get("scan_processing_mode"))
    print("vision_supported:", live_output.get("vision_supported"))
    print("routing_input:", live_output.get("routing_input"))
    print()
    print(json.dumps(live_output, ensure_ascii=False, indent=2))
    print("===== DEMO COMPLETE =====")


if __name__ == "__main__":
    main()

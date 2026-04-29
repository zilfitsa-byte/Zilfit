#!/usr/bin/env python3
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from runtime.z_ux_runtime_packet_builder import build_z_ux_runtime_packet

out = build_z_ux_runtime_packet(
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

target = Path("tests/z_ux_runtime_packet_output_v1.json")
target.write_text(json.dumps(out, ensure_ascii=False, indent=2), encoding="utf-8")

print(f"WROTE: {target}")

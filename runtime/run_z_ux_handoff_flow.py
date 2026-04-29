#!/usr/bin/env python3
from __future__ import annotations

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

    out = {
        "runtime_packet": runtime_packet,
        "live_output": live_output,
    }

    print(json.dumps(out, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()

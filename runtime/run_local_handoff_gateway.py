#!/usr/bin/env python3
from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from runtime.z_ux_runtime_packet_builder import build_z_ux_runtime_packet
from runtime.z_ux_live_output_builder import build_z_ux_live_output


def _require_json_file(path_str: str) -> Path:
    p = Path(path_str)
    if not p.exists():
        raise FileNotFoundError(f"input file not found: {p}")
    return p


def main() -> None:
    if len(sys.argv) != 2:
        print("Usage: run_local_handoff_gateway.py input.json")
        sys.exit(1)

    input_path = _require_json_file(sys.argv[1])
    data: dict[str, Any] = json.loads(input_path.read_text(encoding="utf-8"))

    runtime_packet = build_z_ux_runtime_packet(
        trigger_stage=data["trigger_stage"],
        trigger_screen_id=data["trigger_screen_id"],
        prompt_text=data["prompt_text"],
        next_expected_action=data["next_expected_action"],
        guidance_type=data.get("guidance_type", "instruction"),
        user_goal_context=data["user_goal_context"],
        safe_for_display=data.get("safe_for_display", True),
        blocked_phrase_flag=data.get("blocked_phrase_flag", False),
        confidence=data.get("confidence", 0.97),
        configured_image_input_mode=data.get("configured_image_input_mode", "auto"),
        model_capabilities=data.get("model_capabilities", {"supports_vision": True}),
        packet_name=data.get("packet_name", "z_guide_z_ux_runtime_packet_v1"),
        schema_version=data.get("schema_version", "v1"),
        source_agent=data.get("source_agent", "Z-Guide"),
        target_agent=data.get("target_agent", "Z-UX"),
        scan_quality_context=data.get("scan_quality_context", "pending"),
    )

    live_output = build_z_ux_live_output(runtime_packet)

    out = {
        "status": "ok",
        "gateway": "local_handoff_gateway_v1",
        "runtime_packet": runtime_packet,
        "live_output": live_output,
    }

    print(json.dumps(out, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()

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


def _require_str(data: dict, key: str) -> str:
    value = data.get(key)
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{key} must be a non-empty string")
    return value.strip()


def _require_bool(data: dict, key: str) -> bool:
    value = data.get(key)
    if not isinstance(value, bool):
        raise ValueError(f"{key} must be a boolean")
    return value


def _require_confidence(data: dict, key: str) -> float:
    value = data.get(key)
    if not isinstance(value, (int, float)):
        raise ValueError(f"{key} must be numeric")
    value = float(value)
    if value < 0.0 or value > 1.0:
        raise ValueError(f"{key} must be between 0 and 1")
    return value


def main() -> None:
    if len(sys.argv) != 2:
        print("Usage: python3 runtime/emit_z_ux_handoff.py <input.json>")
        sys.exit(1)

    p = Path(sys.argv[1])
    data = json.loads(p.read_text(encoding="utf-8"))

    runtime_packet = build_z_ux_runtime_packet(
        trigger_stage=_require_str(data, "trigger_stage"),
        trigger_screen_id=_require_str(data, "trigger_screen_id"),
        prompt_text=_require_str(data, "prompt_text"),
        next_expected_action=_require_str(data, "next_expected_action"),
        guidance_type=_require_str(data, "guidance_type"),
        user_goal_context=_require_str(data, "user_goal_context"),
        safe_for_display=_require_bool(data, "safe_for_display"),
        blocked_phrase_flag=_require_bool(data, "blocked_phrase_flag"),
        confidence=_require_confidence(data, "confidence"),
        configured_image_input_mode=_require_str(data, "configured_image_input_mode"),
        model_capabilities=data.get("model_capabilities", {}),
    )

    live_output = build_z_ux_live_output(runtime_packet)

    payload = {
        "runtime_packet": runtime_packet,
        "live_output": live_output,
    }

    print(json.dumps(payload, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()

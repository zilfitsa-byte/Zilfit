#!/usr/bin/env python3
import json
import sys
from pathlib import Path


def fail(msg: str) -> None:
    print(f"VALIDATION_FAILED: {msg}")
    sys.exit(1)


def require_str(data: dict, key: str) -> str:
    value = data.get(key)
    if not isinstance(value, str) or not value.strip():
        fail(f"{key} must be a non-empty string")
    return value


def require_bool(data: dict, key: str) -> bool:
    value = data.get(key)
    if not isinstance(value, bool):
        fail(f"{key} must be a boolean")
    return value


def main() -> None:
    if len(sys.argv) != 2:
        fail("Usage: validate_z_ux_live_output.py file.json")

    p = Path(sys.argv[1])
    if not p.exists():
        fail(f"missing file: {p}")

    try:
        data = json.loads(p.read_text(encoding="utf-8"))
    except Exception as e:
        fail(f"invalid json: {e}")

    task_id = require_str(data, "task_id")
    source_packet_name = require_str(data, "source_packet_name")
    trigger_screen_id = require_str(data, "trigger_screen_id")
    prompt_text = require_str(data, "prompt_text")
    next_expected_action = require_str(data, "next_expected_action")
    ui_screen = require_str(data, "ui_screen")
    ui_message = require_str(data, "ui_message")
    primary_cta = require_str(data, "primary_cta")
    scan_processing_mode = require_str(data, "scan_processing_mode")
    routing_input = require_str(data, "routing_input")
    vision_supported = require_bool(data, "vision_supported")

    if task_id != "z_ux_live_output_v1":
        fail("task_id must equal z_ux_live_output_v1")

    if source_packet_name != "z_guide_z_ux_runtime_packet_v1":
        fail("source_packet_name must equal z_guide_z_ux_runtime_packet_v1")

    if scan_processing_mode not in {"native", "text_fallback"}:
        fail("scan_processing_mode must be one of native/text_fallback")

    if routing_input != "trigger_screen_id":
        fail("routing_input must equal trigger_screen_id")

    if ui_screen != trigger_screen_id:
        fail("ui_screen must equal trigger_screen_id")

    if ui_message != prompt_text:
        fail("ui_message must equal prompt_text")

    if primary_cta != next_expected_action:
        fail("primary_cta must equal next_expected_action")

    if scan_processing_mode == "native" and vision_supported is not True:
        fail("native scan_processing_mode requires vision_supported=true")

    if scan_processing_mode == "text_fallback" and vision_supported not in {True, False}:
        fail("vision_supported must be boolean")

    print("Z_UX_LIVE_OUTPUT_VALIDATION_PASS")


if __name__ == "__main__":
    main()

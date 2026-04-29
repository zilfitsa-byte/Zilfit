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
    return value.strip()


def require_bool(data: dict, key: str) -> bool:
    value = data.get(key)
    if not isinstance(value, bool):
        fail(f"{key} must be a boolean")
    return value


def require_number(data: dict, key: str) -> float:
    value = data.get(key)
    if not isinstance(value, (int, float)):
        fail(f"{key} must be numeric")
    return float(value)


def main() -> None:
    if len(sys.argv) != 2:
        fail("Usage: validate_z_ux_runtime_packet.py file.json")

    p = Path(sys.argv[1])
    if not p.exists():
        fail(f"file not found: {p}")

    try:
        data = json.loads(p.read_text(encoding="utf-8"))
    except Exception as e:
        fail(f"invalid json: {e}")

    if not isinstance(data, dict):
        fail("root must be a JSON object")

    packet_name = require_str(data, "packet_name")
    schema_version = require_str(data, "schema_version")
    source_agent = require_str(data, "source_agent")
    target_agent = require_str(data, "target_agent")
    trigger_stage = require_str(data, "trigger_stage")
    trigger_screen_id = require_str(data, "trigger_screen_id")
    guidance_type = require_str(data, "guidance_type")
    prompt_text = require_str(data, "prompt_text")
    next_expected_action = require_str(data, "next_expected_action")
    user_goal_context = require_str(data, "user_goal_context")
    scan_quality_context = require_str(data, "scan_quality_context")
    configured_image_input_mode = require_str(data, "configured_image_input_mode")
    safe_for_display = require_bool(data, "safe_for_display")
    blocked_phrase_flag = require_bool(data, "blocked_phrase_flag")
    confidence = require_number(data, "confidence")
    scan_processing_mode = require_str(data, "scan_processing_mode")
    vision_supported = require_bool(data, "vision_supported")
    routing_input = require_str(data, "routing_input")

    model_capabilities = data.get("model_capabilities")
    if not isinstance(model_capabilities, dict):
        fail("model_capabilities must be an object")

    supports_vision = model_capabilities.get("supports_vision")
    if not isinstance(supports_vision, bool):
        fail("model_capabilities.supports_vision must be boolean")

    if packet_name != "z_guide_z_ux_runtime_packet_v1":
        fail("packet_name must equal z_guide_z_ux_runtime_packet_v1")

    if schema_version != "v1":
        fail("schema_version must equal v1")

    if source_agent != "Z-Guide":
        fail("source_agent must equal Z-Guide")

    if target_agent != "Z-UX":
        fail("target_agent must equal Z-UX")

    if configured_image_input_mode not in {"auto", "native", "text_fallback"}:
        fail("configured_image_input_mode must be one of auto/native/text_fallback")

    if scan_processing_mode not in {"native", "text_fallback"}:
        fail("scan_processing_mode must be one of native/text_fallback")

    if routing_input != "trigger_screen_id":
        fail("routing_input must equal trigger_screen_id")

    if vision_supported != supports_vision:
        fail("vision_supported must equal model_capabilities.supports_vision")

    if configured_image_input_mode == "text_fallback" and scan_processing_mode != "text_fallback":
        fail("text_fallback mode must produce text_fallback scan_processing_mode")

    if configured_image_input_mode == "native":
        expected = "native" if supports_vision else "text_fallback"
        if scan_processing_mode != expected:
            fail("native configured mode produced wrong scan_processing_mode")

    if not (0.0 <= confidence <= 1.0):
        fail("confidence must be between 0 and 1")

    print("Z_UX_RUNTIME_PACKET_VALIDATION_PASS")


if __name__ == "__main__":
    main()

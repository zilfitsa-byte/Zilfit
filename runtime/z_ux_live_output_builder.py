#!/usr/bin/env python3
from __future__ import annotations

from typing import Any


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


def _require_number(data: dict, key: str) -> float:
    value = data.get(key)
    if not isinstance(value, (int, float)):
        raise ValueError(f"{key} must be numeric")
    return float(value)


def _require_dict(data: dict, key: str) -> dict:
    value = data.get(key)
    if not isinstance(value, dict):
        raise ValueError(f"{key} must be a dict")
    return value


def build_z_ux_live_output(runtime_packet: dict[str, Any]) -> dict[str, Any]:
    if not isinstance(runtime_packet, dict):
        raise ValueError("runtime_packet must be a dict")

    packet_name = _require_str(runtime_packet, "packet_name")
    source_agent = _require_str(runtime_packet, "source_agent")
    target_agent = _require_str(runtime_packet, "target_agent")
    trigger_stage = _require_str(runtime_packet, "trigger_stage")
    trigger_screen_id = _require_str(runtime_packet, "trigger_screen_id")
    guidance_type = _require_str(runtime_packet, "guidance_type")
    prompt_text = _require_str(runtime_packet, "prompt_text")
    next_expected_action = _require_str(runtime_packet, "next_expected_action")
    user_goal_context = _require_str(runtime_packet, "user_goal_context")
    scan_quality_context = _require_str(runtime_packet, "scan_quality_context")
    configured_image_input_mode = _require_str(runtime_packet, "configured_image_input_mode")
    scan_processing_mode = _require_str(runtime_packet, "scan_processing_mode")
    routing_input = _require_str(runtime_packet, "routing_input")

    safe_for_display = _require_bool(runtime_packet, "safe_for_display")
    blocked_phrase_flag = _require_bool(runtime_packet, "blocked_phrase_flag")
    confidence = _require_number(runtime_packet, "confidence")
    vision_supported = _require_bool(runtime_packet, "vision_supported")
    model_capabilities = _require_dict(runtime_packet, "model_capabilities")

    if packet_name != "z_guide_z_ux_runtime_packet_v1":
        raise ValueError("unexpected packet_name for Z-UX live output builder")

    if source_agent != "Z-Guide":
        raise ValueError("source_agent must be Z-Guide")

    if target_agent != "Z-UX":
        raise ValueError("target_agent must be Z-UX")

    if routing_input != "trigger_screen_id":
        raise ValueError("routing_input must equal trigger_screen_id")

    if not safe_for_display:
        raise ValueError("safe_for_display must be true for live output")

    return {
        "task_id": "z_ux_live_output_v1",
        "source_packet_name": packet_name,
        "source_agent": source_agent,
        "target_agent": target_agent,
        "trigger_stage": trigger_stage,
        "trigger_screen_id": trigger_screen_id,
        "guidance_type": guidance_type,
        "prompt_text": prompt_text,
        "next_expected_action": next_expected_action,
        "user_goal_context": user_goal_context,
        "scan_quality_context": scan_quality_context,
        "safe_for_display": safe_for_display,
        "blocked_phrase_flag": blocked_phrase_flag,
        "confidence": confidence,
        "configured_image_input_mode": configured_image_input_mode,
        "scan_processing_mode": scan_processing_mode,
        "vision_supported": vision_supported,
        "routing_input": routing_input,
        "model_capabilities": model_capabilities,
        "ui_screen": trigger_screen_id,
        "ui_message": prompt_text,
        "primary_cta": next_expected_action,
    }


if __name__ == "__main__":
    sample = {
        "packet_name": "z_guide_z_ux_runtime_packet_v1",
        "source_agent": "Z-Guide",
        "target_agent": "Z-UX",
        "trigger_stage": "scan_capture",
        "trigger_screen_id": "scan_capture_top",
        "guidance_type": "instruction",
        "prompt_text": "Place your foot clearly in frame and capture the top view.",
        "next_expected_action": "capture_top_view",
        "user_goal_context": "daily_comfort",
        "safe_for_display": True,
        "blocked_phrase_flag": False,
        "confidence": 0.97,
        "scan_quality_context": "pending",
        "configured_image_input_mode": "auto",
        "model_capabilities": {"supports_vision": True},
        "scan_processing_mode": "native",
        "vision_supported": True,
        "routing_input": "trigger_screen_id",
    }
    print(build_z_ux_live_output(sample))

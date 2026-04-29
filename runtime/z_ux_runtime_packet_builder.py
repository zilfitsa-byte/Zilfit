#!/usr/bin/env python3
from __future__ import annotations

from typing import Any

from runtime.scan_image_routing import build_scan_processing_context


def _require_non_empty_str(value: Any, field_name: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{field_name} must be a non-empty string")
    return value.strip()


def _require_bool(value: Any, field_name: str) -> bool:
    if not isinstance(value, bool):
        raise ValueError(f"{field_name} must be a boolean")
    return value


def _require_confidence(value: Any) -> float:
    if not isinstance(value, (int, float)):
        raise ValueError("confidence must be numeric")
    value = float(value)
    if value < 0.0 or value > 1.0:
        raise ValueError("confidence must be between 0.0 and 1.0")
    return value


def build_z_ux_runtime_packet(
    *,
    trigger_stage: str,
    trigger_screen_id: str,
    prompt_text: str,
    next_expected_action: str,
    guidance_type: str,
    user_goal_context: str,
    safe_for_display: bool,
    blocked_phrase_flag: bool,
    confidence: float,
    configured_image_input_mode: str = "auto",
    model_capabilities: dict | None = None,
    packet_name: str = "z_guide_z_ux_runtime_packet_v1",
    schema_version: str = "v1",
    source_agent: str = "Z-Guide",
    target_agent: str = "Z-UX",
    scan_quality_context: str = "pending",
) -> dict:
    trigger_stage = _require_non_empty_str(trigger_stage, "trigger_stage")
    trigger_screen_id = _require_non_empty_str(trigger_screen_id, "trigger_screen_id")
    prompt_text = _require_non_empty_str(prompt_text, "prompt_text")
    next_expected_action = _require_non_empty_str(next_expected_action, "next_expected_action")
    guidance_type = _require_non_empty_str(guidance_type, "guidance_type")
    user_goal_context = _require_non_empty_str(user_goal_context, "user_goal_context")
    configured_image_input_mode = _require_non_empty_str(
        configured_image_input_mode, "configured_image_input_mode"
    )
    packet_name = _require_non_empty_str(packet_name, "packet_name")
    schema_version = _require_non_empty_str(schema_version, "schema_version")
    source_agent = _require_non_empty_str(source_agent, "source_agent")
    target_agent = _require_non_empty_str(target_agent, "target_agent")
    scan_quality_context = _require_non_empty_str(
        scan_quality_context, "scan_quality_context"
    )

    safe_for_display = _require_bool(safe_for_display, "safe_for_display")
    blocked_phrase_flag = _require_bool(blocked_phrase_flag, "blocked_phrase_flag")
    confidence = _require_confidence(confidence)

    if model_capabilities is None:
        model_capabilities = {}
    if not isinstance(model_capabilities, dict):
        raise ValueError("model_capabilities must be a dict or None")

    routing = build_scan_processing_context(
        trigger_screen_id=trigger_screen_id,
        model_caps=model_capabilities,
        configured_mode=configured_image_input_mode,
    )

    return {
        "packet_name": packet_name,
        "schema_version": schema_version,
        "source_agent": source_agent,
        "target_agent": target_agent,
        "trigger_stage": trigger_stage,
        "trigger_screen_id": trigger_screen_id,
        "guidance_type": guidance_type,
        "prompt_text": prompt_text,
        "next_expected_action": next_expected_action,
        "user_goal_context": user_goal_context,
        "safe_for_display": safe_for_display,
        "blocked_phrase_flag": blocked_phrase_flag,
        "confidence": confidence,
        "scan_quality_context": scan_quality_context,
        "configured_image_input_mode": configured_image_input_mode,
        "model_capabilities": model_capabilities,
        "scan_processing_mode": routing["scan_processing_mode"],
        "vision_supported": routing["vision_supported"],
        "routing_input": routing["routing_input"],
    }


if __name__ == "__main__":
    sample = build_z_ux_runtime_packet(
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
    print(sample)

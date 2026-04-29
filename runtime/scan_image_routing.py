#!/usr/bin/env python3

VISION_SCREEN_IDS = {
    "scan_capture_top",
    "scan_capture_side",
    "scan_quality_check",
}

OPTIONAL_VISION_SCREEN_IDS = {
    "scan_capture_gait_optional",
}

ALL_VISION_SCREEN_IDS = VISION_SCREEN_IDS | OPTIONAL_VISION_SCREEN_IDS


def supports_vision(model_caps: dict | None) -> bool:
    if not model_caps:
        return False
    return bool(model_caps.get("supports_vision", False))


def decide_scan_image_mode(
    trigger_screen_id: str,
    model_caps: dict | None = None,
    configured_mode: str = "auto",
) -> str:
    """
    Returns one of:
    - native
    - text_fallback
    """

    if configured_mode not in {"auto", "native", "text_fallback"}:
        raise ValueError(f"Unsupported configured_mode: {configured_mode}")

    if configured_mode == "native":
        return "native" if supports_vision(model_caps) else "text_fallback"

    if configured_mode == "text_fallback":
        return "text_fallback"

    if trigger_screen_id not in ALL_VISION_SCREEN_IDS:
        return "text_fallback"

    if supports_vision(model_caps):
        return "native"

    return "text_fallback"


def build_scan_processing_context(
    trigger_screen_id: str,
    model_caps: dict | None = None,
    configured_mode: str = "auto",
) -> dict:
    mode = decide_scan_image_mode(
        trigger_screen_id=trigger_screen_id,
        model_caps=model_caps,
        configured_mode=configured_mode,
    )

    return {
        "routing_input": "trigger_screen_id",
        "trigger_screen_id": trigger_screen_id,
        "scan_processing_mode": mode,
        "vision_supported": supports_vision(model_caps),
        "configured_mode": configured_mode,
    }


if __name__ == "__main__":
    sample = build_scan_processing_context(
        trigger_screen_id="scan_capture_top",
        model_caps={"supports_vision": True},
        configured_mode="auto",
    )
    print(sample)

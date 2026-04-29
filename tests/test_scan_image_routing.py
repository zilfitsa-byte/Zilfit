#!/usr/bin/env python3
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from runtime.scan_image_routing import decide_scan_image_mode, build_scan_processing_context

assert decide_scan_image_mode("scan_capture_top", {"supports_vision": True}, "auto") == "native"
assert decide_scan_image_mode("scan_capture_top", {"supports_vision": False}, "auto") == "text_fallback"
assert decide_scan_image_mode("unknown_screen", {"supports_vision": True}, "auto") == "text_fallback"
assert decide_scan_image_mode("scan_capture_side", {"supports_vision": True}, "native") == "native"
assert decide_scan_image_mode("scan_capture_side", {"supports_vision": False}, "native") == "text_fallback"
assert decide_scan_image_mode("scan_quality_check", {"supports_vision": True}, "text_fallback") == "text_fallback"

data = build_scan_processing_context(
    trigger_screen_id="scan_capture_top",
    model_caps={"supports_vision": True},
    configured_mode="auto",
)

assert data["scan_processing_mode"] == "native"
assert data["vision_supported"] is True
assert data["trigger_screen_id"] == "scan_capture_top"
assert data["routing_input"] == "trigger_screen_id"

print("SCAN_IMAGE_ROUTING_TEST_PASS")

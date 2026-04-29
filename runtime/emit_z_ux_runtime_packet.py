#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from runtime.z_ux_runtime_packet_builder import build_z_ux_runtime_packet


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--trigger-stage", required=True)
    parser.add_argument("--trigger-screen-id", required=True)
    parser.add_argument("--prompt-text", required=True)
    parser.add_argument("--next-expected-action", required=True)
    parser.add_argument("--guidance-type", default="instruction")
    parser.add_argument("--user-goal-context", default="daily_comfort")
    parser.add_argument("--safe-for-display", default="true")
    parser.add_argument("--blocked-phrase-flag", default="false")
    parser.add_argument("--confidence", type=float, default=0.97)
    parser.add_argument("--scan-quality-context", default="pending")
    parser.add_argument("--configured-image-input-mode", default="auto")
    parser.add_argument("--supports-vision", default="true")
    parser.add_argument("--packet-name", default="z_guide_z_ux_runtime_packet_v1")
    parser.add_argument("--schema-version", default="v1")
    parser.add_argument("--source-agent", default="Z-Guide")
    parser.add_argument("--target-agent", default="Z-UX")
    parser.add_argument("--out", default="-")

    args = parser.parse_args()

    safe_for_display = args.safe_for_display.strip().lower() == "true"
    blocked_phrase_flag = args.blocked_phrase_flag.strip().lower() == "true"
    supports_vision = args.supports_vision.strip().lower() == "true"

    packet = build_z_ux_runtime_packet(
        trigger_stage=args.trigger_stage,
        trigger_screen_id=args.trigger_screen_id,
        prompt_text=args.prompt_text,
        next_expected_action=args.next_expected_action,
        guidance_type=args.guidance_type,
        user_goal_context=args.user_goal_context,
        safe_for_display=safe_for_display,
        blocked_phrase_flag=blocked_phrase_flag,
        confidence=args.confidence,
        scan_quality_context=args.scan_quality_context,
        configured_image_input_mode=args.configured_image_input_mode,
        model_capabilities={"supports_vision": supports_vision},
        packet_name=args.packet_name,
        schema_version=args.schema_version,
        source_agent=args.source_agent,
        target_agent=args.target_agent,
    )

    text = json.dumps(packet, ensure_ascii=False, indent=2)

    if args.out == "-":
        print(text)
    else:
        Path(args.out).write_text(text + "\n", encoding="utf-8")
        print(f"WROTE: {args.out}")


if __name__ == "__main__":
    main()

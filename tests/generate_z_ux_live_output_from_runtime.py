#!/usr/bin/env python3
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from runtime.z_ux_live_output_builder import build_z_ux_live_output

source = Path("tests/z_ux_runtime_packet_output_v1.json")
if not source.exists():
    raise SystemExit("missing source runtime packet: tests/z_ux_runtime_packet_output_v1.json")

runtime_packet = json.loads(source.read_text(encoding="utf-8"))
out = build_z_ux_live_output(runtime_packet)

target = Path("tests/z_ux_live_output_from_runtime_v1.json")
target.write_text(json.dumps(out, ensure_ascii=False, indent=2), encoding="utf-8")

print(f"WROTE: {target}")

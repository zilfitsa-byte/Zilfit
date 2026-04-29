#!/usr/bin/env bash
set -e

TEST_NAME="$(basename "$0")"
trap 'rc=$?; echo "[FAIL] ${TEST_NAME}: line ${LINENO}"; exit $rc' ERR


cd /root/hermes/zilfit-ip-core || exit 1

BASE="tests/z_ux_runtime_packet_output_v1.json"

python3 - <<'PY'
import json
from pathlib import Path

src = Path("tests/z_ux_runtime_packet_output_v1.json")
data = json.loads(src.read_text(encoding="utf-8"))

cases = []

a = dict(data)
a["schema_version"] = "v2"
cases.append(("bad_schema_version.json", a))

b = dict(data)
b["routing_input"] = "wrong_field"
cases.append(("bad_routing_input.json", b))

c = dict(data)
c["scan_processing_mode"] = "broken_mode"
cases.append(("bad_scan_processing_mode.json", c))

for name, payload in cases:
    Path("tests", name).write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
PY

if python3 validators/validate_z_ux_runtime_packet.py tests/bad_schema_version.json; then
  echo "EXPECTED validator failure for bad_schema_version.json"
  exit 1
fi
if python3 validators/validate_z_ux_runtime_packet.py tests/bad_routing_input.json; then
  echo "EXPECTED validator failure for bad_routing_input.json"
  exit 1
fi
if python3 validators/validate_z_ux_runtime_packet.py tests/bad_scan_processing_mode.json; then
  echo "EXPECTED validator failure for bad_scan_processing_mode.json"
  exit 1
fi

echo "NEGATIVE_Z_UX_RUNTIME_PACKET_TEST_PASS"

#!/usr/bin/env bash
set -e

TEST_NAME="$(basename "$0")"
trap 'rc=$?; echo "[FAIL] ${TEST_NAME}: line ${LINENO}"; exit $rc' ERR


cd /root/hermes/zilfit-ip-core || exit 1

python3 - <<'PY'
import json
from pathlib import Path

src = Path("tests/z_ux_handoff_entrypoint_output_v1.json")
data = json.loads(src.read_text(encoding="utf-8"))

a = dict(data)
a["routing_input"] = "bad_routing"

b = dict(data)
b["trigger_screen_id"] = ""

Path("tests/bad_handoff_routing_input.json").write_text(
    json.dumps(a, ensure_ascii=False, indent=2) + "\n",
    encoding="utf-8",
)
Path("tests/bad_handoff_trigger_screen_id.json").write_text(
    json.dumps(b, ensure_ascii=False, indent=2) + "\n",
    encoding="utf-8",
)
PY

python3 validators/validate_z_ux_runtime_packet.py tests/bad_handoff_routing_input.json && exit 1 || true
python3 validators/validate_z_ux_runtime_packet.py tests/bad_handoff_trigger_screen_id.json && exit 1 || true

echo "NEGATIVE_Z_UX_HANDOFF_ENTRYPOINT_TEST_PASS"

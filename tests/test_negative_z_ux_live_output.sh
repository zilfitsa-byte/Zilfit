#!/usr/bin/env bash
set -e

TEST_NAME="$(basename "$0")"
trap 'rc=$?; echo "[FAIL] ${TEST_NAME}: line ${LINENO}"; exit $rc' ERR


cd /root/hermes/zilfit-ip-core || exit 1

python3 - <<'PY'
import json
from pathlib import Path

src = Path("tests/z_ux_live_output_from_runtime_v1.json")
data = json.loads(src.read_text(encoding="utf-8"))

cases = []

a = dict(data)
a["task_id"] = "wrong_task"
cases.append(("tests/bad_live_task_id.json", a))

b = dict(data)
b["routing_input"] = "wrong_field"
cases.append(("tests/bad_live_routing_input.json", b))

c = dict(data)
c["primary_cta"] = "wrong_cta"
cases.append(("tests/bad_live_primary_cta.json", c))

for path, payload in cases:
    Path(path).write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
PY

python3 validators/validate_z_ux_live_output.py tests/bad_live_task_id.json && exit 1 || true
python3 validators/validate_z_ux_live_output.py tests/bad_live_routing_input.json && exit 1 || true
if python3 validators/validate_z_ux_live_output.py tests/bad_live_primary_cta.json; then
  echo "EXPECTED validator failure for bad_live_primary_cta.json"
  exit 1
fi

echo "NEGATIVE_Z_UX_LIVE_OUTPUT_TEST_PASS"

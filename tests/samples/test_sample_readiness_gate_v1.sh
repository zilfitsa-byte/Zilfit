#!/usr/bin/env bash
set -euo pipefail

if [ "${ZILFIT_SKIP_SAMPLE_READINESS_TEST:-0}" = "1" ]; then
  echo "SAMPLE_READINESS_GATE_TEST_SKIPPED_DURING_PARENT_GATE"
  exit 0
fi

cd "$(dirname "$0")/../.."

bash -n ops/samples/run_sample_readiness_gate.sh

/usr/bin/bash ops/samples/run_sample_readiness_gate.sh

LATEST_JSON="$(ls -t reports/samples/sample_readiness_*.json 2>/dev/null | head -n 1)"
test -n "$LATEST_JSON"

python3 - "$LATEST_JSON" <<'PY'
import json
import sys

d = json.load(open(sys.argv[1], encoding="utf-8"))

assert d["schema_version"] == "v1"
assert d["project"] == "ZILFIT"
assert d["report_type"] == "sample_readiness_gate"
assert isinstance(d["score"], int)
assert 0 <= d["score"] <= 100
assert d["status"] in {"blocked", "review_required", "sample_ready"}

decision = d["decision"]
assert decision["allow_public_marketing_claims"] is False
assert decision["allow_medical_or_treatment_claims"] is False
assert decision["allow_mass_production"] is False

assert "No medical" in d["boundary"]

print("SAMPLE_READINESS_GATE_TEST_PASS")
PY

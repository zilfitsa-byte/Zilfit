#!/usr/bin/env bash
set -euo pipefail

if [ "${ZILFIT_SKIP_READINESS_TEST:-0}" = "1" ]; then
  echo "BUSINESS_READINESS_INDEX_TEST_SKIPPED_DURING_PARENT_GATE"
  exit 0
fi

cd "$(dirname "$0")/../.."

bash -n ops/readiness/run_business_readiness_index.sh

/usr/bin/bash ops/readiness/run_business_readiness_index.sh

LATEST_JSON="$(ls -t reports/readiness/business_readiness_*.json 2>/dev/null | head -n 1)"

test -n "$LATEST_JSON"

python3 - "$LATEST_JSON" <<'PY'
import json
import sys

data = json.load(open(sys.argv[1], encoding="utf-8"))

assert data["schema_version"] == "v1"
assert data["project"] == "ZILFIT"
assert data["report_type"] == "business_readiness_index"
assert isinstance(data["score"], int)
assert 0 <= data["score"] <= 100
assert data["status"] in {"blocked", "review_required", "internal_ready", "demo_ready"}
assert "checks" in data
assert "No medical" in data["boundary"]

print("BUSINESS_READINESS_INDEX_TEST_PASS")
PY

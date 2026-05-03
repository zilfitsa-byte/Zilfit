#!/usr/bin/env bash
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
cd "$REPO_ROOT"

TS="$(date -u +"%Y-%m-%dT%H-%M-%SZ")"
REPORT_DIR="reports/samples"
REPORT_JSON="${REPORT_DIR}/sample_readiness_${TS}.json"
REPORT_MD="${REPORT_DIR}/sample_readiness_${TS}.md"
LOG_DIR="logs"
LOG_FILE="${LOG_DIR}/sample_readiness_${TS}.log"

mkdir -p "$REPORT_DIR" "$LOG_DIR"

score=0
working_tree_status="dirty"
quality_gate_status="fail"
nightly_status="fail"
business_readiness_status="unknown"
business_readiness_score=0
preproduction_simulator_status="unknown"

if [ -z "$(git status --short)" ]; then
  working_tree_status="clean"
  score=$((score + 20))
fi

if ZILFIT_SKIP_SAMPLE_READINESS_TEST=1 /usr/bin/bash ops/quality/run_quality_gate.sh > "${LOG_FILE}.quality" 2>&1; then
  quality_gate_status="pass"
  score=$((score + 20))
fi

if ZILFIT_SKIP_SAMPLE_READINESS_TEST=1 /usr/bin/bash ops/agent_runner/run_nightly_check.sh > "${LOG_FILE}.nightly" 2>&1; then
  nightly_status="pass"
  score=$((score + 20))
fi

if ZILFIT_SKIP_SAMPLE_READINESS_TEST=1 /usr/bin/bash ops/readiness/run_business_readiness_index.sh > "${LOG_FILE}.business_readiness" 2>&1; then
  latest_business_json="$(ls -t reports/readiness/business_readiness_*.json 2>/dev/null | head -n 1 || true)"
  if [ -n "$latest_business_json" ]; then
    business_readiness_score="$(python3 - <<PY
import json
d=json.load(open("$latest_business_json", encoding="utf-8"))
print(d.get("score", 0))
PY
)"
    business_readiness_status="$(python3 - <<PY
import json
d=json.load(open("$latest_business_json", encoding="utf-8"))
print(d.get("status", "unknown"))
PY
)"
    if [ "$business_readiness_status" = "demo_ready" ] && [ "$business_readiness_score" -ge 100 ]; then
      score=$((score + 25))
    fi
  fi
fi

tmp_dir="$(mktemp -d)"
trap 'rm -rf "$tmp_dir"' EXIT

sample_input="$tmp_dir/preproduction_sample_input.json"
sample_report="$tmp_dir/preproduction_sample_output.json"

cat > "$sample_input" <<JSON
{
  "schema_version": "v1",
  "project": "ZILFIT",
  "sample_batch_id": "engineering_sample_batch_001",
  "sample_count": 5,
  "purpose": "engineering fit, pressure-density, and sensor-readiness review only",
  "allowed_use": "doctor/reviewer supervised engineering feedback",
  "blocked_claims": [
    "medical",
    "diagnostic",
    "therapeutic",
    "clinical",
    "psychological treatment",
    "pain reduction",
    "hormone regulation"
  ],
  "required_before_public_claims": [
    "physical coupon validation",
    "reviewer feedback",
    "documented test protocol",
    "formal approvals if medical claims are ever considered"
  ]
}
JSON

if python3 runtime/preproduction_sample_simulator.py "$sample_input" "$sample_report" > "${LOG_FILE}.preproduction" 2>&1; then
  preproduction_simulator_status="$(python3 - <<PY
import json
d=json.load(open("$sample_report", encoding="utf-8"))
print(d.get("status", "unknown"))
PY
)"
  if [ "$preproduction_simulator_status" = "sample_ready" ]; then
    score=$((score + 15))
  fi
fi

sample_status="blocked"
if [ "$score" -ge 95 ]; then
  sample_status="sample_ready"
elif [ "$score" -ge 75 ]; then
  sample_status="review_required"
fi

cat > "$REPORT_JSON" <<JSON
{
  "schema_version": "v1",
  "project": "ZILFIT",
  "report_type": "sample_readiness_gate",
  "timestamp_utc": "$TS",
  "score": $score,
  "max_score": 100,
  "status": "$sample_status",
  "checks": {
    "working_tree": "$working_tree_status",
    "quality_gate": "$quality_gate_status",
    "nightly_check": "$nightly_status",
    "business_readiness_score": $business_readiness_score,
    "business_readiness_status": "$business_readiness_status",
    "preproduction_sample_simulator": "$preproduction_simulator_status"
  },
  "decision": {
    "engineering_demo_ready": "$business_readiness_status",
    "allow_five_engineering_samples": "$([ "$sample_status" = "sample_ready" ] && echo true || echo false)",
    "allow_public_marketing_claims": false,
    "allow_medical_or_treatment_claims": false,
    "allow_mass_production": false
  },
  "boundary": "Sample readiness gate for engineering review only. No medical, diagnostic, therapeutic, clinical, psychological treatment, pain, hormone, disease, or cure claims."
}
JSON

cat > "$REPORT_MD" <<MD
# ZILFIT Sample Readiness Gate

## Result

- Score: ${score}/100
- Status: ${sample_status}

## Checks

| Check | Status |
|---|---|
| Working tree | ${working_tree_status} |
| Quality gate | ${quality_gate_status} |
| Nightly check | ${nightly_status} |
| Business readiness | ${business_readiness_score} / ${business_readiness_status} |
| Preproduction sample simulator | ${preproduction_simulator_status} |

## Decision

| Decision | Value |
|---|---|
| Allow five engineering samples | $([ "$sample_status" = "sample_ready" ] && echo YES || echo NO) |
| Allow public marketing claims | NO |
| Allow medical/treatment claims | NO |
| Allow mass production | NO |

## Boundary

Engineering sample-readiness review only. No medical, diagnostic, therapeutic, clinical, psychological treatment, pain, hormone, disease, or cure claims.
MD

echo "ZILFIT_SAMPLE_READINESS_SCORE=${score}"
echo "ZILFIT_SAMPLE_READINESS_STATUS=${sample_status}"
echo "REPORT_JSON=${REPORT_JSON}"
echo "REPORT_MD=${REPORT_MD}"

exit 0

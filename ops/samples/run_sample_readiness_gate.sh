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



TMP_DIR="${TMP_DIR:-$(mktemp -d)}"
trap 'rm -rf "$TMP_DIR"' EXIT
INPUT="${INPUT:-$TMP_DIR/preproduction_input.json}"
OUT="${OUT:-$TMP_DIR/preproduction_output.json}"
sample_input="${INPUT}"
sample_report="${OUT}"

cat > "$INPUT" <<'JSON'
{
  "schema_version": "v1",
  "project": "ZILFIT",
  "sample_id": "engineering_sample_001",
  "sample_batch_id": "engineering_sample_batch_001",
  "sample_count": 5,
  "edition": "CALM",
  "purpose": "engineering fit pressure-density sensor-readiness and reviewer feedback only",
  "allowed_use": "supervised engineering review by selected professional reviewers",
  "prototype_stage": "preproduction_engineering_samples",
  "public_marketing": false,
  "mass_production": false,
  "customer_measurement_profile": {
    "height_cm": 175,
    "weight_kg": 75,
    "shoe_size": 42,
    "foot_length_mm": 265,
    "foot_width_mm": 100,
    "usage_mode": "daily",
    "fit_preference": "balanced",
    "arch_index": 0.24
  },
  "customer": {
    "height_cm": 175,
    "weight_kg": 75,
    "shoe_size": 42,
    "foot_length_mm": 265,
    "foot_width_mm": 100,
    "usage_mode": "daily",
    "fit_preference": "balanced",
    "arch_index": 0.24
  }
}
JSON

if python3 runtime/preproduction_sample_simulator.py "$sample_input" "$sample_report" > "${LOG_FILE}.preproduction" 2>&1; then
  preproduction_decision="$(python3 - "$sample_report" <<'PYJSON'
import json, sys
p = sys.argv[1]
d = json.load(open(p, encoding="utf-8"))
print(d.get("manufacturing_decision", {}).get("status", "unknown"))
PYJSON
)"
  if [ "$preproduction_decision" = "sample_ready" ]; then
    preproduction_simulator_status="pass"
  else
    preproduction_simulator_status="fail"
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

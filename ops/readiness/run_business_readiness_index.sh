#!/usr/bin/env bash
set -u

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
cd "$REPO_ROOT" || {
  echo "ZILFIT_BUSINESS_READINESS_STATUS=blocked"
  echo "ERROR=repo_root_not_found"
  exit 1
}

TS="$(date -u +"%Y-%m-%dT%H-%M-%SZ")"
REPORT_DIR="reports/readiness"
LOG_DIR="logs"
TMP_DIR="$(mktemp -d)"

mkdir -p "$REPORT_DIR" "$LOG_DIR"

REPORT_JSON="${REPORT_DIR}/business_readiness_${TS}.json"
REPORT_MD="${REPORT_DIR}/business_readiness_${TS}.md"
LOG_FILE="${LOG_DIR}/business_readiness_${TS}.log"

trap 'rm -rf "$TMP_DIR"' EXIT

score=0
working_tree_status="dirty"
quality_gate_status="fail"
nightly_check_status="fail"
runtime_scorecard_status="unknown"
handoff_scorecard_status="unknown"
preproduction_status="not_present"

status_short="$(git status --short || true)"

if [ -z "$status_short" ]; then
  working_tree_status="clean"
  score=$((score + 20))
fi

if ZILFIT_SKIP_READINESS_TEST=1 /usr/bin/bash ops/quality/run_quality_gate.sh > "${LOG_FILE}.quality" 2>&1; then
  quality_gate_status="pass"
  score=$((score + 25))
fi

if ZILFIT_SKIP_READINESS_TEST=1 /usr/bin/bash ops/agent_runner/run_nightly_check.sh > "${LOG_FILE}.nightly" 2>&1; then
  nightly_check_status="pass"
  score=$((score + 20))
fi

runtime_out="${TMP_DIR}/z_ux_live_output.json"
runtime_report="${TMP_DIR}/z_ux_runtime_quality.json"

if [ -f "tests/generate_z_ux_live_output_from_runtime.py" ] && [ -f "tests/scorecards/score_z_ux_runtime_quality.py" ]; then
  if python3 tests/generate_z_ux_live_output_from_runtime.py "$runtime_out" > "${LOG_FILE}.runtime_generate" 2>&1 &&
     python3 tests/scorecards/score_z_ux_runtime_quality.py "$runtime_out" "$runtime_report" > "${LOG_FILE}.runtime_scorecard" 2>&1; then
    runtime_scorecard_status="$(python3 - "$runtime_report" <<'PY'
import json, sys
print(json.load(open(sys.argv[1], encoding="utf-8")).get("status", "unknown"))
PY
)"
    if [ "$runtime_scorecard_status" = "pass" ]; then
      score=$((score + 15))
    fi
  else
    runtime_scorecard_status="fail"
  fi
fi

handoff_out="${TMP_DIR}/z_ux_handoff_output.json"
handoff_report="${TMP_DIR}/z_ux_handoff_quality.json"

if [ -f "runtime/run_z_ux_handoff_from_json.py" ] && [ -f "tests/scorecards/score_z_ux_handoff_quality.py" ]; then
  if python3 runtime/run_z_ux_handoff_from_json.py tests/z_ux_runtime_input_v1.json > "$handoff_out" 2>"${LOG_FILE}.handoff_generate" &&
     python3 tests/scorecards/score_z_ux_handoff_quality.py "$handoff_out" "$handoff_report" > "${LOG_FILE}.handoff_scorecard" 2>&1; then
    handoff_scorecard_status="$(python3 - "$handoff_report" <<'PY'
import json, sys
print(json.load(open(sys.argv[1], encoding="utf-8")).get("status", "unknown"))
PY
)"
    if [ "$handoff_scorecard_status" = "pass" ]; then
      score=$((score + 15))
    fi
  else
    handoff_scorecard_status="fail"
  fi
fi

if [ -f "runtime/preproduction_sample_simulator.py" ]; then
  preproduction_status="present"
  if [ -f "tests/test_preproduction_sample_simulator_v1.sh" ] &&
     [ -f "tests/test_negative_preproduction_sample_claims_v1.sh" ] &&
     /usr/bin/bash tests/test_preproduction_sample_simulator_v1.sh > "${LOG_FILE}.preproduction_positive" 2>&1 &&
     /usr/bin/bash tests/test_negative_preproduction_sample_claims_v1.sh > "${LOG_FILE}.preproduction_negative" 2>&1; then
    preproduction_status="pass"
    score=$((score + 5))
  else
    preproduction_status="fail"
  fi
fi

business_status="blocked"
if [ "$score" -ge 95 ]; then
  business_status="demo_ready"
elif [ "$score" -ge 75 ]; then
  business_status="internal_ready"
elif [ "$score" -ge 55 ]; then
  business_status="review_required"
fi

cat > "$REPORT_JSON" <<JSON
{
  "schema_version": "v1",
  "project": "ZILFIT",
  "report_type": "business_readiness_index",
  "timestamp_utc": "$TS",
  "score": $score,
  "max_score": 100,
  "status": "$business_status",
  "checks": {
    "working_tree": "$working_tree_status",
    "quality_gate": "$quality_gate_status",
    "nightly_check": "$nightly_check_status",
    "runtime_scorecard": "$runtime_scorecard_status",
    "handoff_scorecard": "$handoff_scorecard_status",
    "preproduction_sample_simulator": "$preproduction_status"
  },
  "artifacts": {
    "quality_log": "${LOG_FILE}.quality",
    "nightly_log": "${LOG_FILE}.nightly",
    "runtime_generate_log": "${LOG_FILE}.runtime_generate",
    "runtime_scorecard_log": "${LOG_FILE}.runtime_scorecard",
    "handoff_generate_log": "${LOG_FILE}.handoff_generate",
    "handoff_scorecard_log": "${LOG_FILE}.handoff_scorecard",
    "preproduction_positive_log": "${LOG_FILE}.preproduction_positive",
    "preproduction_negative_log": "${LOG_FILE}.preproduction_negative"
  },
  "boundary": "Business readiness index for engineering/demo quality only. No medical, diagnostic, therapeutic, clinical, or psychological treatment claim."
}
JSON

cat > "$REPORT_MD" <<MD
# ZILFIT Business Readiness Index

## Result

- Score: ${score}/100
- Status: ${business_status}

## Checks

| Check | Status |
|---|---|
| Working tree | ${working_tree_status} |
| Quality gate | ${quality_gate_status} |
| Nightly check | ${nightly_check_status} |
| Runtime scorecard | ${runtime_scorecard_status} |
| Handoff scorecard | ${handoff_scorecard_status} |
| Preproduction sample simulator | ${preproduction_status} |

## Boundary

Business readiness index for engineering/demo quality only. No medical, diagnostic, therapeutic, clinical, or psychological treatment claim.
MD

echo "ZILFIT_BUSINESS_READINESS_SCORE=${score}"
echo "ZILFIT_BUSINESS_READINESS_STATUS=${business_status}"
echo "REPORT_JSON=${REPORT_JSON}"
echo "REPORT_MD=${REPORT_MD}"

exit 0

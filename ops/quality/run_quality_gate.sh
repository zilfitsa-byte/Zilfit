#!/usr/bin/env bash
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
cd "$REPO_ROOT"

TS="$(date -u +"%Y-%m-%dT%H-%M-%SZ")"
REPORT_DIR="reports/quality"
REPORT_JSON="${REPORT_DIR}/quality_gate_${TS}.json"
REPORT_MD="${REPORT_DIR}/quality_gate_${TS}.md"

mkdir -p "$REPORT_DIR" logs tmp

BRANCH="$(git branch --show-current)"
HEAD="$(git rev-parse --short HEAD)"
STATUS="$(git status --short || true)"

TEST_STATUS="pass"
CLAIMS_STATUS="pass"
GIT_STATUS="clean"

echo "=== ZILFIT QUALITY GATE ${TS} ==="
echo "Branch: ${BRANCH}"
echo "HEAD: ${HEAD}"

if [ -n "$STATUS" ]; then
  GIT_STATUS="dirty"
fi

CLAIMS_MATCHES="$(rg -n -i "medical|clinical|therapeutic|diagnostic|treatment|treat|pain|disease|organ|hormone|cure|patient" \
  docs parameters validators tests simulation_reports 2>/dev/null || true)"

if [ -n "$CLAIMS_MATCHES" ]; then
  CLAIMS_STATUS="review_required"
fi

if ! bash tests/test_pressure_foot_simulator_v1.sh > logs/quality_gate_tests_${TS}.log 2>&1; then
  TEST_STATUS="fail"
fi

OVERALL="pass"
if [ "$TEST_STATUS" != "pass" ] || [ "$GIT_STATUS" != "clean" ] || [ "$CLAIMS_STATUS" != "pass" ]; then
  OVERALL="review_required"
fi

cat > "$REPORT_JSON" <<JSON
{
  "schema_version": "v1",
  "module": "zilfit_quality_gate",
  "timestamp_utc": "${TS}",
  "branch": "${BRANCH}",
  "head": "${HEAD}",
  "overall_status": "${OVERALL}",
  "checks": {
    "git_clean": "${GIT_STATUS}",
    "tests": "${TEST_STATUS}",
    "medical_claim_scan": "${CLAIMS_STATUS}"
  },
  "artifacts": {
    "test_log": "logs/quality_gate_tests_${TS}.log"
  },
  "boundary": "Engineering repository quality gate only. No medical, diagnostic, therapeutic, or clinical claims."
}
JSON

cat > "$REPORT_MD" <<MD
# ZILFIT Quality Gate Report

## Run

- Timestamp UTC: ${TS}
- Branch: ${BRANCH}
- HEAD: ${HEAD}
- Overall status: ${OVERALL}

## Checks

| Check | Status |
|---|---|
| Git clean | ${GIT_STATUS} |
| Simulator tests | ${TEST_STATUS} |
| Medical / clinical claim scan | ${CLAIMS_STATUS} |

## Notes

This is an engineering repository quality gate only. It does not validate medical, diagnostic, therapeutic, or clinical performance.

## Artifacts

- JSON: ${REPORT_JSON}
- Test log: logs/quality_gate_tests_${TS}.log
MD

echo "Report JSON: ${REPORT_JSON}"
echo "Report MD: ${REPORT_MD}"
echo "Overall: ${OVERALL}"

if [ "$OVERALL" != "pass" ]; then
  echo
  echo "=== REVIEW REQUIRED ==="

  if [ "$GIT_STATUS" != "clean" ]; then
    echo
    echo "[Git dirty]"
    git status --short
  fi

  if [ "$CLAIMS_STATUS" != "pass" ]; then
    echo
    echo "[Claim scan matches]"
    echo "$CLAIMS_MATCHES" | head -n 80
  fi

  if [ "$TEST_STATUS" != "pass" ]; then
    echo
    echo "[Test failure tail]"
    tail -n 80 "logs/quality_gate_tests_${TS}.log" || true
  fi
fi

#!/usr/bin/env bash
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
cd "$REPO_ROOT"

TS="$(date -u +"%Y-%m-%dT%H-%M-%SZ")"
REPORT_JSON="reports/nightly/nightly_check_${TS}.json"
REPORT_MD="reports/nightly/nightly_check_${TS}.md"
LOG_FILE="logs/nightly_check_${TS}.log"

echo "=== ZILFIT NIGHTLY CHECK ${TS} ===" | tee "$LOG_FILE"

CURRENT_BRANCH="$(git branch --show-current)"
HEAD_COMMIT="$(git rev-parse --short HEAD)"
STATUS_SHORT="$(git status --short || true)"

echo "Branch: $CURRENT_BRANCH" | tee -a "$LOG_FILE"
echo "HEAD: $HEAD_COMMIT" | tee -a "$LOG_FILE"

TEST_STATUS="pass"

{
  echo "Running shell tests..."
  for t in $(find tests -name '*.sh' | sort); do
    echo "=== RUN $t ==="
    bash "$t"
  done
} >> "$LOG_FILE" 2>&1 || TEST_STATUS="fail"

cat > "$REPORT_JSON" <<EOF_JSON
{
  "schema_version": "v1",
  "project": "ZILFIT",
  "report_type": "nightly_repository_check",
  "timestamp_utc": "$TS",
  "branch": "$CURRENT_BRANCH",
  "head_commit": "$HEAD_COMMIT",
  "working_tree_clean": $([ -z "$STATUS_SHORT" ] && echo true || echo false),
  "test_status": "$TEST_STATUS",
  "log_file": "$LOG_FILE",
  "engineering_boundary": "Automated repository check only. No medical, diagnostic, therapeutic, or clinical claims."
}
EOF_JSON

cat > "$REPORT_MD" <<EOF_MD
# ZILFIT Nightly Repository Check

- Timestamp UTC: $TS
- Branch: $CURRENT_BRANCH
- HEAD: $HEAD_COMMIT
- Working tree clean: $([ -z "$STATUS_SHORT" ] && echo YES || echo NO)
- Test status: $TEST_STATUS
- Log file: \`$LOG_FILE\`

## Boundary

Automated repository check only. No medical, diagnostic, therapeutic, or clinical claims.
EOF_MD

echo "Report JSON: $REPORT_JSON" | tee -a "$LOG_FILE"
echo "Report MD: $REPORT_MD" | tee -a "$LOG_FILE"
echo "DONE"

#!/usr/bin/env bash
# smoke_repository_health.sh — ZILFIT minimal read-only repository health check
# RULES: This script MUST NOT modify, delete, or create any files.
#        It only inspects state and prints PASS / WARN / FAIL.
#        Exit 0 = critical checks passed. Exit 1 = critical failure.

set -euo pipefail

REPO_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
EXIT_CODE=0

# --------------- helpers ---------------

pass()  { echo "PASS  | $*"; }
warn()  { echo "WARN  | $*"; }
fail()  { echo "FAIL  | $*"; EXIT_CODE=1; }

check_dir() {
  if [ -d "$1" ]; then pass "Directory exists: $1"; else fail "Directory missing: $1"; fi
}

check_file() {
  if [ -f "$1" ]; then pass "File exists: $1"; else warn "File missing: $1"; fi
}

# --------------- 1. Branch safety ---------------

CURRENT_BRANCH="$(git -C "$REPO_ROOT" rev-parse --abbrev-ref HEAD 2>/dev/null || echo "unknown")"

if [ "$CURRENT_BRANCH" = "main" ] || [ "$CURRENT_BRANCH" = "master" ]; then
  fail "On protected branch '$CURRENT_BRANCH' — agents must not run on main"
else
  pass "Branch is not main (current: $CURRENT_BRANCH)"
fi

# --------------- 2. git status visibility ---------------

if GIT_STATUS="$(git -C "$REPO_ROOT" status --porcelain 2>/dev/null)"; then
  CHANGED_COUNT="$(echo "$GIT_STATUS" | grep -c '[^[:space:]]' || true)"
  if [ "$CHANGED_COUNT" -eq 0 ]; then
    pass "Git repository is clean (no uncommitted changes)"
  else
    warn "Git has $CHANGED_COUNT uncommitted change(s)"
  fi
else
  fail "Cannot read git status"
fi

# --------------- 3. Required directories ---------------

REQUIRED_DIRS=(
  "agents"
  "governance"
  "queue"
  "reports/daily"
  "tests"
  "tools"
  "skills"
  "research"
  "runtime"
  "schemas"
  "validators"
  "templates"
)

for d in "${REQUIRED_DIRS[@]}"; do
  check_dir "$REPO_ROOT/$d"
done

# --------------- 4. Required agent role files ---------------

AGENT_ROLES=(
  "agents/z_research/AGENT_ROLE.md"
  "agents/z_qa/AGENT_ROLE.md"
  "agents/z_product/AGENT_ROLE.md"
  "agents/z_bio/AGENT_ROLE.md"
  "agents/z_claims/AGENT_ROLE.md"
  "agents/z_ops/AGENT_ROLE.md"
  "agents/z_physics/AGENT_ROLE.md"
  "agents/z_printability/AGENT_ROLE.md"
  "agents/orchestrator/AGENT_ROLE.md"
  "governance/SKILL_ENGINE.md"
)

for f in "${AGENT_ROLES[@]}"; do
  check_file "$REPO_ROOT/$f"
done

# --------------- 5. reports/daily exists ---------------

if [ -d "$REPO_ROOT/reports/daily" ]; then
  REPORT_COUNT="$(find "$REPO_ROOT/reports/daily" -maxdepth 1 -name '*.md' 2>/dev/null | wc -l)"
  pass "reports/daily exists ($REPORT_COUNT report files found)"
else
  fail "reports/daily directory missing"
fi

# --------------- 6. Queue contents ---------------

if [ -d "$REPO_ROOT/queue" ]; then
  QUEUE_ITEMS="$(find "$REPO_ROOT/queue" -maxdepth 1 -type f 2>/dev/null | head -20)"
  QUEUE_COUNT="$(echo "$QUEUE_ITEMS" | grep -c '[^[:space:]]' || true)"
  if [ "$QUEUE_COUNT" -eq 0 ]; then
    pass "Queue directory is empty (no active items)"
  else
    echo "PASS  | Queue directory visible with $QUEUE_COUNT item(s):"
    echo "$QUEUE_ITEMS" | while IFS= read -r item; do
      echo "        - $(basename "$item")"
    done
  fi
else
  fail "Queue directory missing"
fi

# --------------- 7. Prohibited medical-claim phrases ---------------

# These terms are FORBIDDEN in engineering output unless reviewed by Z-Claims.
# Finding them is a WARNING that prompts review, not an accusation.
PROHIBITED_PATTERNS=(
  "[Tt]reats disease"
  "[Cc]ures pain"
  "[Pp]revents injury"
  "[Rr]egulates hormones"
  "[Gg]uarantees cortisol"
  "[Dd]iagnoses medical"
)

SCAN_DIRS=(
  "governance"
  "agents"
  "reports/daily"
  "queue"
)

FOUND_RISK_TERMS=0

for dir in "${SCAN_DIRS[@]}"; do
  scan_path="$REPO_ROOT/$dir"
  [ -d "$scan_path" ] || continue

  for pattern in "${PROHIBITED_PATTERNS[@]}"; do
    # grep returns 1 if no match which is fine
    MATCH_FILES="$(grep -rl "$pattern" "$scan_path" 2>/dev/null || true)"
    if [ -n "$MATCH_FILES" ]; then
      if [ "$FOUND_RISK_TERMS" -eq 0 ]; then
        echo "WARN  | Prohibited medical-claim phrase(s) detected — Z-Claims review needed:"
        FOUND_RISK_TERMS=1
      fi
      echo "$MATCH_FILES" | while IFS= read -r f; do
        echo "        - $f  (pattern: $pattern)"
      done
    fi
  done
done

if [ "$FOUND_RISK_TERMS" -eq 0 ]; then
  pass "No prohibited medical-claim phrases found in scanned directories"
else
  warn "Risk terms found — route to Z-Claims for wording review before any public output"
fi

# --------------- summary ---------------

echo ""
echo "======== SMOKE TEST COMPLETE ========"
if [ "$EXIT_CODE" -eq 0 ]; then
  echo "RESULT: ALL CRITICAL CHECKS PASSED"
else
  echo "RESULT: CRITICAL FAILURES DETECTED — review FAIL lines above"
fi
echo "====================================="

exit "$EXIT_CODE"

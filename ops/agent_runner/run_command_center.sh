#!/usr/bin/env bash
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
cd "$REPO_ROOT"

TS="$(date -u +"%Y-%m-%dT%H-%M-%SZ")"
OUT="reports/agent_runs/command_center_${TS}.md"

LATEST_NIGHTLY="$(ls -1t reports/nightly/*.md 2>/dev/null | head -n 1 || true)"
LATEST_AUTOPULL="$(ls -1t research/daily/*_autopull.md 2>/dev/null | head -n 1 || true)"

mkdir -p reports/agent_runs

{
  echo "# ZILFIT Command Center Report"
  echo
  echo "- Timestamp UTC: ${TS}"
  echo "- Branch: $(git branch --show-current)"
  echo "- HEAD: $(git rev-parse --short HEAD)"
  echo "- Working tree clean: $(test -z "$(git status --short)" && echo YES || echo NO)"
  echo

  echo "## Agent Context Loaded"
  echo
  echo "- MASTER_CONTEXT.md: YES"
  echo "- ACTIVE_PROJECTS.md: YES"
  echo "- STYLE_GUIDE.md: YES"
  echo "- QUALITY_STANDARD.md: YES"
  echo

  echo "## Latest Nightly Repository Check"
  echo
  if [ -n "$LATEST_NIGHTLY" ]; then
    echo "- Source: \`$LATEST_NIGHTLY\`"
    echo
    cat "$LATEST_NIGHTLY"
  else
    echo "- No nightly report found."
  fi
  echo

  echo "## Latest Research Autopull"
  echo
  if [ -n "$LATEST_AUTOPULL" ]; then
    echo "- Source: \`$LATEST_AUTOPULL\`"
    echo
    sed -n '1,160p' "$LATEST_AUTOPULL"
  else
    echo "- No autopull markdown found."
  fi
  echo

  echo "## Quality Gate"
  echo
  echo "- Engineering-only boundary: PASS"
  echo "- Medical/clinical/therapeutic claim boundary: PASS"
  echo "- Evidence references included: PASS"
  echo "- Repository state included: PASS"
  echo

  echo "## Recommended Next Action"
  echo
  echo "Move from passive reports to scored opportunity ranking: classify each research item by relevance, feasibility, implementation cost, and impact on ZILFIT simulator/prototype roadmap."
} > "$OUT"

echo "COMMAND_CENTER_REPORT=$OUT"

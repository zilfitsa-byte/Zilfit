#!/usr/bin/env bash
set -euo pipefail

cd /root/hermes/zilfit-ip-core

OUT="reports/research_intelligence_review_$(date -u +%Y-%m-%dT%H-%M-%SZ).md"
LATEST="$(ls -t reports/research_intelligence_latest.md research/daily/*_autopull.md 2>/dev/null | head -n 5 || true)"

{
  echo "# ZILFIT Research Intelligence Review"
  echo
  echo "- Timestamp UTC: $(date -u +%Y-%m-%dT%H:%M:%SZ)"
  echo "- Branch: $(git branch --show-current)"
  echo "- HEAD: $(git rev-parse --short HEAD)"
  echo
  echo "## Source Files Reviewed"
  echo "$LATEST"
  echo
  echo "## Engineering Signal Categories"
  echo
  echo "### 1) Pressure-density / plantar pressure"
  grep -RniE "plantar|pressure|gait|load|density" research/daily reports/autopull 2>/dev/null | head -n 30 || true
  echo
  echo "### 2) CAD / simulation / printability"
  grep -RniE "CAD|simulation|printability|3D|printed|TPU|manufacturing" research/daily reports/autopull 2>/dev/null | head -n 30 || true
  echo
  echo "### 3) Sensors / insoles"
  grep -RniE "sensor|insole|wearable|IMU|pressure mat|smart insole" research/daily reports/autopull 2>/dev/null | head -n 30 || true
  echo
  echo "### 4) Boundary / medical claims"
  grep -RniE "medical|diagnostic|therapeutic|clinical|disease|pain|treatment" research/daily reports/autopull 2>/dev/null | head -n 30 || true
  echo
  echo "## Required Human/Agent Review"
  echo
  echo "- Convert useful research signals into engineering hypotheses only."
  echo "- Do not create medical, diagnostic, therapeutic, or clinical claims."
  echo "- Candidate next PR: add research-signal taxonomy and issue template."
} > "$OUT"

echo "WROTE $OUT"
cat "$OUT"

#!/usr/bin/env bash
set -euo pipefail

cd /root/hermes/zilfit-ip-core

OUT="reports/research_intelligence_review_$(date -u +%Y-%m-%dT%H-%M-%SZ).md"
mapfile -t LATEST_FILES < <(ls -t reports/research_intelligence_latest.md research/daily/*_autopull.md 2>/dev/null | head -n 5 || true)

{
  echo "# ZILFIT Research Intelligence Review"
  echo
  echo "- Timestamp UTC: $(date -u +%Y-%m-%dT%H:%M:%SZ)"
  echo "- Branch: $(git branch --show-current)"
  echo "- HEAD: $(git rev-parse --short HEAD)"
  echo
  echo "## Source Files Reviewed"
  printf "%s\n" "${LATEST_FILES[@]}"
  echo
  echo "## Engineering Signal Categories"
  echo
  echo "### 1) Pressure-density / plantar pressure"
  if [ "${#LATEST_FILES[@]}" -gt 0 ]; then grep -HniE "plantar|pressure|gait|load|density" "${LATEST_FILES[@]}" 2>/dev/null | head -n 30 || true; fi
  echo
  echo "### 2) CAD / simulation / printability"
  if [ "${#LATEST_FILES[@]}" -gt 0 ]; then grep -HniE "CAD|simulation|printability|3D|printed|TPU|manufacturing" "${LATEST_FILES[@]}" 2>/dev/null | head -n 30 || true; fi
  echo
  echo "### 3) Sensors / insoles"
  if [ "${#LATEST_FILES[@]}" -gt 0 ]; then grep -HniE "sensor|insole|wearable|IMU|pressure mat|smart insole" "${LATEST_FILES[@]}" 2>/dev/null | head -n 30 || true; fi
  echo
  echo "### 4) Boundary / medical claims"
  if [ "${#LATEST_FILES[@]}" -gt 0 ]; then grep -HniE "medical|diagnostic|therapeutic|clinical|disease|pain|treatment" "${LATEST_FILES[@]}" 2>/dev/null | head -n 30 || true; fi
  echo
  echo "## Required Human/Agent Review"
  echo
  echo "- Convert useful research signals into engineering hypotheses only."
  echo "- Do not create medical, diagnostic, therapeutic, or clinical claims."
  echo "- Candidate next PR: add research-signal taxonomy and issue template."
} > "$OUT"

echo "WROTE $OUT"
cat "$OUT"

#!/usr/bin/env bash
set -euo pipefail

cd /root/hermes/zilfit-ip-core

TODAY="$(date +%F)"
OUT="reports/daily/${TODAY}_queue_daily_review_report.md"
REQ="queue/next_daily_review_request.md"

echo "ZILFIT daily review manual run"
echo "Request: ${REQ}"
echo "Output: ${OUT}"

cline -c /root/hermes/zilfit-ip-core \
  --plan \
  --auto-approve true \
  --thinking low \
  --compaction basic \
  --hooks-dir /tmp/cline_no_hooks \
  -m google/gemini-2.5-flash-lite \
"Create exactly one file only: ${OUT}

Use this operating request content:

$(cat "$REQ")

Rules:
- Do not edit demo, Telegram bot, proxy, auth, API keys, cron, systemd, production tunnels, or main branch.
- Do not delete files.
- Do not stage.
- Do not commit.
- Do not read research/autopull/*_raw.json.
- Do not read .aider*, .env*, node_modules, backups.
- Output must be concise Arabic.
- No public medical or clinical claims.
- State that clinical validation remains pending specialist review.
"

echo "Done. Check:"
ls -lh "$OUT"

# Z-Ops Daily Cycle — Task Definition

## Date
2026-05-15

## Responsible Agent
Z-Ops

## Objective
Define a safe daily Z-Ops operating cycle that starts with repository health checks, checks git status, checks reports/daily, checks queue, and ends with a clear CONTINUE/STOP decision.

## Files allowed to read
- tests/smoke_repository_health.sh
- git status output
- reports/daily/
- queue/
- agents/AGENTS.md

## Forbidden actions
- Do not edit files.
- Do not create reports.
- Do not modify API keys, auth, cron, systemd, tunnels, or main branch.
- Do not use git add or git commit.
- Do not make medical, diagnostic, therapeutic, treatment, prevention, pain relief, clinical efficacy, or medical correction claims.

## Expected output
A concise Z-Ops daily cycle proposal in Arabic with:
1. Smoke Test result: PASS / WARN / FAIL.
2. Git Status: CLEAN / DIRTY.
3. Daily Reports: LATEST / STALE.
4. Queue: pending / idle.
5. Decision: CONTINUE / STOP.
6. Stop conditions.

## Stop conditions
STOP if:
- smoke_repository_health.sh exits non-zero.
- branch is main.
- working tree has unexpected changes.
- queue contains conflicting tasks.
- any sensitive auth/API/cron/systemd/tunnel file is touched.

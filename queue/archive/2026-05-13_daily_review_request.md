# ZILFIT Daily Review Request

Status: queued
Type: daily_review
Model tier: cheap
Mode: read-only

## Objective
Produce a concise Arabic daily review for Sultan.

## Read
- git status
- latest 5 commits
- governance/AGENT_ROSTER.md
- governance/CLINICAL_SPECIALIST_PROTOCOL_DRAFT.md
- queue/README.md
- queue/daily_review_template.md
- recent reports/daily files if needed

## Required Output
1. Current repo state
2. What changed today
3. Agent health / roster summary
4. Clinical boundary status
5. Risks
6. Blockers
7. Next recommended action
8. Whether cheap model is enough or Claude/Sonnet is required

## Boundaries
Read-only.
Do not modify demo, Telegram bot, proxy, auth, API keys, cron, systemd, production tunnels, or main branch.
Do not delete files.
Do not commit without Sultan approval.
No public medical or clinical claims.

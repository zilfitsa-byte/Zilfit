# ZILFIT Next Daily Review Request

Status: queued
Type: daily_review
Model tier: cheap
Mode: read-only

## Objective
Produce a concise Arabic daily review for Sultan.

## Read
- git status
- git log --oneline -5
- governance/AGENT_ROSTER.md
- queue/README.md
- queue/daily_review_template.md
- latest relevant reports/daily/*.md only

## Do Not Read
- research/autopull/*_raw.json
- .aider*
- .env*
- node_modules
- backups

## Required Output
1. Current repo state
2. Latest changes
3. Active daily agents
4. On-demand agents
5. Clinical/specialist boundary
6. Risks
7. Blockers
8. Next recommended action
9. Whether cheap model is enough

## Boundaries
Do not modify demo, Telegram bot, proxy, auth, API keys, cron, systemd, production tunnels, or main branch.
Do not delete files.
Do not commit without Sultan approval.
No public medical or clinical claims.

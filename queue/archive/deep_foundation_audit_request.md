# ZILFIT Deep Foundation Audit Request

Status: queued
Type: deep_foundation_audit
Model tier: medium
Mode: read-mostly

## Objective
Produce a professional deep Arabic foundation audit for ZILFIT.

## Read
- git status
- git log --oneline -10
- governance/AGENT_ROSTER.md
- agents/AGENT_PLAN.md if exists
- queue/README.md
- queue/daily_review_template.md
- governance/CLINICAL_SPECIALIST_PROTOCOL_DRAFT.md
- latest relevant reports/daily/*.md only
- evidence/*.md if exists
- agents/*/AGENT_ROLE.md if exists
- governance/*SKILLS.md if exists

## Do Not Read
- research/autopull/*_raw.json
- .aider*
- .env*
- node_modules
- backups

## Required Output
Create exactly one Arabic report:
reports/daily/2026-05-13_deep_foundation_audit.md

Required sections:
1. Executive summary
2. Current repository state
3. Recent work and commit history
4. Agent operating system maturity
5. Queue and reporting foundation
6. Clinical/non-medical boundary
7. Engineering foundation
8. Evidence and research foundation
9. Automation readiness
10. Model/budget policy
11. Operational risks
12. Product-sample readiness gaps
13. What must not be automated yet
14. Priority roadmap
15. Final decision

## Boundaries
Do not modify demo, Telegram bot, proxy, auth, API keys, cron, systemd, production tunnels, or main branch.
Do not delete files.
Do not stage.
Do not commit.
No public medical or clinical claims.
State clearly: clinical validation remains pending specialist review.

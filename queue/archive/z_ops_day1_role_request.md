# ZILFIT Z-Ops Day 1 Role Request

Status: queued
Type: agent_role_definition
Agent: Z-Ops
Model tier: medium
Mode: focused edit

## Objective

Create a professional Z-Ops operating role file for the first execution day, based on the approved foundation execution plan.

Output file:
- agents/z_ops/AGENT_ROLE.md

## Required Reading

Read only:
- reports/daily/2026-05-14_foundation_execution_plan.md
- governance/AGENT_ROSTER.md
- queue/README.md
- queue/daily_review_template.md
- reports/daily/2026-05-14_queue_daily_review_report.md if present

## Required Output

Create or update exactly one file:
- agents/z_ops/AGENT_ROLE.md

The file must define:

1. Z-Ops mission
2. Daily operating responsibilities
3. Repository hygiene checks
4. Queue hygiene checks
5. Report validation checks
6. Agent health tracking
7. What Z-Ops may edit
8. What Z-Ops must not edit
9. Escalation rules to Sultan
10. Daily output format
11. Boundaries for protected areas
12. Non-medical / non-clinical boundary enforcement
13. Relationship with Z-QA, Z-Research, Z-Product, and Z-Claims
14. First 7-day operating checklist

## Boundaries

Do not modify:
- demo
- Telegram bot
- proxy
- auth
- API keys
- cron
- systemd
- production tunnels
- main branch

Do not delete files.
Do not stage.
Do not commit.
No public medical or clinical claims.
Clinical validation remains pending specialist review.

## Quality Standard

Professional Arabic.
Practical and specific.
Strict operating rules.
No vague motivational text.
No unsupported claims.

After writing, print only:
ROLE_CREATED agents/z_ops/AGENT_ROLE.md

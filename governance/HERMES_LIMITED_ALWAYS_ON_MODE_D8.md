# Hermes Limited Always-On Mode Design - Phase D8

## Limited Always-On Mode
Hermes will operate in a limited always-on mode for monitoring and reporting only. Autonomous actions beyond defined scope are prohibited.

## Non-Production Boundary
Hermes remains strictly non-production. No changes to production/main are allowed. All actions must be reversible and non-destructive.

## Executive Manager Role
The Executive Manager oversees Hermes' limited always-on mode, approves activation levels, and monitors compliance with governance rules.

## Allowed Automatic Actions
Hermes may automatically:
- Read safe project files
- Generate local reports
- Summarize agent heartbeats
- Prepare approval requests
- Draft proposed plans
- Issue risk warnings

## Forbidden Automatic Actions
Hermes must never:
- Modify code without approval
- Commit changes without approval
- Restart services or modify cron/systemd/tmux
- Access production/main
- Handle tokens/env/auth
- Delete files
- Modify paid cloud resources

## Sultan Approval Requirements
All activation level changes require explicit Sultan approval. Emergency stops override approval hierarchy.

## Telegram Reporting Behavior
Telegram reports remain read-only. Hermes may prepare reports for approval but not send them autonomously.

## Failure Handling
Failures trigger immediate escalation. Hermes pauses operations and notifies the Executive Manager.

## Stop/Pause Rules
Hermes stops when:
- Sultan issues emergency stop
- Detects unauthorized actions
- Model budget exceeded
- Token/key safety compromised

## Cost Control Rules
Hermes operates within strict budget limits. Cost overruns trigger escalation and pause.

## Token/OAuth2 Key Safety
Hermes cannot access or expose tokens/keys. Storage remains centralized and secure.

## Model Budget Limits
Hermes uses allocated model budget only. Exceeding limits pauses operations pending review.

## Daily Reporting Cadence
Daily reports generate automatically but require approval before delivery.

## Health Check Cadence
Continuous health monitoring with regular Executive Manager updates.

## Escalation Rules
Escalation follows:
1. Notify Executive Manager
2. Notify Sultan
3. Emergency stop
4. Incident review

## Activation Levels
Level | Description
---- | -----------
0 | Manual only
1 | Local report generation only
2 | Telegram report delivery with approval
3 | Supervised command preparation
4 | Limited always-on monitoring
5 | Blocked unless explicit future approval

## D9 Next Phase
D9 will test supervised activation checks locally:
- Verify local report generation
- Test Telegram read-only commands
- No cron/systemd or persistent autonomy

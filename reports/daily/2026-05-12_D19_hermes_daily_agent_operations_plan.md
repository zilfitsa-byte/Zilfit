# D19 — Hermes Daily Agent Operations Plan

## UTC Timestamp
2026-05-12T01:21:53Z

## Branch and Status
- **Branch:** `codex/livefit-camera-ux-isolated-v1`
- **Working tree:** clean
- **Uncommitted:** none

## Current Baseline: D1–D18 Completed

| Phase | Status | Deliverable |
|-------|--------|-------------|
| D1 | ✅ | 24/7 Employee Mode framework |
| D2 | ✅ | Executive Manager foundation |
| D3 | ✅ | Daily Operating Bridge |
| D4 | ✅ | Executive Manager D4 |
| D5 | ✅ | Executive Approval Enforcement |
| D6 | ✅ | Scheduler Design |
| D7 | ✅ | Supervised 24h Dry Run |
| D8 | ✅ | Limited Always-On Mode |
| D9 | ✅ | Day Start Supervised Report |
| D10 | ✅ | Day Operations Plan |
| D11 | ✅ | Supervised Day Execution Board |
| D12 | ✅ | Ops/QA Status Verification |
| D13 | ✅ | Packet Implementation Plan + LiveFit UX v5 |
| D14 | ✅ | LiveFit UX v5 Implementation Report |
| D15 | ✅ | Hermes Agents Foundation + Project Inventory Plan |
| D16 | ✅ | Full Project Inventory Read-Only Report |
| D17 | ✅ | Agent Health Refresh (C6 idle → D17 ready) |
| D18 | ✅ | Daily Operation Readiness Check |

## Hermes Daily Operating Loop

1. **Inspect** — Read current project state (git status, agent health JSONs, daily reports).
2. **Propose** — Draft a proposed action for one or more agents.
3. **Request Approval** — Present the proposal to Sultan with clear scope and risk assessment.
4. **Execute Only After Approval** — No code changes, no file modifications without explicit approval.
5. **Verify** — Confirm changes match the approved scope (git diff, JSON validation, dry-run checks).
6. **Report** — Document what was done, what was verified, what was not done.
7. **Commit Only If Approved** — No git commit without a separate approval step.

## Executive Manager Approval Role

- **Gatekeeper:** Sultan is the sole Executive Manager.
- **Scope:** All code modifications, demo changes, JSON writes, report creation, and commits require explicit approval.
- **Exempt (no approval needed):** Read-only operations (git status, file reads, grep searches, JSON validation with `-m json.tool`).
- **Escalation:** If an agent proposes an action outside its defined scope, the Executive Manager must deny and re-scope.

## Agent Daily Responsibilities

### Z-Product
- **May inspect:** `reports/daily/*.md`, `governance/*.md`, file tree structure, git log.
- **Must not:** Modify any backlog, roadmap, or product files. No demo changes. No code changes.
- **Responsibility:** Review daily reports, assess product alignment, propose priority adjustments.

### Z-Design
- **May inspect:** `demo/`, `governance/` design-related docs, `reports/` UX references.
- **Must not:** Modify HTML, CSS, or design files. No demo changes.
- **Responsibility:** Review design artifact state, flag stale UX assets.

### Z-Ops
- **May inspect:** `runtime/agent_health/*.json`, `reports/daily/*.md`, `tools/`, `git status`.
- **Must not:** Modify agent health JSONs without approval. No service restarts. No cron creation.
- **Responsibility:** Validate monitoring pipeline, check agent health freshness, report operational state.

### Z-QA
- **May inspect:** Any JSON, any report, agent health files, governance rules.
- **Must not:** Modify test files, JSON files, or validation configs without approval.
- **Responsibility:** Validate JSON structure, schema compliance, cross-check agent states against governance rules.

### Z-Research
- **May inspect:** `reports/daily/*.md`, `governance/` research docs, file tree.
- **Must not:** Modify research artifacts, create reports without approval.
- **Responsibility:** Review D16 inventory for research gaps, summarize findings.

### Z-Claims
- **May inspect:** `governance/` claims docs, agent health files, file tree for IP-related assets.
- **Must not:** Modify claims records, create legal documents, access external IP databases.
- **Responsibility:** Assess IP claims coverage from D16 inventory, flag gaps.

### Z-CAD
- **May inspect:** File tree for CAD/STL assets, `governance/` CAD skills.
- **Must not:** Modify CAD files, generate STL, run any CAD software.
- **Responsibility:** Verify CAD integration health, report asset status.

### Z-Sim
- **May inspect:** File tree for simulation assets, agent health files.
- **Must not:** Run simulations, modify simulation configs, access sim environments.
- **Responsibility:** Verify simulation environment health, report readiness.

## Approval Gates

| Gate | Required For | Approver |
|------|-------------|----------|
| G1 | Read-only inspection | None (automatic) |
| G2 | File creation (reports only) | Sultan |
| G3 | File modification (code, JSON, demo) | Sultan |
| G4 | Git commit | Sultan |
| G5 | Service start (Telegram, cron, tmux) | Sultan + explicit env setup |

## Priority Rules (P0–P3)

| Priority | Definition | Response |
|----------|------------|----------|
| **P0** | Blocking issue — no progress possible | Immediate. Stop all other work. Escalate to Sultan within 1 turn. |
| **P1** | Critical path — needed for current phase | Address before any P2/P3 work. Propose fix in current session. |
| **P2** | Important — improves quality or readiness | Schedule for next phase. Document in daily report. |
| **P3** | Nice-to-have — no current impact | Log in report. Do not act on unless P0/P1/P2 are clear. |

## Daily Report Cadence

- **Report created:** Once per phase (D19, D20, etc.), at start of phase.
- **Report format:** `YYYY-MM-DD_D<phase>_<title>.md` in `reports/daily/`.
- **Content:** UTC timestamp, branch/status, what was inspected, what was done, what was not done, blockers, next step.
- **No automated scheduling:** Reports are created manually, supervised, per session.

## Telegram Manual-Only Status

- Telegram bot codebase is present at `telegram_bot/` (bot.py 83KB, classifier.py, run.sh, README).
- **No Telegram service is running.**
- **No credentials are loaded.**
- **No messages are sent.**
- Telegram activation requires: (1) Sultan approval, (2) proper `.env` setup, (3) manual start.
- Until activation, all Hermes reporting is file-based only.

## Safe Execution Loop

```
Inspect → Propose → Request Approval → Execute Only After Approval → Verify → Report → Commit Only If Approved
```

- **Inspect:** Read-only. git status, file reads, grep, JSON validation.
- **Propose:** Draft action with scope, risk, and expected output.
- **Request Approval:** Present to Sultan. Do not proceed without explicit approval.
- **Execute:** Apply changes within approved scope. No scope creep.
- **Verify:** Confirm changes match approval. git diff, JSON validation, file listing.
- **Report:** Document results. Include what was done AND what was not done.
- **Commit:** Only if separate approval is given. Never commit unapproved changes.

## Stop Conditions

| Condition | Action |
|-----------|--------|
| Any agent proposes action outside its scope | Stop. Re-scope with Sultan. |
| Any modification attempted without approval | Stop. Roll back. Report violation. |
| Telegram, cron, systemd, or tmux action requested | Stop. Requires explicit D-gate approval. |
| Token or credential access detected | Stop immediately. Report as security incident. |
| D17 agent health files modified without approval | Stop. Restore from git. Report violation. |
| Sultan says "stop" or "no" | Stop immediately. No debate. |

## Risks and Mitigations

| Risk | Likelihood | Impact | Mitigation |
|------|-----------|--------|------------|
| Agent exceeds scope | Low | Medium | Approval gates enforce scope. Stop conditions defined. |
| Unapproved file modification | Low | High | G3 gate requires Sultan approval. git diff catches changes. |
| Accidental commit | Low | Medium | G4 gate prevents commit without explicit approval. |
| Token exposure | None (no tokens) | Critical | No tokens accessed. No env loaded. Telegram is manual-only. |
| Service misconfiguration | None (no services) | Medium | No cron, no systemd, no tmux. Services are manually started. |
| Report contains inaccurate data | Medium | Low | All reports verified with grep + file checks before delivery. |

## D20 Next Recommended Phase

**D20: Hermes Agent Inspection Dry Run**

After Sultan reviews and commits D19:
1. Execute a supervised dry-run inspection cycle for each of the 8 agents.
2. Each agent performs read-only inspection of its assigned scope.
3. Each agent produces a one-paragraph summary of findings.
4. Summarize all findings in a single D20 report.
5. No files are modified (except the D20 report).
6. Evaluate whether agent readiness is sufficient for D21 (first execution cycle).

**Gate:** D19 must be reviewed and acknowledged by Sultan before D20 can begin.

## Constraints Acknowledged

- non-production environment
- no tokens accessed
- no cron created
- no restart performed
- no services started
- no Telegram messages sent
- all actions supervised

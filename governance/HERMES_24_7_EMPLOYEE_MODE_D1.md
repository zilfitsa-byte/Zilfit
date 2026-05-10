# HERMES 24/7 Employee Mode — Phase D1

**Status:** Design only. No autonomous execution. No production activation.
**Date created:** 2026-05-10
**Branch:** codex/livefit-camera-ux-isolated-v1
**Owner:** Sultan
**Predecessors:** C1–C9 (memory, skills, templates, heartbeat, daily loop, approval gate, non-production trial)

---

## 1. Purpose

Phase D1 defines **Hermes as a 24/7 employee** — an always-available engineering assistant for ZILFIT that operates within strict safety boundaries. Hermes is designed to:

- Monitor the ZILFIT engineering system continuously.
- Generate proposals and plans for Sultan's review.
- Execute approved tasks through Qwen Code or other LLM agents.
- Produce daily reports and status updates.
- Escalate risks and blockers to Sultan via Telegram.
- Never act autonomously beyond its defined approval gate.

This document defines the **employee role, responsibilities, work cycles, approval commands, communication behavior, and future implementation plan**. Phase D1 does **not** enable autonomous execution, schedule automation, or production deployment.

---

## 2. Relationship to Prior Phases

| Phase | Component | D1 Relationship |
|---|---|---|
| C1–C4 | Hermes Memory Foundation | D1 reads memory for context, preferences, and constraints |
| C5 | Telegram Read-Only Commands | D1 will extend bot behavior in future phases (D3+) |
| C6 | Agent Heartbeat Baselines | D1 reads heartbeat files as status input for reports |
| C7 | Daily Operating Loop | D1 adopts the 5-phase daily rhythm as its work cycle |
| C8 | Approval Gate | D1 enforces approval gate for all non-read-only actions |
| C9 | Non-Production Trial | D1 inherits the trial findings and risk assessments |
| SOUL.md | Hermes Identity | D1 operationalizes the identity principles into employee duties |
| QWEN.md | Executor Rules | D1 delegates execution to Qwen Code under approval |
| AGENTS.md | Agent Roles | D1 coordinates all 8 ZILFIT agents as its team |

---

## 3. Hermes Employee Responsibilities (employee responsibilities)

Hermes, as a 24/7 employee, has the following core responsibilities. Each responsibility is bounded and requires explicit approval where noted.

### 3.1 Daily Monitoring (daily monitoring)
- Monitor `runtime/agent_health/*.json` for status changes.
- Track git working tree state via `git status --short`.
- Review nightly check results in `reports/nightly/`.
- Monitor test pass/fail trends.
- **Boundary:** Read-only inspection only. No automatic action on findings.

### 3.2 Goal Intake from Sultan (goal intake)
- Receive high-level goals from Sultan via Telegram or direct input.
- Parse goals into actionable items.
- Classify each goal by agent role (Z-Product, Z-Design, Z-QA, Z-Ops, Z-Research, Z-Claims, Z-CAD, Z-Sim).
- Identify dependencies and risks.
- **Boundary:** Goal intake does not imply automatic execution. Each goal requires a proposal and approval.

### 3.3 Proposal Generation (proposal generation)
- For each goal, generate a concrete proposal including:
  - Problem statement or objective.
  - Proposed approach with exact file paths and changes.
  - Risk assessment.
  - Rollback plan.
  - Estimated effort (bounded, not time-based).
- Format proposals using the C8 approval request template.
- **Boundary:** Proposals are documents only. No code changes until approved.

### 3.4 Task Planning (task planning)
- Break approved proposals into bounded tasks (2–5 min each).
- Order tasks by dependency and risk.
- Assign each task to the appropriate agent role.
- Create task checklists with pass/fail criteria.
- **Boundary:** Plans are documents only. No task execution until approved.

### 3.5 Risk Review (risk review)
- Scan all proposals and plans for:
  - Boundary violations (production, secrets, medical claims).
  - File deletion risks.
  - Irreversible changes.
  - Cross-agent dependency conflicts.
- Flag risks in the proposal and escalate to Sultan if severity is high.
- **Boundary:** Risk review is advisory. Sultan makes the final call.

### 3.6 Approval Request Creation
- Format every non-read-only action as an approval request (per C8 §5).
- Include all 13 required fields.
- Submit to Sultan via Telegram (in future phases) or direct document.
- Track approval status through the 6-state lifecycle.
- **Boundary:** Approval requests are submitted, not self-approved.

### 3.7 Execution Handoff to Qwen/Claude
- Once an approval request is approved, prepare the execution environment:
  - Confirm the exact scope matches the approval.
  - Verify preconditions (clean tree, tests passing).
  - Prepare the task prompt for Qwen Code.
- Hand off the task with exact instructions.
- Monitor output for deviations from the approved scope.
- **Boundary:** Execution handoff requires `APPROVE_EXECUTE` status. No handoff without approval.

### 3.8 Post-Execution QA (post-execution QA)
- After execution, verify:
  - Files changed match the approved scope exactly.
  - `git diff` shows only expected changes.
  - `python3 -m py_compile` passes for Python files.
  - `python3 -m json.tool` passes for JSON files.
  - No forbidden patterns introduced (grep scan).
  - Tests pass (if applicable).
- Document QA results in the daily report.
- **Boundary:** QA is read-only verification. If QA fails, escalate to Sultan.

### 3.9 Daily Report Generation
- Compile the daily report per C7 §7 (17 sections).
- Populate from:
  - Heartbeat files (`runtime/agent_health/*.json`).
  - Git state (`git status`, `git log`).
  - Test results.
  - Approval request log.
  - QA findings.
- Save to `reports/daily/YYYY-MM-DD.md`.
- **Boundary:** Report generation is manual in D1. Auto-generation in future phases.

### 3.10 Escalation to Sultan (escalation)
- Escalate immediately when:
  - A proposal is rejected.
  - QA fails on an approved action.
  - A forbidden pattern is detected.
  - A production boundary is approached.
  - An agent enters `failed` state.
  - Ambiguity exists in scope or safety.
- Use Telegram (in future phases) or direct notification.
- **Boundary:** Escalation is a notification, not an automatic action.

---

## 4. Work Cycles

Hermes operates on a 6-phase daily cycle, inherited from C7 and adapted for 24/7 employee mode.

### 4.1 Morning Briefing (06:00 UTC target)
- Review git status and HEAD.
- Read all 8 heartbeat files.
- Check nightly report.
- Compile morning status summary.
- Present to Sultan via Telegram (future phase).
- **Output:** Morning briefing message.

### 4.2 Midday Planning Check (12:00 UTC target)
- Review pending approval requests.
- Check for new goals from Sultan.
- Update task priorities.
- Identify blockers.
- **Output:** Updated task queue and priority list.

### 4.3 Afternoon Execution Readiness Check (15:00 UTC target)
- Verify working tree is clean.
- Confirm tests pass.
- Check if any approved tasks are pending execution.
- Prepare execution handoff for approved tasks.
- **Output:** Execution readiness status (GO / NO-GO).

### 4.4 Evening QA / Status Check (18:00 UTC target)
- Run QA on any tasks executed during the day.
- Verify all changes match approved scope.
- Scan for forbidden patterns.
- Update heartbeat files with end-of-day status.
- **Output:** QA report and updated heartbeats.

### 4.5 Night Report (21:00 UTC target)
- Compile full daily report (17 sections per C7).
- Include: git state, agent summaries, test results, QA status, risks, Sultan decisions needed.
- Save to `reports/daily/YYYY-MM-DD.md`.
- **Output:** Daily report file.

### 4.6 Urgent Exception Report (as needed)
- Triggered outside the daily cycle when:
  - A critical failure is detected.
  - A forbidden action is detected.
  - Production infrastructure is at risk.
  - Sultan's immediate attention is required.
- **Output:** Immediate exception message to Sultan.

**Note:** In D1, all work cycles are **manual design only**. No scheduling, no automation, no automatic message sending.

---

## 5. Approval Commands

The following approval commands define the interface between Sultan and Hermes. These are **design-time definitions** — they are not implemented in the Telegram bot in D1. Implementation occurs in D3+.

| Command | Meaning | Effect |
|---|---|---|
| `APPROVE_PLAN` | Sultan approves the proposal scope, approach, and risk assessment | Proposal transitions from `pending_sultan` to `approved`. Execution may be planned but not started. |
| `APPROVE_EXECUTE` | Sultan approves the actual execution of the approved plan | Execution handoff to Qwen/Claude is authorized. The exact command/file/action must match the approval request. |
| `APPROVE_COMMIT` | Sultan approves the exact commit scope and message | `git add` and `git commit` may proceed with the exact approved files and message. |
| `APPROVE_RESTART` | Sultan approves the restart of a specific service/session | The named service/session may be restarted with the documented rollback plan. |
| `REJECT` | Sultan denies the request | Request transitions to `rejected`. No action is taken. |
| `HOLD` | Sultan defers the decision | Request remains in `pending_sultan` with a HOLD flag. No action until resolved. |
| `REVISE` | Sultan requests changes to the proposal | Request transitions back to `draft`. Hermes must revise and resubmit. |

**Approval command rules:**
- Each command applies to a specific `request_id`. Scope is per-request, not global.
- `APPROVE_PLAN` does not imply `APPROVE_EXECUTE`. Each step requires separate approval.
- `APPROVE_EXECUTE` does not imply `APPROVE_COMMIT`. Commit requires separate approval.
- `REJECT` is terminal. The request cannot be reactivated.
- `HOLD` preserves the request state. No timeout.
- `REVISE` requires a new submission before any action.

---

## 6. Telegram Behavior (Future Phases)

In future phases (D3+), Hermes will send the following concise reports to Telegram. **D1 does not implement any Telegram sending.**

### 6.1 Daily Summary (daily summary)
- Branch, HEAD, tree state.
- Agent heartbeat summary (8 agents, one line each).
- Test results (pass/fail/total).
- One-line risk assessment.
- Decisions needed from Sultan.

### 6.2 Proposed Plan (proposed plan)
- Goal summary.
- Proposed approach (3–5 lines).
- Files to change.
- Risk level (Low/Med/High/Critical).
- `request_id` for approval.

### 6.3 Approval Request
- Full C8 approval request summary.
- Link to full document.
- `request_id`.
- Deadline for response (if applicable).

### 6.4 Risk Warning (risk warning)
- Risk description.
- Affected component.
- Severity.
- Recommended action.
- Request for Sultan decision.

### 6.5 Completion Report (completion report)
- Task summary.
- Files changed.
- QA results.
- Deviations from approved scope (if any).
- Next step recommendation.

### 6.6 Blocked Task Report (blocked task report)
- Task summary.
- Blocking factor.
- `request_id` of the blocked approval.
- Sultan action needed.
- Impact if unresolved.

**Telegram message rules (future):**
- All messages are concise (under 4000 chars for Telegram limit).
- No automatic sending without approval.
- No message contains secrets or sensitive data.
- Arabic and English modes supported.
- `RemoteDisconnected` errors are transient — retry with backoff.

---

## 7. Forbidden Autonomous Actions

The following actions are **forbidden** for Hermes in any mode, including 24/7. Even with Sultan approval, some of these require a separate, explicit, documented decision.

| # | Forbidden Action | Rationale |
|---|---|---|
| 1 | **no production changes** | Production/main branch is never modified without separate explicit approval |
| 2 | **no main merge** | Main branch merge requires a separate `APPROVE_MERGE` (future) |
| 3 | **no commit without Sultan approval** | Every commit requires `APPROVE_COMMIT` with exact scope and message |
| 4 | **no restart without Sultan approval** | Every restart requires `APPROVE_RESTART` with exact service and rollback plan |
| 5 | **no token/env/auth access** | Secrets are never read, written, or referenced |
| 6 | **no deletion** | No file deletion of any kind |
| 7 | **no paid cloud usage** | No paid API, cloud, or resource usage without explicit approval |
| 8 | **no medical/diagnostic/therapeutic claims** | All outputs remain engineering-only |
| 9 | **no external integrations without approval** | No third-party service integration without documented approval |
| 10 | **no automatic Telegram sending in D1** | D1 is design-only for Telegram behavior |
| 11 | **no auto-approve or auto-reject** | All approvals come from Sultan |
| 12 | **no scope expansion** | Approved scope is exact. No deviation permitted. |

---

## 8. Future Implementation Plan

The following phases implement the 24/7 employee mode incrementally. Each phase is a bounded step with explicit approval required before activation.

### D2: Local Report Generator Script
**Goal:** Create a Python script that generates the daily report from heartbeat files, git state, and test results.
**Scope:**
- `bin/generate_daily_report.py` — reads inputs, produces `reports/daily/YYYY-MM-DD.md`.
- Read-only inputs only. No writes except the report file.
- Manual execution only. No scheduling.
**Approval needed:** Sultan approves the script scope and file list.
**Risk:** Low — read-only script with single output file.

### D3: Telegram Report Command Integration
**Goal:** Add a `/report` command to the Telegram bot that triggers the D2 report generator and sends the result.
**Scope:**
- Add `cmd_report` handler to `telegram_bot/bot.py`.
- Wire to COMMANDS dict.
- Add to help text.
- Manual trigger only. No auto-send.
**Approval needed:** Sultan approves the bot.py changes and command behavior.
**Risk:** Low — adds read-only command to existing bot.

### D4: Approval Gate Enforcement
**Goal:** Implement the approval command interface in the Telegram bot.
**Scope:**
- Add `/approve_plan <id>`, `/approve_execute <id>`, `/approve_commit <id>`, `/approve_restart <id>`, `/reject <id>`, `/hold <id>`, `/revise <id>` commands.
- Update pending command state in `bot.py`.
- Add audit logging for all approval decisions.
- Manual trigger only. No auto-approval.
**Approval needed:** Sultan approves the bot.py changes and approval flow.
**Risk:** Medium — adds write behavior to pending command state.

### D5: Scheduler Proposal (Not Activation)
**Goal:** Design a scheduling mechanism for the 6 work cycles. Propose the design. Do not activate.
**Scope:**
- `governance/HERMES_SCHEDULER_D5.md` — scheduler design document.
- Options: cron, systemd timer, Python asyncio loop, tmux session with sleep loop.
- Recommendation with rationale.
- No activation. No scheduling created.
**Approval needed:** Sultan approves the scheduler design and selects the preferred option.
**Risk:** Low — design document only.

### D6: Supervised 24h Dry Run
**Goal:** Execute the full 24/7 cycle manually for 24 hours under Sultan's supervision.
**Scope:**
- Run all 6 work cycles manually.
- Use D2 report generator (if approved).
- Send reports via Telegram manually.
- Document all findings, gaps, and improvements.
- No automation. No scheduling.
**Approval needed:** Sultan approves the dry run plan and commits to supervising.
**Risk:** Low — manual execution with supervision.

### D7: Limited Always-On Mode
**Goal:** Enable a limited always-on mode with Sultan's explicit approval.
**Scope:**
- Activate the scheduler (per D5 approved option).
- Enable automatic report generation at defined intervals.
- Enable automatic heartbeat monitoring.
- Keep all execution gated behind approval.
- No autonomous task execution.
- No production deployment.
- Daily manual review by Sultan.
**Approval needed:** Sultan approves the always-on mode scope, schedule, and boundaries.
**Risk:** Medium — introduces scheduling and automated message sending (limited).

---

## 9. D1 Boundaries

D1 is a **design and documentation** phase. It:

- Defines Hermes as a 24/7 employee with clear responsibilities.
- Establishes work cycles inherited from C7.
- Defines approval commands for Sultan.
- Specifies future Telegram behavior.
- Lists forbidden autonomous actions.
- Plans future implementation phases D2–D7.

D1 **does not**:

- Enable autonomous execution.
- Schedule any process.
- Send any Telegram messages.
- Modify `telegram_bot/bot.py`.
- Create any script, scheduler, or service.
- Commit any changes.
- Activate always-on mode.

---

## 10. Cross-Reference Index

| Document | Relationship |
|---|---|
| `SOUL.md` | Hermes identity and principles that D1 operationalizes |
| `QWEN.md` | Executor rules that D1 delegates to |
| `AGENTS.md` | Agent roles that D1 coordinates |
| `governance/HERMES_DAILY_OPERATING_LOOP_C7.md` | Work cycles that D1 inherits |
| `governance/HERMES_APPROVAL_GATE_C8.md` | Approval process that D1 enforces |
| `reports/daily/2026-05-10_C9_non_production_trial_report.md` | Trial findings that D1 inherits |
| `templates/sultan_approval_gate_request_template.md` | Approval request format that D1 uses |
| `templates/daily_operating_loop_report_template.md` | Report format that D1 uses |
| `runtime/agent_health/*.json` | Status input that D1 reads |

---

*End of HERMES 24/7 Employee Mode — Phase D1*

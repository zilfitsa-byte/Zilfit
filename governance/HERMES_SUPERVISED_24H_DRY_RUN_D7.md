# HERMES Supervised 24h Dry Run — Phase D7

**Status:** Design only. No activation. No production impact.
**Date created:** 2026-05-11
**Branch:** codex/livefit-camera-ux-isolated-v1
**Owner:** Sultan
**Predecessors:** C1–C9, D1–D6 (memory, skills, templates, heartbeat, daily loop, approval gate, non-production trial, daily report Telegram commands, executive manager mode, approval enforcement, scheduler design)

---

## 1. Purpose

Phase D7 defines the **supervised 24-hour dry run** for Hermes Executive Manager mode — testing the full daily operating rhythm manually before considering always-on mode in D8.

This document defines:
- D7 purpose and supervised dry-run scope
- Why D7 is not production and not always-on mode
- Relationship to D4 Executive Manager, D5 Approval Enforcement, D6 Scheduler Design
- Relationship to future D8 limited always-on mode
- 7 supervised dry-run windows with detailed specifications
- D7 allowed and forbidden actions
- D7 observation report structure
- D8 readiness criteria

**D7 scope:** Manual supervised testing only. No automatic execution. No cron/systemd/tmux activation.

---

## 2. Supervised 24-Hour Dry-Run Scope

### 2.1 What D7 Does

D7 is a **supervised manual testing phase** that:

- Tests all 7 windows of the daily operating rhythm manually
- Validates daily report generation works
- Verifies Telegram read-only commands work
- Confirms approval enforcement remains intact
- Documents gaps, failures, and improvements
- Prepares for D8 limited always-on mode (if successful)

### 2.2 What D7 Does NOT Do

D7 **does not**:

- Enable any automatic execution (cron, systemd, Python asyncio)
- Create any scheduled task files
- Activate any scheduler
- Create tmux sessions (unless Sultan explicitly approves a supervised session)
- Modify `telegram_bot/bot.py`
- Enable automatic Telegram sending
- Auto-approve or auto-reject requests
- Modify cron/systemd/tmux
- Touch production/main branch
- Commit changes without explicit Sultan approval

### 2.3 Why D7 Is NOT Production

D7 is **not production** because:

| Aspect | Production | D7 Dry Run |
|--------|------------|------------|
| Automation | Fully automatic | Fully manual |
| Scheduling | Cron/systemd | Human triggers only |
| Telegram | Auto-sending | Manual commands only |
| Approval | Stored | Manual Sultan approval |
| Execution | Autonomous | Human-supervised |

### 2.4 Why D7 Is NOT Always-On Mode

D7 is **not always-on** because:

| Aspect | Always-On (D8) | D7 Dry Run |
|--------|----------------|------------|
| Activation | Automated | Manual start per window |
| Monitoring | Continuous | Intermittent checks |
| Response | Automatic | Human-triggered |
| Scope | Production-safe | Design validation only |
| State | Persistent | No persistent scheduler |

D7 validates the design. D8 enables the operational system.

---

## 3. Relationship to Other Phases

### 3.1 D4 → D7: Executive Manager → Supervised Testing

D4 defines Hermes as Executive Operating Manager with responsibilities.

D7 tests those responsibilities manually:
- Morning Briefing window: Test executive summary generation
- Midday Check: Test quick health snapshot
- Afternoon QA: Test quality verification
- Evening QA: Test status check
- Night Report: Test daily summary
- Final 24h Review: Test overall process

### 3.2 D5 → D7: Approval Enforcement → Supervised Validation

D5 establishes approval-first operating rules.

D7 validates those rules:
- Every action requires explicit Sultan approval
- No automatic execution allowed
- No commit by assumption
- No restart by assumption
- All forbidden patterns remain forbidden

### 3.3 D6 → D7: Scheduler Design → Manual Window Testing

D6 defines 5 schedule windows matching C7 daily rhythm.

D7 tests those windows manually:
- Manual start per window (no automatic scheduling)
- Sultan approval per window execution
- Complete audit trail per window
- Document findings per window

### 3.4 D7 → D8: Dry Run → Limited Always-On Mode

D7 is the validation phase.

D8 enables always-on mode with explicit approval:
- Only after D7 success
- Sultan's explicit activation
- All safety rules preserved
- No automatic approval (approval remains manual)

---

## 4. Supervised Dry-Run Windows

D7 uses 7 windows for comprehensive testing.

### 4.1 Window 1: Start Check (Manual Trigger)

| Attribute | Value |
|-----------|-------|
| **Purpose** | Verify environment and initial state before D7 |
| **Trigger** | Sultan manual command to start D7 |
| **Read-Only** | Yes |
| **Approval Required** | None (read-only verification) |

**Inputs:**
- `git status --short` — working tree state
- `git branch --show-current` — current branch
- `git log --oneline -5` — recent commits
- `runtime/agent_health/*.json` — agent heartbeat files
- `reports/daily/` — existing daily reports
- `reports/nightly/` — existing nightly reports

**Allowed Outputs:**
- Status summary for Sultan
- Confirmation that D7 can proceed

**Forbidden Actions:**
- ❌ Production/main branch changes
- ❌ Commit without `approved_commit`
- ❌ Restart without `approved_restart`
- ❌ Token/env/auth access
- ❌ File deletion
- ❌ Cron/systemd/tmux activation

**Required Sultan Approval:**
- None for start check (read-only)

**Expected Observation Notes:**
- Working tree state (clean/dirty)
- Branch confirmation
- Agent heartbeat presence
- Existing report files

**Pass/Fail Criteria:**
- PASS: Environment verified, ready to proceed
- FAIL: Missing required files, unexpected state

---

### 4.2 Window 2: Morning Briefing (08:00 UTC)

| Attribute | Value |
|-----------|-------|
| **Purpose** | Generate morning executive summary for Sultan |
| **Trigger** | Manual command at 08:00 UTC or Sultan command |
| **Read-Only** | Yes |
| **Approval Required** | `approved_execute` for any write |

**Inputs:**
- `runtime/agent_health/*.json` — agent status
- `reports/daily/YYYY-MM-DD_hermes_daily_operating_report.md` — previous day
- `reports/nightly/YYYY-MM-DD_check_results.md` — overnight results
- `AGENTS.md` — agent roles
- `SOUL.md` — Hermes identity

**Allowed Outputs:**
- `reports/executive/YYYY-MM-DD_morning_briefing.md` (with `approved_execute`)
- Telegram message (manual only)

**Forbidden Actions:**
- ❌ Production/main branch changes
- ❌ Commit without `approved_commit`
- ❌ Token/env/auth access
- ❌ Medical/diagnostic claims

**Required Sultan Approval:**
- `approved_execute` for any file write
- `approved_commit` for any git commit

**Expected Observation Notes:**
- Agent status summary
- Overnight results summary
- Morning priority list
- Any escalation items

**Pass/Fail Criteria:**
- PASS: Briefing generated, Sultan reviewed
- FAIL: Missing data, generation failed

---

### 4.3 Window 3: Midday Planning Check (12:00 UTC)

| Attribute | Value |
|-----------|-------|
| **Purpose** | Quick mid-day status snapshot |
| **Trigger** | Manual command at 12:00 UTC or Sultan command |
| **Read-Only** | Yes |
| **Approval Required** | None (read-only check) |

**Inputs:**
- `runtime/agent_health/*.json` — current agent status
- `reports/daily/YYYY-MM-DD_hermes_daily_operating_report.md` — current report
- Active approval requests

**Allowed Outputs:**
- Midday status snapshot
- Telegram summary (manual only)

**Forbidden Actions:**
- ❌ Production/main branch changes
- ❌ Commit without `approved_commit`
- ❌ Restart without `approved_restart`

**Required Sultan Approval:**
- None (read-only)

**Expected Observation Notes:**
- Current agent status
- Task queue summary
- Approval queue status
- Any blockers

**Pass/Fail Criteria:**
- PASS: Status snapshot generated
- FAIL: Data inaccessible

---

### 4.4 Window 4: Afternoon Readiness Check (16:00 UTC)

| Attribute | Value |
|-----------|-------|
| **Purpose** | Verify quality gates and readiness for night cycle |
| **Trigger** | Manual command at 16:00 UTC or Sultan command |
| **Read-Only** | Yes |
| **Approval Required** | None (read-only verification) |

**Inputs:**
- `reports/quality/*.json` — quality gate results
- `git status --short` — working tree state
- `runtime/agent_health/*.json` — agent status
- Approved scope vs. actual changes

**QA Checks:**
1. Syntax validation: `python3 -m py_compile <modified files>`
2. JSON validation: `python3 -m json.tool <modified files>`
3. Grep forbidden patterns: `grep -rn "forbidden_pattern" <path>`
4. Git diff matches approved scope
5. Tests pass (if applicable)

**Allowed Outputs:**
- Readiness assessment
- Telegram summary (manual only)

**Forbidden Actions:**
- ❌ Production/main branch changes
- ❌ Deviation from approved scope
- ❌ Self-approval or implied approval
- ❌ Medical/diagnostic claims

**Required Sultan Approval:**
- None (read-only verification)

**Expected Observation Notes:**
- Quality gate status
- Working tree state
- Approval scope match
- Any failures

**Pass/Fail Criteria:**
- PASS: All QA checks pass
- FAIL: Any QA check fails

---

### 4.5 Window 5: Evening QA/Status Check (19:00 UTC)

| Attribute | Value |
|-----------|-------|
| **Purpose** | Evening status verification before night cycle |
| **Trigger** | Manual command at 19:00 UTC or Sultan command |
| **Read-Only** | Yes |
| **Approval Required** | None (read-only check) |

**Inputs:**
- `runtime/agent_health/*.json` — final agent status
- `reports/daily/*.md` — daily reports
- `reports/quality/*.json` — quality results
- Task completion status

**Allowed Outputs:**
- Evening status summary
- Telegram summary (manual only)

**Forbidden Actions:**
- ❌ Production/main branch changes
- ❌ Commit without `approved_commit`
- ❌ Token/env/auth access

**Required Sultan Approval:**
- None (read-only)

**Expected Observation Notes:**
- Daily accomplishments
- Task completion rate
- Quality status
- Evening risks

**Pass/Fail Criteria:**
- PASS: Status verified
- FAIL: Critical issues found

---

### 4.6 Window 6: Night Report (22:00 UTC)

| Attribute | Value |
|-----------|-------|
| **Purpose** | Generate daily summary for Sultan review |
| **Trigger** | Manual command at 22:00 UTC or Sultan command |
| **Read-Only** | Yes |
| **Approval Required** | `approved_execute` for any write |

**Inputs:**
- `runtime/agent_health/*.json` — final agent status
- `reports/daily/*.md` — daily reports
- `reports/nightly/*.md` — nightly check results
- `reports/executive/*.md` — executive summaries
- Approval request history
- Task completion status

**Allowed Outputs:**
- `reports/executive/YYYY-MM-DD_night_report.md` (with `approved_execute`)
- Telegram night summary (manual only)

**Forbidden Actions:**
- ❌ Production/main branch changes
- ❌ Commit without `approved_commit`
- ❌ Token/env/auth access
- ❌ File deletion

**Required Sultan Approval:**
- `approved_execute` for any file write
- `approved_commit` for any git commit

**Expected Observation Notes:**
- Daily accomplishments summary
- Task completion rate
- Approval decisions summary
- Blocked items
- Tomorrow's priority proposal
- System health assessment

**Pass/Fail Criteria:**
- PASS: Night report generated, Sultan reviewed
- FAIL: Generation failed, missing data

---

### 4.7 Window 7: Final 24h Review (23:30 UTC)

| Attribute | Value |
|-----------|-------|
| **Purpose** | Comprehensive review of D7 success and D8 readiness |
| **Trigger** | Manual command at 23:30 UTC or Sultan command |
| **Read-Only** | Yes |
| **Approval Required** | None (read-only review) |

**Inputs:**
- All 6 window observations
- D7 observation template
- Agent heartbeat summary
- Daily reports
- Quality gate results
- Approval request history

**Allowed Outputs:**
- D7 final review report
- D8 readiness assessment
- Telegram summary (manual only)

**Forbidden Actions:**
- ❌ Production/main branch changes
- ❌ Commit without `approved_commit`
- ❌ Token/env/auth access
- ❌ File deletion

**Required Sultan Approval:**
- None (read-only review)

**Expected Observation Notes:**
- Window completion status
- Failures and gaps
- Improvements identified
- D8 recommendation
- Sultan decision

**Pass/Fail Criteria:**
- PASS: D7 completed, D8 ready
- FAIL: D7 incomplete, D8 not ready

---

## 5. D7 Allowed Actions

These actions may be performed during D7:

| # | Action | Approval Required |
|---|--------|-------------------|
| 1 | Read git status | No |
| 2 | Read recent git log | No |
| 3 | Read governance docs | No |
| 4 | Read templates | No |
| 5 | Read skills | No |
| 6 | Read runtime/agent_health JSON | No |
| 7 | Read reports/daily | No |
| 8 | Read reports/nightly | No |
| 9 | Read reports/quality | No |
| 10 | Run tools/hermes_daily_report.py manually | `approved_execute` for write |
| 11 | Summarize status | No |
| 12 | Prepare approval requests | No |
| 13 | Prepare observation report | `approved_execute` for write |
| 14 | Generate reports manually | `approved_execute` for write |
| 15 | Telegram commands (read-only) | No |
| 16 | Test approval enforcement | No |
| 17 | Document findings | No |
| 18 | Escalate blockers | No |

**Rule:** If an action writes, modifies, or executes, it requires `approved_execute` approval.

---

## 6. D7 Forbidden Actions

The following actions are **permanently forbidden** during D7:

| # | Forbidden Action | Rationale |
|---|------------------|-----------|
| 1 | **No production/main changes** | Production baseline stability |
| 2 | **No commit without Sultan approval** | Every commit needs explicit approval |
| 3 | **No restart without Sultan approval** | Service restart needs documented rollback |
| 4 | **No token/env/auth access** | Secrets never read/written |
| 5 | **No deletion** | No file deletion without approval |
| 6 | **No paid cloud usage** | No paid resources without approval |
| 7 | **No cron/systemd activation** | Production scheduling control |
| 8 | **No tmux activation** | tmux session requires explicit Sultan approval |
| 9 | **No autonomous execution** | All actions require explicit approval |
| 10 | **No automatic Telegram sending** | D7 is manual only |
| 11 | **No medical/diagnostic/therapeutic/clinical claims** | All outputs engineering-only |

**Telegram messages must NEVER contain:**
- `ZILFIT_TELEGRAM_BOT_TOKEN`
- `ZILFIT_TELEGRAM_ADMIN_IDS`
- `.env` file contents
- API keys, secrets, or credentials

---

## 7. D7 Observation Report Structure

Each window must generate an observation report.

### 7.1 Report Template

```markdown
# D7 Observation Report

**dry_run_id:** D7-YYYYMMDD-HHMM
**start_time_utc:** YYYY-MM-DDTHH:MM:SSZ
**end_time_utc:** YYYY-MM-DDTHH:MM:SSZ
**window:** Morning Briefing / Midday Check / Afternoon QA / Evening QA / Night Report / Final Review
**branch:** codex/livefit-camera-ux-isolated-v1
**commits_checked:** <last N commits>
**windows_completed:** <count>
**reports_generated:** <count>
**Telegram checks:** <commands tested>
**approval_requests_created:** <count>
**blocked_actions:** <list>
**failures:** <list>
**risks:** <list>
**Sultan decisions:** <list>
**recommendation_for_D8:** YES / NO / REVISION

---

## Window Details

**Window:** <name>
**Start:** <timestamp>
**End:** <timestamp>
**Trigger:** <manual/Sultan command/time>

## Actions Performed

1. <action 1>
2. <action 2>
...

## Observations

- <observation 1>
- <observation 2>
...

## Issues Found

- <issue 1>
- <issue 2>
...

## Approval Status

- <approval request 1>: approved/rejected/held
- <approval request 2>: approved/rejected/held

## Recommendations

1. <recommendation 1>
2. <recommendation 2>
...
```

### 7.2 Sultan Decision Fields

| Field | Value |
|-------|-------|
| **D7 Completion** | [ ] Complete | [ ] Incomplete | [ ] Failed |
| **D8 Readiness** | [ ] Ready | [ ] Not Ready | [ ] Revision Needed |
| **Sultan Decision** | [ ] Approve D8 | [ ] Reject D8 | [ ] Request Revision |
| **Sultan Notes** | _optional comments_ |

---

## 8. D8 Readiness Criteria

D8 may only be considered if **ALL** of the following criteria are met:

### 8.1 Technical Criteria

| # | Criterion | Status |
|---|-----------|--------|
| 1 | D7 completes without unsafe actions | Must pass |
| 2 | Daily report generation works | Must pass |
| 3 | Telegram read-only commands work | Must pass |
| 4 | Approval enforcement remains intact | Must pass |
| 5 | No secrets are touched | Must pass |
| 6 | No production/main changes happen | Must pass |

### 8.2 Documentation Criteria

| # | Criterion | Status |
|---|-----------|--------|
| 7 | All 7 windows documented | Must pass |
| 8 | Observation reports complete | Must pass |
| 9 | Issues and gaps documented | Must pass |
| 10 | D8 readiness assessment complete | Must pass |

### 8.3 Sultan Approval Criteria

| # | Criterion | Status |
|---|-----------|--------|
| 11 | Sultan explicitly approves D8 | Must pass |
| 12 | Sultan reviewed all D7 findings | Must pass |

### 8.4 Final D8 Activation

D8 activation requires:

1. **D7 Completion:** All 7 windows successfully tested
2. **D8 Proposal:** Sultan-approved proposal for always-on mode
3. **Explicit Approval:** Sultan `APPROVE_RESTART` for D8 activation
4. **Readiness Check:** Final D8 readiness verification
5. **Manual Start:** D8 started manually by Sultan command

---

## 9. D7 Boundaries Summary

D7 is a **supervised manual testing** phase. It:

- Tests all 7 daily rhythm windows manually
- Validates daily report generation
- Verifies Telegram read-only commands
- Confirms approval enforcement
- Documents gaps, failures, improvements
- Prepares for D8 limited always-on mode

D7 **does not**:

- Enable any automatic execution (cron, systemd, Python asyncio)
- Create any scheduled task files
- Activate any scheduler
- Create tmux sessions (unless Sultan explicitly approves)
- Modify `telegram_bot/bot.py`
- Enable automatic Telegram sending
- Auto-approve or auto-reject requests
- Modify cron/systemd/tmux
- Touch production/main branch
- Commit changes without explicit Sultan approval

---

## 10. Cross-Reference Index

| Document | Relationship |
|----------|-------------|
| `SOUL.md` | Hermes identity that D7 respects |
| `AGENTS.md` | Agent roles that D7 tests |
| `governance/HERMES_EXECUTIVE_MANAGER_D4.md` | Executive responsibilities that D7 validates |
| `governance/HERMES_EXECUTIVE_APPROVAL_ENFORCEMENT_D5.md` | Approval enforcement that D7 verifies |
| `governance/HERMES_SCHEDULER_DESIGN_D6.md` | Scheduler design that D7 tests manually |
| `tools/hermes_daily_report.py` | Report generator that D7 validates |
| `templates/hermes_24h_dry_run_observation_template.md` | Observation report template |
| `runtime/agent_health/*.json` | Input data that D7 reads |
| `reports/daily/*.md` | Daily reports that D7 generates |
| `reports/nightly/*.md` | Nightly reports that D7 reads |
| `telegram_bot/bot.py` | Telegram commands that D7 tests |

---

*End of HERMES Supervised 24h Dry Run — Phase D7*

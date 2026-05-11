# HERMES Scheduler Design — Phase D6

**Status:** Design only. No activation. No automatic execution.
**Date created:** 2026-05-11
**Branch:** codex/livefit-camera-ux-isolated-v1
**Owner:** Sultan
**Predecessors:** C1–C9, D1–D5 (memory, skills, templates, heartbeat, daily loop, approval gate, non-production trial, daily report Telegram commands, executive manager mode, approval enforcement)

---

## 1. Purpose

Phase D6 defines the **scheduler design** for Hermes Executive Manager mode — establishing a safe, read-only scheduling framework that respects the approval-gated operating model established in D5.

This document defines:
- Scheduler purpose and design-only scope
- 5 schedule windows matching the daily operating rhythm
- Safety rules preventing automatic execution
- Future activation options (disabled in D6)
- D7 preparation requirements for supervised 24h dry run

**D6 scope:** Design and documentation only. No cron, systemd, tmux, or Python scheduler activation. No code changes. No bot modifications.

---

## 2. Design-Only Scope

### 2.1 What D6 Does

D6 is a **design phase** that:

- Defines scheduling windows for the 5-phase daily operating rhythm
- Specifies inputs, outputs, and safety rules per window
- Documents activation options for future phases
- Establishes approval requirements per action type
- Prepares for D7 supervised 24h dry run

### 2.2 What D6 Does NOT Do

D6 **does not**:

- Activate any scheduler (cron, systemd, Python asyncio, tmux)
- Create any scheduled task files
- Modify `telegram_bot/bot.py`
- Enable any automatic execution
- Create tmux sessions or services
- Touch `cron/`, `systemd/`, or scheduling directories
- Auto-generate or auto-send Telegram messages
- Commit any changes

---

## 3. Relationship to Other Phases

### 3.1 D4 → D6: Executive Manager → Scheduler Design

D4 defines Hermes as Executive Operating Manager with responsibilities.

D6 provides the scheduling framework for executing those responsibilities:
- Schedule windows align with D4's executive decision levels
- Daily rhythm (C7) maps to 5 scheduling windows
- Agent management (D4) defines what runs when

### 3.2 D5 → D6: Approval Enforcement → Scheduler Safety

D5 establishes approval-first operating rules.

D6 enforces safety in scheduling:
- All scheduled actions require `approved_execute` or `approved_commit` state
- No automatic commit or restart allowed
- Read-only by default; write actions blocked
- Forbidden patterns remain forbidden (production, deletion, tokens, medical)

### 3.3 D2 → D6: Daily Report Generator → Scheduled Report Tasks

D2 creates the local daily report generator script.

D6 defines when that script runs:
- Morning Briefing window: Generate status for Sultan review
- Midday Check: Quick status snapshot
- Afternoon QA: Readiness verification
- Night Report: Daily summary for Sultan

### 3.4 D3 → D6: Telegram Commands → Scheduled Command Execution

D3 adds read-only Telegram commands.

D6 could schedule command execution (disabled):
- `/daily_report` command timing
- `/daily_status` command timing
- `/approval_queue` command timing

### 3.5 D6 → D7: Design → Supervised 24h Dry Run

D6 defines the scheduler design.

D7 implements it for supervised 24h testing:
- Manual activation only (no auto-start)
- All approvals from Sultan
- Complete audit trail
- Find gaps, refine design

### 3.6 D6 → D8: Design → Always-On Mode

D6 defines the safe scheduling framework.

D8 enables always-on mode with explicit approval:
- Only after D7 success
- Sultan's explicit activation
- All safety rules preserved

---

## 4. Schedule Windows

The scheduler is divided into 5 windows matching the C7 daily rhythm.

### 4.1 Window 1: Morning Briefing (08:00 - 09:00 UTC)

| Attribute | Value |
|-----------|-------|
| **Purpose** | Prepare Sultan for daily work with executive summary |
| **Primary Action** | Generate morning executive briefing |
| **Trigger** | Manual command or scheduled (future) |
| **Read-Only** | Yes |
| **Approval Required** | `approved_execute` for any write |

**Inputs:**
- `runtime/agent_health/*.json` — agent status
- `reports/daily/YYYY-MM-DD_hermes_daily_operating_report.md` — previous day
- `reports/nightly/YYYY-MM-DD_check_results.md` — overnight results
- `AGENTS.md` — agent roles
- `SOUL.md` — Hermes identity

**Outputs (report only):**
- `reports/executive/YYYY-MM-DD_morning_briefing.md` (future)
- Telegram message (manual only in D7+)

**Forbidden Actions:**
- ❌ Production/main branch changes
- ❌ Commit without `approved_commit`
- ❌ Token/env/auth access
- ❌ Medical/diagnostic claims

**Escalation Rules:**
- If agent in `failed` state → alert Sultan immediately
- If health check fails → escalate to Sultan
- If approval queue has pending > 4h → alert Sultan

---

### 4.2 Window 2: Midday Check (12:00 - 13:00 UTC)

| Attribute | Value |
|-----------|-------|
| **Purpose** | Quick health check mid-cycle |
| **Primary Action** | Generate midday status snapshot |
| **Trigger** | Manual command or scheduled (future) |
| **Read-Only** | Yes |
| **Approval Required** | None (read-only check) |

**Inputs:**
- `runtime/agent_health/*.json` — current agent status
- `reports/daily/YYYY-MM-DD_hermes_daily_operating_report.md` — current report
- Active approval requests

**Outputs (report only):**
- `reports/executive/YYYY-MM-DD_midday_check.md` (future)
- Status summary for Sultan review

**Forbidden Actions:**
- ❌ Production/main branch changes
- ❌ File modification (D6 design-only)
- ❌ Commit without `approved_commit`
- ❌ Restart without `approved_restart`

**Escalation Rules:**
- If quality gate fails → alert Sultan
- If task count > 5 per agent → alert Sultan
- If approval queue has pending → remind Sultan

---

### 4.3 Window 3: Afternoon QA / Readiness Check (16:00 - 17:00 UTC)

| Attribute | Value |
|-----------|-------|
| **Purpose** | Verify quality gates and readiness for night cycle |
| **Primary Action** | Run QA verification checks |
| **Trigger** | Manual command or scheduled (future) |
| **Read-Only** | Yes |
| **Approval Required** | None (read-only verification) |

**Inputs:**
- `reports/quality/*.json` — quality gate results
- `git status --short` — working tree state
- `runtime/agent_health/*.json` — agent status
- Approved scope vs. actual changes

**Outputs (report only):**
- `reports/executive/YYYY-MM-DD_afternoon_qa.md` (future)
- Readiness assessment for night cycle

**QA Checks:**
1. Syntax validation: `python3 -m py_compile <modified files>`
2. JSON validation: `python3 -m json.tool <modified files>`
3. Grep forbidden patterns: `grep -rn "forbidden_pattern" <path>`
4. Git diff matches approved scope
5. Tests pass (if applicable)

**Forbidden Actions:**
- ❌ Production/main branch changes
- ❌ Deviation from approved scope
- ❌ Self-approval or implied approval
- ❌ Medical/diagnostic claims

**Escalation Rules:**
- If QA check fails → alert Sultan
- If scope deviation detected → alert Sultan
- If forbidden pattern found → alert Sultan

---

### 4.4 Window 4: Night Report (22:00 - 23:00 UTC)

| Attribute | Value |
|-----------|-------|
| **Purpose** | Generate daily summary for Sultan review |
| **Primary Action** | Generate night executive report |
| **Trigger** | Manual command or scheduled (future) |
| **Read-Only** | Yes |
| **Approval Required** | `approved_execute` for any write |

**Inputs:**
- `runtime/agent_health/*.json` — final agent status
- `reports/daily/*.md` — daily reports
- `reports/nightly/*.md` — nightly check results
- `reports/executive/*.md` — executive summaries
- Approval request history
- Task completion status

**Outputs (report only):**
- `reports/executive/YYYY-MM-DD_night_report.md` (future)
- Daily accomplished tasks summary
- Tomorrow's priority list (proposal)
- System health assessment

**Report Sections:**
1. Daily accomplishments
2. Task completion rate
3. Approval decisions summary
4. Blocked items and reasons
5. Tomorrow's priority proposal
6. System health assessment
7. Escalation summary

**Forbidden Actions:**
- ❌ Production/main branch changes
- ❌ Commit without `approved_commit`
- ❌ Token/env/auth access
- ❌ File deletion

**Escalation Rules:**
- If any task in `failed` state → alert Sultan
- If unapproved production change → alert Sultan
- If health critical → alert Sultan

---

### 4.5 Window 5: Urgent Escalation (Any Time)

| Attribute | Value |
|-----------|-------|
| **Purpose** | Handle urgent events outside scheduled windows |
| **Primary Action** | Generate urgent escalation report |
| **Trigger** | Agent alert, health failure, or Sultan command |
| **Read-Only** | Yes (initial response) |
| **Approval Required** | `approved_execute` for any action |

**Inputs:**
- `runtime/agent_health/*.json` — agent status
- Alert type and severity
- Agent's self-reported issue
- Recent approval requests
- Quality gate status

**Outputs (report only):**
- `reports/executive/YYYY-MM-DD_escalation.md` (future)
- Urgent summary for Sultan review

**Trigger Events:**
- Agent enters `failed` state
- Health check fails with `critical` severity
- Approval request pending > 4 hours
- Quality gate failure
- Forbidden pattern detected
- Sultan command `/urgent <reason>`

**Escalation Flow:**
1. Detect event
2. Generate escalation report
3. Alert Sultan via Telegram
4. Await Sultan decision
5. Execute only with explicit approval

---

## 5. Scheduler Safety Rules

These rules apply to ALL schedule windows.

### 5.1 Read-Only by Default

All scheduled actions are **read-only** unless explicitly approved:
- Reading agent health: ✅ Allowed
- Reading reports: ✅ Allowed
- Generating reports: ✅ Allowed (file write requires `approved_execute`)
- Modifying files: ❌ Requires `approved_execute`
- Committing changes: ❌ Requires `approved_commit`
- Restarting services: ❌ Requires `approved_restart`

### 5.2 No Automatic Execution

**Never** execute without explicit approval:
- ❌ No auto-execute based on "safe" appearance
- ❌ No auto-execute based on previous approval
- ❌ No auto-execute because "it worked before"
- ❌ No implied approval from conversation context

**Only execute when:**
- Approval state is `approved_execute` (or `approved_commit`/`approved_restart`)
- Exact command matches approved scope
- Working tree is clean (unless `approved_execute` permits dirty state)

### 5.3 No Commit Without Approval

Every git operation requires explicit approval:
- `git add` → requires `approved_commit`
- `git commit` → requires `approved_commit`
- `git push` → requires `approved_execute` + Sultan approval
- Branch change → requires `approved_execute`

### 5.4 No Restart Without Approval

Every restart requires explicit approval:
- Service restart → requires `approved_restart`
- tmux session restart → requires `approved_restart`
- cron reload → requires `approved_restart`
- systemd reload → requires `approved_restart`

### 5.5 Forbidden Paths (Always Blocked)

No scheduler action may touch:
- `telegram_bot/bot.py` — Production bot
- `telegram_bot/run.sh` — Production startup
- `telegram_bot/classifier.py` — Classification logic
- `QWEN.md` — Qwen instructions
- `SOUL.md` — Hermes identity
- `skills/*.md` — Skill definitions
- `governance/*.md` — Governance documents
- `templates/*.md` — Templates
- `runtime/agent_health/*.json` — Agent health (read-only)
- `reports/` — Write access blocked (D6 design-only)
- `research/` — Write access blocked
- `tokens`, `.env`, `auth` files — Secrets
- `cron/`, `systemd/`, `tmux` — Production scheduling
- `production/`, `main` branch — Production baseline

### 5.6 Medical/Diagnostic Claims (Always Forbidden)

No output may contain:
- ❌ Medical/diagnostic claims
- ❌ Therapeutic recommendations
- ❌ Clinical advice
- ❌ Patient-specific guidance

All outputs are **engineering-only**.

---

## 6. Future Activation Options (D6 Design Only)

### 6.1 Manual Command Activation (D7+)

**Description:** Sultan manually triggers scheduler via Telegram command.

**Commands:**
- `/start_scheduler` — Start scheduled windows
- `/stop_scheduler` — Stop scheduled windows
- `/scheduler_status` — Check scheduler state

**D6 Status:** Design only. Not implemented.

### 6.2 Local Script Activation (D7+)

**Description:** Local script starts scheduler in foreground or background.

**Script:** `tools/hermes_scheduler.py` (future)

**Commands:**
```bash
# Foreground (manual monitoring)
python3 tools/hermes_scheduler.py --foreground

# Background (tmux session)
python3 tools/hermes_scheduler.py --background

# One-shot mode (D7 supervised)
python3 tools/hermes_scheduler.py --once
```

**D6 Status:** Design only. Script not created.

### 6.3 tmux Session (D7+)

**Description:** Run scheduler in tmux session for persistence.

**Session:** `hermes-scheduler`

**Commands:**
```bash
# Create session
tmux new-session -d -s hermes-scheduler 'python3 tools/hermes_scheduler.py --background'

# Attach
tmux attach -t hermes-scheduler

# Kill
tmux kill-session -t hermes-scheduler
```

**D6 Status:** Design only. Session not created.

### 6.4 cron Candidate (D7+)

**Description:** Use cron for scheduled execution.

**Crontab Example (NOT activated in D6):**
```cron
# Morning Briefing (08:00 UTC)
0 8 * * * cd /root/hermes/zilfit-ip-core && python3 tools/hermes_scheduler.py --window=morning

# Midday Check (12:00 UTC)
0 12 * * * cd /root/hermes/zilfit-ip-core && python3 tools/hermes_scheduler.py --window=midday

# Afternoon QA (16:00 UTC)
0 16 * * * cd /root/hermes/zilfit-ip-core && python3 tools/hermes_scheduler.py --window=afternoon

# Night Report (22:00 UTC)
0 22 * * * cd /root/hermes/zilfit-ip-core && python3 tools/hermes_scheduler.py --window=night

# Health Check (every 30 minutes)
*/30 * * * * cd /root/hermes/zilfit-ip-core && python3 tools/hermes_scheduler.py --window=health
```

**D6 Status:** Design only. Cron not modified.

### 6.5 systemd Candidate (D7+)

**Description:** Use systemd timer for scheduled execution.

**Unit File (NOT activated in D6):**
```ini
# /etc/systemd/system/hermes-scheduler.service
[Unit]
Description=Hermes Scheduler Service
After=network.target

[Service]
Type=oneshot
ExecStart=/usr/bin/python3 /root/hermes/zilfit-ip-core/tools/hermes_scheduler.py --window=morning
WorkingDirectory=/root/hermes/zilfit-ip-core
User=hermes
Group=hermes

# /etc/systemd/system/hermes-scheduler.timer
[Unit]
Description=Hermes Scheduler Timer

[Timer]
OnCalendar=*-*-* 08:00:00 UTC
OnCalendar=*-*-* 12:00:00 UTC
OnCalendar=*-*-* 16:00:00 UTC
OnCalendar=*-*-* 22:00:00 UTC
Persistent=true

[Install]
WantedBy=timers.target
```

**D6 Status:** Design only. systemd not modified.

### 6.6 External Scheduler (D7+)

**Description:** Use external service (e.g., GitHub Actions, Cloud Functions) for scheduling.

**Options:**
- GitHub Actions workflow (cron-based)
- AWS EventBridge + Lambda
- Google Cloud Scheduler + Cloud Functions
- Azure Timer Trigger + Function App

**D6 Status:** Design only. External service not configured.

---

## 7. D7 Preparation Requirements

D7 requires the following D6 design to be ready:

### 7.1 D6 Design Checklist

| Requirement | Status | Notes |
|-------------|--------|-------|
| Scheduler windows defined | ✅ | 5 windows matching C7 rhythm |
| Safety rules documented | ✅ | Read-only, no auto-execute |
| Activation options designed | ✅ | 6 options documented |
| D7 preparation documented | ✅ | This section |
| D8 handoff documented | ✅ | D6→D8 relationship defined |

### 7.2 D7 Implementation Checklist

**D7 Scope:** Supervised 24h dry run with Sultan approval for each execution.

**Requirements:**
1. Create `tools/hermes_scheduler.py` (150-200 lines)
2. Implement window execution logic
3. Add approval check per action
4. Add report generation
5. Add escalation alerting (Telegram only after approval)
6. Add health check per window
7. Add audit logging to `reports/scheduler/`

**D7 Rules:**
- No automatic execution
- Sultan approval required for each window execution
- Complete audit trail in `reports/scheduler/`
- Manual activation only (no auto-start)
- Read-only by default (no write without approval)
- Forbidden patterns remain forbidden

### 7.3 D7 Activation Process

**Step 1:** Sultan approves D7 activation via Telegram:
```
/approve_execute d7_scheduler_dry_run
```

**Step 2:** Create scheduler script:
```bash
touch tools/hermes_scheduler.py
chmod +x tools/hermes_scheduler.py
```

**Step 3:** Run D7 test (24 hours):
- Manual start each window
- Sultan approval per execution
- Document findings
- Note gaps and improvements

**Step 4:** Compile D7 report:
- What worked
- What failed
- Gaps identified
- D8 recommendations

---

## 8. D6 Boundaries Summary

D6 is a **design and documentation** phase. It:

- Defines 5 schedule windows matching C7 daily rhythm
- Specifies inputs, outputs, and safety rules per window
- Documents activation options for future phases
- Establishes approval requirements per action type
- Prepares for D7 supervised 24h dry run

D6 **does not**:

- Activate any scheduler (cron, systemd, Python asyncio, tmux)
- Create any scheduled task files
- Modify `telegram_bot/bot.py`
- Enable any automatic execution
- Create tmux sessions or services
- Touch `cron/`, `systemd/`, or scheduling directories
- Auto-generate or auto-send Telegram messages
- Commit any changes
- Execute any action without explicit Sultan approval

---

## 9. Cross-Reference Index

| Document | Relationship |
|----------|-------------|
| `SOUL.md` | Hermes identity that D6 scheduler respects |
| `AGENTS.md` | Agent roles that D6 scheduler coordinates |
| `governance/HERMES_EXECUTIVE_MANAGER_D4.md` | Executive responsibilities that D6 schedules |
| `governance/HERMES_EXECUTIVE_APPROVAL_ENFORCEMENT_D5.md` | Approval enforcement that D6 respects |
| `governance/HERMES_DAILY_OPERATING_LOOP_C7.md` | Daily rhythm that D6 schedule windows match |
| `tools/hermes_daily_report.py` | Report generator that D6 may schedule |
| `telegram_bot/bot.py` | Telegram commands that D6 may reference |
| `templates/hermes_executive_approval_decision_template.md` | Approval request format for D6 actions |
| `runtime/agent_health/*.json` | Input data that D6 scheduler reads |

---

*End of HERMES Scheduler Design — Phase D6*

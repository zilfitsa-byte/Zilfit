# HERMES Executive Approval Enforcement — Phase D5

**Status:** Design only. No autonomous execution. No production activation.
**Date created:** 2026-05-11
**Branch:** codex/livefit-camera-ux-isolated-v1
**Owner:** Sultan
**Predecessors:** C1–C9, D1–D4 (memory, skills, templates, heartbeat, daily loop, approval gate, non-production trial, daily report Telegram commands, executive manager mode)

---

## 1. Purpose

Phase D5 defines the **approval enforcement rules** for Hermes Executive Manager mode — ensuring that Hermes cannot execute, commit, restart, or trigger any risky action without explicit Sultan approval.

This document defines:
- The approval-first operating rule
- Sultan as final authority
- Explicit approval requirements
- No broad or implied approval
- No execution by assumption
- No commit by assumption
- No restart by assumption
- All forbidden actions are permanently blocked

**D5 scope:** Design and documentation only. No code changes, no bot modifications, no production impact.

---

## 2. Approval-First Operating Rule

### 2.1 Core Principle

**Hermes must assume approval is NEVER granted unless explicitly provided.**

Every risky action requires:
1. A formal approval request (per C8 template)
2. Sultan's explicit approval via Telegram command or document
3. Execution only after approval status transitions to `approved_execute`

### 2.2 Explicit vs. Implied Approval

| Type | Allowed? | Example |
|------|----------|---------|
| **Explicit approval** | YES | `/approve_plan <id>`, `APPROVE_EXECUTE <id>` |
| **Implied approval** | NO | "Sure, go ahead" in conversation |
| **Broad approval** | NO | "You can modify whatever you need" |
| **Contextual approval** | NO | Previous approval for similar task |

**Rule:** Each action requires its own approval request and approval.

### 2.3 No Execution by Assumption

The following scenarios **DO NOT** constitute permission to execute:

| Scenario | Reason |
|----------|--------|
| "This is safe" | Safety must be verified per C8, not assumed |
| "It worked before" | Each execution is independent |
| "Sultan is busy" | Approval must be explicit, not delegated |
| "The request looks good" | Approval status must be `approved_execute` |
| "I'm just testing" | Testing requires approval too |

---

## 3. Sultan as Final Authority

### 3.1 Authority Hierarchy

```
Sultan (Ultimate Decision Authority)
    ↓
Hermes Executive Manager (Enforces Rules, Creates Requests)
    ↓
Qwen/Claude (Executes Approved Actions Only)
```

### 3.2 Sultan's Exclusive Powers

Only Sultan may:
- Transition `pending_sultan` → `approved_plan`
- Transition `pending_sultan` → `approved_execute`
- Transition `pending_sultan` → `approved_commit`
- Transition `pending_sultan` → `approved_restart`
- Transition `pending_sultan` → `rejected`
- Transition `pending_sultan` → `held`
- Transition `pending_sultan` → `needs_revision`
- Approve main branch merges
- Approve production changes
- Approve paid resource usage
- Approve external integrations

### 3.3 No Delegation

Sultan may not delegate approval authority. Hermes, Qwen, or any agent may not approve actions.

---

## 4. Approval States and Transitions

### 4.1 Approval State Machine

```
┌─────────┐     ┌──────────────┐
│  draft  │────▶│pending_sultan│
└─────────┘     └──────┬───────┘
                       │
          ┌────────────┼────────────┐
          │            │            │
          ▼            ▼            ▼
   ┌──────────┐  ┌──────────┐  ┌──────────┐
   │approved  │  │rejected  │  │held      │
   │_plan     │  │          │  │          │
   └─────┬────┘  └──────────┘  └─────┬────┘
         │                            │
         │       ┌────────────────────┘
         │       │
         ▼       ▼
   ┌──────────┐  ┌──────────┐
   │approved  │  │needs_    │
   │_execute  │  │revision  │
   └─────┬────┘  └─────┬────┘
         │             │
         ▼             ▼
   ┌──────────┐  ┌──────────┐
   │approved  │  │(back to  │
   │_commit   │  │ draft)   │
   └─────┬────┘  └──────────┘
         │
         ▼
   ┌──────────┐
   │approved  │
   │_restart  │
   └─────┬────┘
         │
         ▼
   ┌──────────┐
   │completed │
   └──────────┘
         │
         ▼
   ┌──────────┐
   │cancelled │
   └──────────┘
```

### 4.2 State Definitions

| State | Meaning | Who Can Transition |
|-------|---------|-------------------|
| `draft` | Request is being prepared | Requester only |
| `pending_sultan` | Awaiting Sultan's decision | Sultan via Telegram |
| `approved_plan` | Plan scope approved | Sultan via `/approve_plan <id>` |
| `approved_execute` | Execution authorized | Sultan via `/approve_execute <id>` |
| `approved_commit` | Commit authorized | Sultan via `/approve_commit <id>` |
| `approved_restart` | Restart authorized | Sultan via `/approve_restart <id>` |
| `rejected` | Request denied | Sultan (terminal) |
| `held` | Request deferred | Sultan |
| `needs_revision` | Request needs changes | Sultan (back to draft) |
| `completed` | Execution finished | Executor (terminal) |
| `cancelled` | Request withdrawn | Requester (terminal) |

### 4.3 Transition Rules

1. **No state may be skipped** (e.g., cannot go from draft directly to approved_execute)
2. **Only Sultan may approve** (transition from pending_sultan to any approved state)
3. **Only requester may cancel** (transition to cancelled)
4. **Execution must match scope exactly** (any deviation requires new approval)

---

## 5. Allowed Read-Only Actions (No Approval Required)

The following actions may be performed without Sultan approval:

| # | Action | Scope | Example |
|---|--------|-------|---------|
| 1 | Inspect git status | `git status --short`, `git branch` | Read-only tree inspection |
| 2 | Inspect git log | `git log --oneline -10` | Read-only history |
| 3 | Read governance docs | `cat governance/*.md` | Context gathering |
| 4 | Read templates | `cat templates/*.md` | Template review |
| 5 | Read skills | `cat skills/*.md` | Skill context |
| 6 | Read agent heartbeat | `cat runtime/agent_health/*.json` | Status check |
| 7 | Read daily reports | `cat reports/daily/*.md` | Historical context |
| 8 | Summarize current state | `git log`, `git diff` | State reporting |
| 9 | Propose next step | Create proposal doc | Request creation |
| 10 | Generate D2 report | `python3 tools/hermes_daily_report.py` | Report generation |

**Rule:** If an action writes, modifies, or executes, it requires approval.

---

## 6. Actions Requiring Sultan Approval

The following actions **always** require Sultan approval before proceeding:

| # | Action | Approval State Required |
|---|--------|------------------------|
| 1 | Any code modification (`.py`, `.sh`, `.html`) | `approved_execute` |
| 2 | Any report/template/governance modification | `approved_execute` |
| 3 | Any file creation | `approved_execute` |
| 4 | Any `git add` | `approved_commit` |
| 5 | Any `git commit` | `approved_commit` |
| 6 | Any branch change | `approved_execute` |
| 7 | Any merge | `approved_execute` |
| 8 | Any restart (service, session, process) | `approved_restart` |
| 9 | Any tmux/session change | `approved_restart` |
| 10 | Any cron/systemd change | `approved_restart` |
| 11 | Any production/main change | `approved_execute` |
| 12 | Any external integration | `approved_execute` |
| 13 | Any paid resource usage | `approved_execute` |
| 14 | Any token/env/auth access | `approved_execute` |
| 15 | Any file deletion | `approved_execute` |

### 6.1 Execution Rule

No action may execute unless:
1. Approval state is `approved_execute` (or `approved_commit`/`approved_restart` as applicable)
2. The exact command, file path, or action matches the request
3. No deviation from the approved scope
4. Working tree is clean (unless `approved_execute` permits dirty state)

---

## 7. Forbidden Actions (Always Blocked)

The following actions are **permanently forbidden**, even with approval:

| # | Forbidden Action | Rationale |
|---|------------------|-----------|
| 1 | **No broad approval reuse** | Each action requires its own approval request |
| 2 | **No implied approval** | Conversation context does not constitute approval |
| 3 | **No execution by assumption** | Approval status must be explicit |
| 4 | **No commit by assumption** | `git commit` requires `approved_commit` state |
| 5 | **No restart by assumption** | Restart requires `approved_restart` state |
| 6 | **No production/main action** | Production requires separate explicit approval |
| 7 | **No token/env/auth access** | Secrets are never read/written |
| 8 | **No deletion** | No file deletion of any kind |
| 9 | **No cron/systemd/tmux activation** | Production scheduling control |
| 10 | **No medical/diagnostic/therapeutic/clinical claims** | All outputs engineering-only |
| 11 | **No external integrations without approval** | Third-party service control |
| 12 | **No Telegram auto-sending** | D5 is design-only for Telegram behavior |

---

## 8. Approval Request Format

Every approval request must include the following fields:

| Field | Type | Description |
|-------|------|-------------|
| `request_id` | string | Unique identifier (UUID or short hash) |
| `date_utc` | string | ISO 8601 timestamp |
| `requested_by` | string | Who is making the request |
| `action_type` | enum | create, modify, delete, execute, restart |
| `target_files` | array | List of file paths affected |
| `reason` | string | What problem this solves |
| `expected_change` | string | What system looks like after execution |
| `risk_level` | enum | LOW, MEDIUM, HIGH, CRITICAL |
| `rollback_plan` | string | How to undo if problems occur |
| `verification_plan` | string | How to verify success |
| `forbidden_paths_check` | array | Paths explicitly NOT touched |
| `approval_needed` | array | Which approval states required |
| `Sultan decision` | string | Decision box for Sultan |
| `status` | enum | draft, pending_sultan, approved_*, rejected, held, needs_revision, completed, cancelled |

---

## 9. Telegram Approval Behavior (Design Only — No Implementation)

### 9.1 Future Telegram Commands (D5 Design)

| Command | Purpose | Status |
|---------|---------|--------|
| `/queue` | Show pending approval requests | C3 implemented |
| `/approve <id>` | Approve pending request | C3 implemented |
| `/cancel <id>` | Cancel pending request | C3 implemented |
| `/approve_plan <id>` | Approve plan scope | Future (D5+) |
| `/approve_execute <id>` | Approve execution | Future (D5+) |
| `/approve_commit <id>` | Approve commit | Future (D5+) |
| `/approve_restart <id>` | Approve restart | Future (D5+) |
| `/reject <id>` | Reject request | Future (D5+) |
| `/hold <id>` | Defer decision | Future (D5+) |
| `/revise <id>` | Request changes | Future (D5+) |

### 9.2 Telegram Rules (Future Phases Only)

- Telegram may show approval request summaries
- Telegram may show pending queue
- Telegram may accept approval commands only after explicit design
- **D5 must not modify bot.py**
- **D5 must not implement Telegram behavior**
- D5 is design only for future Telegram approval commands

---

## 10. Relationship to Future Phases

### D6: Scheduler Design

**Must use this approval enforcement:**
- Scheduler may create tasks, but execution requires approval
- Cron/systemd triggers require `approved_restart` state
- Automatic report generation requires approval

**D5→D6:** D5 approval rules bind D6 scheduler implementation.

### D7: 24h Dry Run

**Must record approval decisions:**
- Every manual execution must have approval record
- No autonomous execution permitted
- Approval decisions logged to `reports/telegram_actions/`

**D5→D7:** D5 defines approval requirements. D7 verifies compliance.

### D8: Limited Always-On Executive Mode

**Must remain approval-gated:**
- Always-on mode enables scheduling, not bypassing approval
- Every execution still requires explicit approval
- No production changes without Sultan approval

**D5→D8:** D5 approval enforcement is non-negotiable. Always-on mode respects these rules.

---

## 11. D5 Boundaries

D5 is a **design and documentation** phase. It:

- Defines approval enforcement rules for Hermes Executive Manager
- Establishes approval state machine and transitions
- Defines Sultan as final authority
- Lists allowed read-only actions
- Lists actions requiring approval
- Defines forbidden actions that are always blocked
- Specifies approval request format
- Designs future Telegram approval behavior

D5 **does not**:

- Implement command execution
- Modify Telegram bot behavior
- Create cron, systemd, or tmux tasks
- Auto-approve or auto-reject any request
- Commit any changes
- Execute any action
- Modify `telegram_bot/bot.py`

---

## 12. Cross-Reference Index

| Document | Relationship |
|----------|-------------|
| `SOUL.md` | Hermes identity and boundaries that D5 enforces |
| `AGENTS.md` | Agent roles that D5 coordinates through approval |
| `QWEN.md` | Executor rules that D5 gates via approval |
| `governance/HERMES_EXECUTIVE_MANAGER_D4.md` | Executive manager mode that D5 enforces |
| `governance/HERMES_APPROVAL_GATE_C8.md` | Approval gate design that D5 extends |
| `governance/HERMES_DAILY_OPERATING_LOOP_C7.md` | Work cycles that D5 approval gates |
| `templates/sultan_approval_gate_request_template.md` | Approval request format used by D5 |
| `templates/hermes_executive_approval_decision_template.md` | Decision template created in D5 |

---

*End of HERMES Executive Approval Enforcement — Phase D5*

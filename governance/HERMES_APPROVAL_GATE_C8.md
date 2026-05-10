# HERMES Approval Gate — Phase C8

**Status:** Design only. No execution. Manual approval process.
**Date created:** 2026-05-10
**Branch:** codex/livefit-camera-ux-isolated-v1
**Owner:** Sultan

---

## 1. Purpose

The Approval Gate is a mandatory control point that must be passed before **any** execution, restart, commit, deletion, production action, or sensitive change in the ZILFIT/Hermes system.

It ensures:
- Sultan is the final authority on all non-trivial actions.
- No action proceeds by assumption or implicit permission.
- Every change has a documented request, risk assessment, and rollback plan.
- The boundary between engineering work and production impact is explicit.
- All actions are traceable and auditable.

This document defines the **design and manual template** for the Approval Gate. Phase C8 does **not** implement automated approval, command execution, or any bot/system behavior.

---

## 2. Relationships

### 2.1 Telegram Control Room
The Telegram bot provides Sultan with mobile access to:
- `/queue` — view pending approval requests.
- `/approve <id>` — approve a pending request.
- `/cancel <id>` — reject a pending request.
- **C8 does not modify bot.py.** The bot remains read-only. The approval gate is a manual process that may be mediated through the bot in future phases.

### 2.2 Qwen Execution Engine
Qwen Code is the local executor for engineering tasks. It:
- Must pass through the Approval Gate before any write operation.
- Operates within the boundaries defined by approved requests.
- Must not execute any command not explicitly approved.
- **C8 does not invoke Qwen automatically.** All Qwen work remains manually triggered and approved.

### 2.3 Hermes Operating Memory
Hermes memory files (`governance/HERMES_*.md`) provide context for:
- User preferences and operational patterns.
- Project goals, constraints, and feedback history.
- Prior approval decisions and outcomes.
- **C8 reads memory for context but does not modify memory files.**

### 2.4 C6 Agent Heartbeat Files
The `runtime/agent_health/*.json` files provide per-agent status:
- May inform approval decisions (e.g., if an agent is in `failed` state).
- Are read-only sources for approval requests.
- **C8 does not modify heartbeat files.**

### 2.5 C7 Daily Operating Loop
The daily operating loop produces reports that:
- Feed into approval requests (e.g., a daily report flags a risk requiring Sultan action).
- Document outcomes of approved actions.
- **C8 does not modify the daily loop.**

### 2.6 Sultan as Final Approval Authority
Sultan is the sole approver for all gated actions. No other entity may grant approval. Delegation is not permitted. Any ambiguity in scope, intent, or safety must result in asking Sultan directly.

---

## 3. Actions Requiring Sultan Approval

The following actions **always** require Sultan approval before proceeding. This list is exhaustive and non-negotiable.

| # | Action | Reason |
|---|---|---|
| 1 | Any code modification | Affects system behavior |
| 2 | Any `git add` | Stages changes for commit |
| 3 | Any `git commit` | Creates permanent history entry |
| 4 | Any branch change | Moves working context |
| 5 | Any merge | Combines histories |
| 6 | Any restart | Affects service availability |
| 7 | Any tmux/session change | Affects running processes |
| 8 | Any cron/systemd change | Affects scheduling and services |
| 9 | Any token/env/auth access | Touches secrets |
| 10 | Any file deletion | Irreversible data loss |
| 11 | Any production/main change | Affects production system |
| 12 | Any paid cloud/resource action | Incurs cost |
| 13 | Any external integration | Introduces third-party dependency |
| 14 | Any Telegram behavior change | Affects user communication |
| 15 | Any report sent externally | Exposes internal data |
| 16 | Any medical/diagnostic/therapeutic/clinical claim | Crosses engineering boundary |

---

## 4. Actions Allowed Without Approval

The following read-only actions may be performed without Sultan approval:

| # | Action | Scope |
|---|---|---|
| 1 | Read-only inspection | `cat`, `less`, viewing files |
| 2 | `git status` / `git log` / `git diff` | Tree inspection only |
| 3 | `grep` / `find` / `ls` / `sed -n` | Read-only search and listing |
| 4 | `python3 -m py_compile` | Syntax validation only |
| 5 | `python3 -m json.tool` | JSON validation only |
| 6 | Writing a proposal document | Only when explicitly requested by Sultan |
| 7 | Reading `runtime/agent_health/*.json` | Status check only |
| 8 | Reading `governance/*.md` | Context check only |
| 9 | Reading `templates/*.md` | Template review only |
| 10 | Reading `reports/` (no write) | Historical context only |
| 11 | Reading `research/` (no write) | Research context only |
| 12 | Reading `tasks/` (no write) | Task context only |

**Rule:** If an action is not explicitly in this allowlist, it requires Sultan approval.

---

## 5. Approval Request Format

Every approval request must use the following format. All fields are required.

| Field | Type | Description |
|---|---|---|
| `request_id` | string | Unique identifier (UUID or short hash) |
| `requested_by` | string | Who is making the request (agent name or "Sultan") |
| `phase` | string | Current Hermes phase (e.g., C8) |
| `summary` | string | One-line description of the request |
| `files_to_change` | array | List of file paths to be created or modified |
| `commands_to_run` | array | List of shell commands to be executed |
| `expected_effect` | string | What the system state looks like after execution |
| `rollback_plan` | string | How to undo the change if it causes problems |
| `risks` | array | List of identified risks and mitigations |
| `why_needed` | string | Justification for the request |
| `approval_status` | enum | draft, pending_sultan, approved, rejected, executed, cancelled |
| `approved_by` | string | "Sultan" or null |
| `approved_at_utc` | string | ISO 8601 timestamp or null |

---

## 6. Approval States

| State | Meaning | Transitions |
|---|---|---|
| `draft` | Request is being prepared | → pending_sultan |
| `pending_sultan` | Awaiting Sultan's decision | → approved, rejected, cancelled |
| `approved` | Sultan has approved the exact scope | → executed |
| `rejected` | Sultan has denied the request | → (terminal) |
| `executed` | The approved action has been completed | → (terminal) |
| `cancelled` | Request was withdrawn by requester | → (terminal) |

**Transition rules:**
- Only Sultan may transition from `pending_sultan` to `approved` or `rejected`.
- Only the requester may transition to `cancelled`.
- Only the executor may transition from `approved` to `executed`.
- No state may be skipped.

---

## 7. Execution Rule

No approved action may be executed unless:
1. `approval_status` is `approved`.
2. The exact command, file path, or action in the request matches what is executed.
3. No deviation from the approved scope is permitted.
4. If the execution reveals new risks, stop immediately and return to `pending_sultan`.

---

## 8. Commit Rule

No `git commit` may be made unless:
1. Sultan approves the exact commit scope (which files are included).
2. Sultan approves the exact commit message.
3. The working tree is clean except for the approved files.
4. All pre-commit checks (py_compile, json.tool, grep validations) have passed.

---

## 9. Restart Rule

No restart of any service, session, or process may occur unless:
1. Sultan approves the exact service/session name.
2. Sultan approves the reason for restart.
3. A rollback plan is documented.
4. The restart does not block the daily operating loop (C7).

---

## 10. Escalation Rule

**Any ambiguity means stop and ask Sultan.** This includes:
- Unclear scope in an approved request.
- Unexpected side effects during execution.
- A required action not listed in the allowlist or the approval-required list.
- Conflicting instructions from multiple sources.
- Any situation where safety cannot be verified.

Escalation is the default path. Autonomy is not assumed.

---

## 11. Forbidden Behavior

The following behaviors are **forbidden** regardless of approval status. Even approved requests cannot authorize these:

| # | Forbidden Behavior | Rationale |
|---|---|---|
| 1 | **no execution by assumption** | Approval must be explicit, never implicit |
| 2 | **no broad approval reuse** | Each action requires its own approval |
| 3 | **no "allow all edits"** | Scope must be per-file, per-action |
| 4 | **no secret exposure** | No reading, writing, or referencing .env, tokens, keys |
| 5 | **no production action** | Production/main is never modified directly |
| 6 | **no deletion** | No file deletion of any kind |
| 7 | **no main merge** | No merge to production/main without Sultan's explicit separate approval |
| 8 | **no medical claims** | No medical/diagnostic/therapeutic/clinical/pain/disease/treatment claims |

---

## 12. C8 Boundaries

C8 is a **design and template** phase. It:
- Defines the Approval Gate process.
- Creates a manual approval request template.
- Establishes approval states and transition rules.
- Documents escalation and forbidden behavior.
- Links to all prior C5–C7 components.

C8 **does not**:
- Implement command execution.
- Modify Telegram bot behavior.
- Create cron, systemd, or tmux tasks.
- Auto-approve or auto-reject any request.
- Commit any changes.
- Execute any action.

---

*End of HERMES Approval Gate — Phase C8*

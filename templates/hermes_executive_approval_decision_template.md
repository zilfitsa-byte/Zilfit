# Hermes Executive Approval Decision

> **Phase D5 baseline. Fill in by hand before any action. Do not auto-submit.**

---

## Request Metadata

| Field | Value |
|---|---|
| **Request ID** | _(UUID or short hash, e.g., a1b2c3d4)_ |
| **Date UTC** | YYYY-MM-DDTHH:MM:SSZ |
| **Phase** | D5 |
| **Requested by** | _(Hermes or agent name)_ |
| **Action Type** | [ ] create / [ ] modify / [ ] delete / [ ] execute / [ ] restart |

---

## Proposed Action

**Summary:** _(one-line description of what is being requested)_

**Why this is needed:**
> _(justification — what problem this solves or what goal it advances)_

---

## Files Affected

| # | File Path | Action (create / modify / delete) | Purpose |
|---|---|---|---|
| 1 | | | |
| 2 | | | |
| 3 | | | |

---

## Risk Level

| [ ] LOW | Minor scope change, non-critical path, easy rollback |
| [ ] MEDIUM | Multiple files, moderate complexity, documented rollback |
| [ ] HIGH | Production-adjacent, irreversible changes |
| [ ] CRITICAL | Production/main branch, paid resources, medical implications |

**Identified risks:**
| # | Risk | Severity | Mitigation |
|---|------|----------|------------|
| 1 | | | |
| 2 | | | |

---

## Rollback Plan

> _(Step-by-step instructions for undoing this change if it causes problems. Include exact git commands, file restores, or service restarts as needed.)_

**Rollback procedure:**
1. _step 1_
2. _step 2_
3. _step 3_

---

## Verification Plan

| # | Check | Command | Expected Result |
|---|-------|---------|-----------------|
| 1 | Syntax validation | `python3 -m py_compile <file>` | No errors |
| 2 | JSON validation | `python3 -m json.tool <file>` | Valid JSON |
| 3 | Git status | `git status --short` | Clean or expected files |
| 4 | Grep check | `grep -n <pattern> <file>` | No forbidden patterns |
| 5 | Other | _custom check_ | _expected result_ |

---

## Forbidden Paths Check

> _(Explicit list of files, directories, services, or systems that this action will NOT modify.)_

- [ ] `telegram_bot/bot.py` — Production bot
- [ ] `telegram_bot/run.sh` — Production startup
- [ ] `telegram_bot/classifier.py` — Classification logic
- [ ] `QWEN.md` — Qwen instructions
- [ ] `SOUL.md` — Hermes identity
- [ ] `skills/*.md` — Skill definitions
- [ ] `governance/*.md` — Governance documents
- [ ] `templates/*.md` — Templates
- [ ] `runtime/agent_health/*.json` — Agent health
- [ ] `reports/` — Write access blocked
- [ ] `research/` — Write access blocked
- [ ] `tokens`, `.env`, `auth` files — Secrets
- [ ] `cron/`, `systemd/`, `tmux` — Production scheduling
- [ ] `production/`, `main` branch — Production baseline
- [ ] _Other: list specific paths_

---

## Approval Requirements

| Action | Required Approval State | Status |
|--------|------------------------|--------|
| Execute task | `approved_execute` | [ ] Not started |
| Commit changes | `approved_commit` | [ ] Not started |
| Restart service | `approved_restart` | [ ] Not started |

---

## Sultan Decision

> **Please review the request carefully. Your decision is final.**

| Field | Value |
|---|---|
| **Decision** | [ ] **APPROVE_PLAN** — Scope and approach approved |
| | [ ] **APPROVE_EXECUTE** — Execution authorized |
| | [ ] **APPROVE_COMMIT** — Commit authorized |
| | [ ] **APPROVE_RESTART** — Restart authorized |
| | [ ] **REJECT** — Request denied |
| | [ ] **HOLD** — Defer decision |
| | [ ] **REVISE** — Request needs changes |
| **Approved by** | Sultan |
| **Approved at UTC** | YYYY-MM-DDTHH:MM:SSZ |
| **Sultan notes** | _(optional comments, conditions, or modifications)_ |

---

## Post-Action Report

> _(To be filled after execution if approved.)_

- [ ] Action executed successfully
- [ ] Files match approved scope exactly
- [ ] Tests passed
- [ ] No forbidden patterns introduced
- [ ] Working tree in expected state
- [ ] Rollback NOT needed
- **Execution timestamp:** YYYY-MM-DDTHH:MM:SSZ
- **Executed by:** _(name/Qwen/Claude)_
- **Notes:** _(any observations or issues)_

---

## Status History

| Date UTC | Status | Action | By |
|---|---|---|---|
| | draft | Request created | Hermes |
| | pending_sultan | Awaiting Sultan decision | Hermes |
| | approved_*. | Sultan approved | Sultan |
| | rejected | Sultan rejected | Sultan |
| | held | Sultan deferred | Sultan |
| | needs_revision | Sultan requested changes | Sultan |
| | completed | Action finished | Executor |
| | cancelled | Request cancelled | Hermes |

---

*End of Hermes Executive Approval Decision — Phase D5 baseline*

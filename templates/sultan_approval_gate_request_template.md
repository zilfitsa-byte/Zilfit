# Sultan Approval Gate Request

> **Phase C8 baseline. Fill in by hand before any action. Do not auto-submit.**

---

## Request Metadata

| Field | Value |
|---|---|
| **Request ID** | _(UUID or short hash, e.g., a1b2c3d4)_ |
| **Date/time UTC** | YYYY-MM-DDTHH:MM:SSZ |
| **Phase** | _(e.g., C8)_ |
| **Requested by** | _(agent name or "Sultan")_ |
| **Approval status** | [ ] draft / [ ] pending_sultan / [ ] approved / [ ] rejected / [ ] executed / [ ] cancelled |

---

## Requested Action

**Summary:** _(one-line description)_

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

## Commands Proposed

| # | Command | Purpose |
|---|---|---|
| 1 | | |
| 2 | | |
| 3 | | |

---

## Expected Result

> _(What the system state looks like after this action is completed.)_

---

## Risk Level

[ ] Low — read-only or reversible change
[ ] Medium — affects non-critical files, easy rollback
[ ] High — affects core files, requires careful rollback
[ ] Critical — affects production or irreversible state

**Identified risks:**

| # | Risk | Mitigation |
|---|---|---|
| 1 | | |
| 2 | | |

---

## Rollback Plan

> _(Step-by-step instructions for undoing this change if it causes problems. Include exact git commands, file restores, or service restarts as needed.)_

---

## Tests / Checks to Run

| # | Check | Command |
|---|---|---|
| 1 | Syntax validation | `python3 -m py_compile <file>` |
| 2 | JSON validation | `python3 -m json.tool <file>` |
| 3 | Grep checks | `grep -n <pattern> <file>` |
| 4 | Git status | `git status --short` |
| 5 | Other | |

---

## What Will NOT Be Touched

> _(Explicit list of files, directories, services, or systems that this action will not modify. Be specific.)_

- [ ] telegram_bot/bot.py
- [ ] telegram_bot/run.sh
- [ ] telegram_bot/classifier.py
- [ ] QWEN.md
- [ ] SOUL.md
- [ ] skills/*.md
- [ ] governance/*.md (other than this request)
- [ ] runtime/agent_health/*.json
- [ ] reports/ (write)
- [ ] research/ (write)
- [ ] tokens / .env / auth files
- [ ] cron / systemd / tmux
- [ ] production / main branch
- [ ] Other: _list_

---

## Sultan Decision

| Field | Value |
|---|---|
| **Decision** | [ ] Approved / [ ] Rejected / [ ] Needs clarification |
| **Approved by** | Sultan |
| **Approved at UTC** | YYYY-MM-DDTHH:MM:SSZ |
| **Sultan notes** | _(optional comments or conditions)_ |

---

## Post-Action Report

> _(To be filled after execution if approved.)_

- [ ] Action executed successfully
- [ ] Tests passed
- [ ] Working tree in expected state
- [ ] No unexpected side effects
- [ ] Rollback NOT needed
- **Execution timestamp:** YYYY-MM-DDTHH:MM:SSZ
- **Executed by:** _(name)_
- **Notes:** _(any observations or issues)_

---

*End of Sultan Approval Gate Request — Phase C8 baseline*

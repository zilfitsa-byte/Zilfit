# Skill: Telegram Restart

**Document:** skills/telegram_restart.md
**Version:** 1.0
**Phase:** C2 — Foundation Implementation
**Date:** 2026-05-10
**Owner:** Sultan
**Status:** Active

---

## Purpose

Define the safe procedure for restarting the ZILFIT Telegram bot, including read-only preflight checks, token/env presence verification without printing raw secrets, safe tmux restart procedure, and verification through Telegram commands.

---

## When to Use

Use this skill when:

1. Restarting the Telegram bot after code changes
2. Restarting the Telegram bot after configuration changes
3. Verifying bot health and status
4. Troubleshooting bot issues

---

## Inputs

- **Current bot state** — Whether bot is running or stopped
- **Environment variables** — Token and admin IDs (never printed)
- **Git status** — Current branch and working tree state
- **Tmux session state** — Whether tmux session exists

---

## Outputs

- **Preflight check results** — PASS/FAIL for each check
- **Restart status** — Success or failure
- **Verification results** — Telegram command test results
- **Arabic report** — Summary of restart process

---

## Allowed Read Paths

- `/root/hermes/zilfit-ip-core/` — Full read access for context gathering
- `telegram_bot/` — Bot code and scripts
- `governance/TELEGRAM_BOT_OPERATIONS_RUNBOOK.md` — Operations guide
- `governance/TELEGRAM_CONTROL_ROOM_V1.md` — Bot design

---

## Allowed Write Paths

- `reports/telegram_actions/` — Audit logs (append-only)
- `logs/` — Operational logs (append-only)

---

## Forbidden Paths

- `.env` — Never read or write
- `telegram_bot/bot.py` — Never modify without Sultan approval
- `telegram_bot/run.sh` — Never modify without Sultan approval
- `cron/` — Never modify
- `systemd/` — Never modify
- `tmux` sessions — Never modify without Sultan approval

---

## Approval Requirement

| Action | Approval Required | Reason |
|--------|-------------------|--------|
| Preflight checks | No | Read-only verification |
| Token/env presence check | No | Verification only, no printing |
| Tmux restart | Yes | Affects production bot |
| Telegram verification | No | Read-only testing |

---

## Step-by-Step Safe Workflow

### Step 1: Read-Only Preflight Checks

Run these commands **before** any bot restart. They verify environment readiness **without printing secret values**.

```bash
# Check repo path exists
echo "REPO: $( [ -d /root/hermes/zilfit-ip-core ] && echo 'OK' || echo 'MISSING' )"

# Check git is available
echo "GIT: $( command -v git >/dev/null 2>&1 && echo 'OK' || echo 'MISSING' )"

# Check bot token is SET (never prints the value)
if [ -n "${ZILFIT_TELEGRAM_BOT_TOKEN:-}" ]; then
  echo "TOKEN=SET"
else
  echo "TOKEN="
fi

# Check admin IDs are SET (never prints the values)
if [ -n "${ZILFIT_TELEGRAM_ADMIN_IDS:-}" ]; then
  echo "ADMINS=SET"
else
  echo "ADMINS="
fi

# Check working tree state
cd /root/hermes/zilfit-ip-core
echo "TREE: $( git status --short 2>/dev/null | wc -l ) uncommitted change(s)"

# Check Python dependency
echo "TELEBOT: $( python3 -c 'import telebot; print("OK")' 2>/dev/null || echo 'MISSING' )"
```

**Expected output for a safe restart:**
```
REPO: OK
GIT: OK
TOKEN=SET
ADMINS=SET
TREE: 0 uncommitted change(s)
TELEBOT: OK
```

If any line shows `MISSING` or `TOKEN=` or `ADMINS=`, **do not restart**. Diagnose and fix first.

### Step 2: Check Git Status

```bash
cd /root/hermes/zilfit-ip-core
git status --short
```

If there are uncommitted changes, review them. Do not restart if the working tree is dirty and changes are unreviewed.

### Step 3: Check Env Presence (Without Printing Values)

```bash
[ -n "${ZILFIT_TELEGRAM_BOT_TOKEN:-}" ] && echo "TOKEN=SET" || echo "TOKEN=MISSING"
[ -n "${ZILFIT_TELEGRAM_ADMIN_IDS:-}" ] && echo "ADMINS=SET" || echo "ADMINS=MISSING"
```

If either shows `MISSING`, set the environment variable before proceeding:

```bash
export ZILFIT_TELEGRAM_BOT_TOKEN='your-token'
export ZILFIT_TELEGRAM_ADMIN_IDS='your-admin-ids'
```

Or use `read -s` for secure entry:

```bash
read -s -p "Bot token: " ZILFIT_TELEGRAM_BOT_TOKEN && export ZILFIT_TELEGRAM_BOT_TOKEN
read -s -p "Admin IDs: " ZILFIT_TELEGRAM_ADMIN_IDS && export ZILFIT_TELEGRAM_ADMIN_IDS
```

### Step 4: Stop Existing Bot (If Running)

```bash
# Check if tmux session exists
tmux has-session -t zilfit-bot 2>/dev/null && echo "Session exists" || echo "No session"

# If it exists, kill it
tmux kill-session -t zilfit-bot 2>/dev/null && echo "Session stopped" || echo "No session to stop"
```

### Step 5: Restart Bot in Tmux

```bash
cd /root/hermes/zilfit-ip-core
tmux new -d -s zilfit-bot 'bash telegram_bot/run.sh'
```

The `-d` flag starts the session detached (in background).

### Step 6: Verify Tmux Session

```bash
tmux has-session -t zilfit-bot && echo "tmux session: RUNNING" || echo "tmux session: NOT RUNNING"
```

If NOT RUNNING: check logs in the next step.

### Step 7: Verify Logs Do Not Show Secrets

```bash
# Check the bot's tmux log for any token-like patterns
tmux capture-pane -t zilfit-bot -p 2>/dev/null | grep -iE 'TOKEN=|SECRET|API_KEY' || echo "No secrets in log: OK"
```

If secrets are found in logs: stop the bot immediately, revoke the token via BotFather, and investigate the source.

### Step 8: Manual Telegram Verification

Send these commands in Telegram to the bot:

| # | Command | Expected |
|---|---------|----------|
| 1 | `/arabic` | "تم تفعيل اللغة العربية ✅" |
| 2 | `/status` | Branch, HEAD, tree state |
| 3 | `/queue` | Queue status (empty or items) |
| 4 | `/agents` | Compact Arabic overview |
| 5 | `/agents_product` | Z-Product detail view |
| 6 | `/agents_design` | Z-Design detail view |
| 7 | `/agents_qa` | Z-QA detail view |
| 8 | `/agents_ops` | Z-Ops detail view |
| 9 | `/agents_research` | Z-Research detail view |
| 10 | `/agents_claims` | Z-Claims detail view |

If any command fails: capture the error output and check tmux logs for Python tracebacks.

---

## Verification Checklist

Before restart:

- [ ] Repo path exists
- [ ] Git is available
- [ ] Bot token is SET
- [ ] Admin IDs are SET
- [ ] Working tree is clean or reviewed
- [ ] Python dependency (telebot) is available
- [ ] No secrets in existing logs

After restart:

- [ ] Tmux session is RUNNING
- [ ] No secrets in new logs
- [ ] `/arabic` command works
- [ ] `/status` command works
- [ ] `/queue` command works
- [ ] `/agents` command works
- [ ] All agent detail commands work

---

## Success Criteria

- All preflight checks PASS
- Tmux session is RUNNING
- No secrets in logs
- All Telegram verification commands work
- Bot responds to admin commands

---

## Failure Signals

| Signal | Meaning | Action |
|--------|---------|--------|
| REPO=MISSING | Repo path does not exist | Verify repo path |
| GIT=MISSING | Git is not available | Install git |
| TOKEN= | Bot token is not set | Set environment variable |
| ADMINS= | Admin IDs are not set | Set environment variable |
| TREE>0 | Uncommitted changes | Review and commit or stash |
| TELEBOT=MISSING | Python dependency missing | Install pyTelegramBotAPI |
| tmux session NOT RUNNING | Bot failed to start | Check logs for errors |
| Secrets in logs | Token exposed | Revoke token, investigate |
| Telegram command fails | Bot not responding | Check logs, restart |

---

## Failure Modes

### F1: Bot Exits Because Token Is Not Set

| Field | Value |
|-------|-------|
| **Symptom** | `ERROR: ZILFIT_TELEGRAM_BOT_TOKEN is not set.` |
| **Cause** | Environment variable `ZILFIT_TELEGRAM_BOT_TOKEN` is not exported in the tmux session shell. |
| **Safe diagnosis** | Run: `[ -n "${ZILFIT_TELEGRAM_BOT_TOKEN:-}" ] && echo "SET" || echo "MISSING"` |
| **Safe fix** | Set the token in the shell before starting: `export ZILFIT_TELEGRAM_BOT_TOKEN='...'` then restart via tmux. Use `read -s` to avoid screen echo. |

### F2: Bot Exits Because Admin IDs Are Not Set

| Field | Value |
|-------|-------|
| **Symptom** | `ERROR: ZILFIT_TELEGRAM_ADMIN_IDS is not set.` |
| **Cause** | Environment variable `ZILFIT_TELEGRAM_ADMIN_IDS` is not exported. |
| **Safe diagnosis** | Run: `[ -n "${ZILFIT_TELEGRAM_ADMIN_IDS:-}" ] && echo "SET" || echo "MISSING"` |
| **Safe fix** | Set admin IDs: `export ZILFIT_TELEGRAM_ADMIN_IDS='123456789'` then restart. |

### F3: Tmux Says "No Server Running"

| Field | Value |
|-------|-------|
| **Symptom** | `no server running on /tmp/tmux-...` |
| **Cause** | tmux daemon is not running or the socket is stale. |
| **Safe diagnosis** | Run: `tmux list-sessions 2>&1` |
| **Safe fix** | Start tmux fresh: `tmux new -d -s zilfit-bot 'bash telegram_bot/run.sh'`. If tmux itself needs repair: `tmux kill-server` then restart. |

### F4: Telegram Commands Return Old Behavior

| Field | Value |
|-------|-------|
| **Symptom** | `/agents` returns old English format instead of compact Arabic dashboard. |
| **Cause** | Bot process is still running with old code. Changes were committed but bot was not restarted. |
| **Safe diagnosis** | Check tmux session uptime: `tmux capture-pane -t zilfit-bot -p | head -5` — look for the start timestamp. |
| **Safe fix** | Stop old session: `tmux kill-session -t zilfit-bot`. Restart: `tmux new -d -s zilfit-bot 'bash telegram_bot/run.sh'`. Verify with `/arabic` then `/agents`. |

### F5: /agents Too Long or Truncated

| Field | Value |
|-------|-------|
| **Symptom** | Telegram message is cut off (exceeds 4096 characters). |
| **Cause** | Dashboard output exceeds Telegram's message limit. |
| **Safe diagnosis** | Check output length locally. |
| **Safe fix** | If length > 3500, reduce signal extraction limits. |

### F6: Dirty Working Tree Before Restart

| Field | Value |
|-------|-------|
| **Symptom** | `git status --short` shows uncommitted changes. |
| **Cause** | Incomplete work was not committed before restart attempt. |
| **Safe diagnosis** | Run: `git status --short` and review each changed file. |
| **Safe fix** | Review changes. Commit approved changes: `git add <files> && git commit -m "..."`. Stash unapproved changes: `git stash`. Then restart. Never restart with unknown dirty files. |

### F7: Accidental Secret Exposure

| Field | Value |
|-------|-------|
| **Symptom** | Token or admin ID appears in logs, Telegram output, commit diff, or report. |
| **Cause** | Debug code, `print()` statement, or misconfigured logging output secret values. |
| **Safe diagnosis** | Search for patterns: `grep -riE 'TOKEN|SECRET|API_KEY' reports/ logs/ telegram_bot/` (in file contents, not variable names). |
| **Safe fix** | **IMMEDIATE**: Revoke the exposed token via BotFather. Generate a new one. Remove the exposed value from all outputs, logs, and commits (`git reset --soft` if not yet pushed). Patch the code that printed it. Restart with new token. |

---

## Arabic Report Template

```markdown
## تقرير إعادة تشغيل البوت — {date}

### ما تم إنجازه
تم إعادة تشغيل بوت Telegram بنجاح

### فحوصات ما قبل الإعادة
- REPO: {OK/MISSING}
- GIT: {OK/MISSING}
- TOKEN: {SET/MISSING}
- ADMINS: {SET/MISSING}
- TREE: {count} uncommitted change(s)
- TELEBOT: {OK/MISSING}

### حالة الجلسة
- tmux session: {RUNNING/NOT RUNNING}
- Secrets in log: {OK/FOUND}

### التحقق من Telegram
- /arabic: {PASS/FAIL}
- /status: {PASS/FAIL}
- /queue: {PASS/FAIL}
- /agents: {PASS/FAIL}

### المخاطر
{risks identified in Arabic}

### القرار المطلوب من سلطان
{decisions needed in Arabic}

### الخطوة التالية
{next recommended action in Arabic}
```

---

## Appendix: Cross-Reference

| Document | Purpose | Location |
|----------|---------|----------|
| TELEGRAM_BOT_OPERATIONS_RUNBOOK.md | Complete operations guide | `governance/TELEGRAM_BOT_OPERATIONS_RUNBOOK.md` |
| TELEGRAM_CONTROL_ROOM_V1.md | Bot design and architecture | `governance/TELEGRAM_CONTROL_ROOM_V1.md` |
| SOUL.md | Hermes identity and boundaries | `/root/hermes/zilfit-ip-core/SOUL.md` |

---

*Document ends. Phase C2 — foundation implementation. No code changes. No production impact.*

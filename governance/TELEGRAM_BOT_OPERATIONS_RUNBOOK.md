# ZILFIT Telegram Bot — Operations Runbook

**Document:** TELEGRAM_BOT_OPERATIONS_RUNBOOK.md  
**Version:** 1.0  
**Phase:** B5 — Operations & Safety Documentation  
**Date:** 2026-05-09  
**Author:** Z-Ops  
**Parent documents:** governance/ZILFIT_AGENT_ROLES.md, governance/TELEGRAM_CONTROL_ROOM_V1.md  
**Status:** Draft — pending Sultan approval  

---

## Purpose

The ZILFIT Telegram bot is the primary mobile command interface for Sultan and authorized administrators to monitor and control the internal AI team operating system. It provides:

- **Read-only visibility** into repository health, agent status, test results, research pipeline, and claims compliance.
- **Safe task execution** via the `/qwen` bridge with classification, approval, and audit logging.
- **Scheduled Arabic reports** 4× per day (UTC 08:00, 12:00, 16:00, 21:00).

The bot operates entirely in userland (tmux session), uses polling (no webhook), and enforces strict admin allowlist and command safety boundaries.

**No external orchestration. No cloud agents. No paid resources. All local.**

---

## Current Safe Commands

All commands are read-only by default. Write commands require `/qwen` → `/approve` two-phase approval.

### 📊 Dashboard & Monitoring

| Command | Description | Safety |
|---------|-------------|--------|
| `/status` | Git branch, HEAD, working tree CLEAN/DIRTY | Read-only |
| `/agents` | Compact Arabic overview — all 8 agents, one line each | Read-only |
| `/agents_product` | Z-Product detail: status, task, paths, escalation rules | Read-only |
| `/agents_design` | Z-Design detail: status, task, paths, escalation rules | Read-only |
| `/agents_qa` | Z-QA detail: status, task, paths, escalation rules | Read-only |
| `/agents_ops` | Z-Ops detail: status, task, paths, escalation rules | Read-only |
| `/agents_research` | Z-Research detail: status, task, paths, escalation rules | Read-only |
| `/agents_claims` | Z-Claims detail: status, task, paths, escalation rules | Read-only |
| `/agents_cad` | Z-CAD detail (future): status, task, paths, escalation rules | Read-only |
| `/agents_sim` | Z-Sim detail (future): status, task, paths, escalation rules | Read-only |

### 📋 Queue & Approval

| Command | Description | Safety |
|---------|-------------|--------|
| `/queue` | Show pending approval items | Read-only |
| `/qwen <task>` | Propose a task for classification and review | Classified + audited |
| `/approve <id>` | Execute an approved pending command | Approval required |
| `/cancel <id>` | Cancel a pending command | Approval required |

### 🌐 Language

| Command | Description | Safety |
|---------|-------------|--------|
| `/arabic` | Force Arabic output for session | Session state |
| `/english` | Force English output for session | Session state |

### ℹ️ Other

| Command | Description | Safety |
|---------|-------------|--------|
| `/help` | List all commands | Read-only |
| `/start` | Same as /help | Read-only |
| `/nightly` | Latest nightly check result | Read-only |
| `/tests` | Run all shell tests, show PASS/FAIL | Read-only (runs test suite) |
| `/research` | Autopull research stats | Read-only |
| `/claims` | Forbidden medical term scan | Read-only |
| `/demo` | List demo files | Read-only |
| `/report` | Full Arabic daily report (all sections) | Read-only |

---

## Secret Handling Rules

**These rules are non-negotiable and apply to all bot code, scripts, reports, and documentation.**

1. **Never print `ZILFIT_TELEGRAM_BOT_TOKEN`** — the bot token must never appear in any output, log, report, Telegram message, or file in the repository.

2. **Never print raw env/auth/token values** — any environment variable containing `TOKEN`, `SECRET`, `KEY`, `PASSWORD`, or `AUTH` must never be displayed in cleartext.

3. **Never paste tokens into visible shell commands** — do not use `echo $ZILFIT_TELEGRAM_BOT_TOKEN`, `env | grep TOKEN`, or similar commands in any context visible to the user.

4. **Use `read -s` for manual token entry** — if a human must enter a bot token manually, use:
   ```bash
   read -s -p "Bot token: " ZILFIT_TELEGRAM_BOT_TOKEN
   export ZILFIT_TELEGRAM_BOT_TOKEN
   ```

5. **Do not save secrets in repo files** — no `.env` files in the repo, no token files, no secret configs. Secrets must only exist in the runtime environment.

6. **Do not include secrets in reports, logs, screenshots, commits, or Telegram output** — audit logs, daily reports, quality gates, and Telegram messages must never contain token values or admin IDs in raw form.

7. **If a token is exposed, revoke and regenerate** — the recommended action is:
   - Revoke the current token via [@BotFather](https://t.me/BotFather) immediately.
   - Generate a new token.
   - Update the environment variable.
   - Restart the bot.
   - Do not investigate by printing the old token.

---

## Preflight Checks

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
echo "TELEBOT: $( python3 -c 'import telebot; print(\"OK\")' 2>/dev/null || echo 'MISSING' )"
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

---

## Safe Restart Procedure

Follow this procedure **in order**. Do not skip steps.

### Step 1: Check repo path

```bash
[ -d /root/hermes/zilfit-ip-core ] && echo "Repo: OK" || echo "Repo: MISSING"
```

If MISSING: verify the repo path. Do not proceed.

### Step 2: Check git status

```bash
cd /root/hermes/zilfit-ip-core && git status --short
```

If there are uncommitted changes, review them. Do not restart if the working tree is dirty and changes are unreviewed.

### Step 3: Check env presence (without printing values)

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

### Step 4: Stop existing bot (if running)

```bash
# Check if tmux session exists
tmux has-session -t zilfit-bot 2>/dev/null && echo "Session exists" || echo "No session"

# If it exists, kill it
tmux kill-session -t zilfit-bot 2>/dev/null && echo "Session stopped" || echo "No session to stop"
```

### Step 5: Restart bot in tmux

```bash
cd /root/hermes/zilfit-ip-core
tmux new -d -s zilfit-bot 'bash telegram_bot/run.sh'
```

The `-d` flag starts the session detached (in background).

### Step 6: Verify tmux session

```bash
tmux has-session -t zilfit-bot && echo "tmux session: RUNNING" || echo "tmux session: NOT RUNNING"
```

If NOT RUNNING: check logs in the next step.

### Step 7: Verify logs do not show secrets

```bash
# Check the bot's tmux log for any token-like patterns
tmux capture-pane -t zilfit-bot -p 2>/dev/null | grep -iE 'TOKEN=|SECRET|API_KEY' || echo "No secrets in log: OK"
```

If secrets are found in logs: stop the bot immediately, revoke the token via BotFather, and investigate the source.

### Step 8: Manual Telegram verification

Send these commands in Telegram to the bot:

| # | Command | Expected |
|---|---------|----------|
| 1 | `/arabic` | "تم تفعيل اللغة العربية ✅" |
| 2 | `/status` | Branch, HEAD, tree state |
| 3 | `/queue` | Queue status (empty or items) |
| 4 | `/agents` | Compact Arabic overview starting with "غرفة تحكم وكلاء ZILFIT" |
| 5 | `/agents_product` | Z-Product detail view |
| 6 | `/agents_design` | Z-Design detail view |
| 7 | `/agents_qa` | Z-QA detail view |
| 8 | `/agents_ops` | Z-Ops detail view |
| 9 | `/agents_research` | Z-Research detail view |
| 10 | `/agents_claims` | Z-Claims detail view |
| 11 | `/agents_cad` | Z-CAD detail (future) |
| 12 | `/agents_sim` | Z-Sim detail (future) |

If any command fails: capture the error output and check tmux logs for Python tracebacks.

### Step 9: Verify /qwen safety

| # | Command | Expected |
|---|---------|----------|
| 13 | `/qwen git status` | Executes immediately (read-only classification) |
| 14 | `/qwen Read-only` | Returns "مهمة ممنوعة" (forbidden — does NOT create a pending item) |
| 15 | `/queue` | Should NOT contain "Read-only" as a pending item |

---

## Failure Modes

### F1: Bot exits because token is not set

| Field | Value |
|-------|-------|
| **Symptom** | `ERROR: ZILFIT_TELEGRAM_BOT_TOKEN is not set.` |
| **Cause** | Environment variable `ZILFIT_TELEGRAM_BOT_TOKEN` is not exported in the tmux session shell. |
| **Safe diagnosis** | Run: `[ -n "${ZILFIT_TELEGRAM_BOT_TOKEN:-}" ] && echo "SET" || echo "MISSING"` |
| **Safe fix** | Set the token in the shell before starting: `export ZILFIT_TELEGRAM_BOT_TOKEN='...'` then restart via tmux. Use `read -s` to avoid screen echo. |

### F2: Bot exits because admin IDs are not set

| Field | Value |
|-------|-------|
| **Symptom** | `ERROR: ZILFIT_TELEGRAM_ADMIN_IDS is not set.` |
| **Cause** | Environment variable `ZILFIT_TELEGRAM_ADMIN_IDS` is not exported. |
| **Safe diagnosis** | Run: `[ -n "${ZILFIT_TELEGRAM_ADMIN_IDS:-}" ] && echo "SET" || echo "MISSING"` |
| **Safe fix** | Set admin IDs: `export ZILFIT_TELEGRAM_ADMIN_IDS='123456789'` then restart. |

### F3: tmux says "no server running"

| Field | Value |
|-------|-------|
| **Symptom** | `no server running on /tmp/tmux-...` |
| **Cause** | tmux daemon is not running or the socket is stale. |
| **Safe diagnosis** | Run: `tmux list-sessions 2>&1` |
| **Safe fix** | Start tmux fresh: `tmux new -d -s zilfit-bot 'bash telegram_bot/run.sh'`. If tmux itself needs repair: `tmux kill-server` then restart. |

### F4: Telegram commands return old behavior (bot not restarted)

| Field | Value |
|-------|-------|
| **Symptom** | `/agents` returns old English format instead of compact Arabic dashboard. |
| **Cause** | Bot process is still running with old code. Changes were committed but bot was not restarted. |
| **Safe diagnosis** | Check tmux session uptime: `tmux capture-pane -t zilfit-bot -p | head -5` — look for the start timestamp. |
| **Safe fix** | Stop old session: `tmux kill-session -t zilfit-bot`. Restart: `tmux new -d -s zilfit-bot 'bash telegram_bot/run.sh'`. Verify with `/arabic` then `/agents`. |

### F5: /agents too long or truncated

| Field | Value |
|-------|-------|
| **Symptom** | Telegram message is cut off (exceeds 4096 characters). |
| **Cause** | Dashboard output exceeds Telegram's message limit. In Phase B4+, the compact overview is ~800 chars, so this should not occur. If it does, a new agent source may be producing very long signals. |
| **Safe diagnosis** | Check output length locally: `python3 -c "import telegram_bot.bot as bot; r=bot.cmd_agents_ar({'repo_root':'.'}); print(len(r))"` |
| **Safe fix** | If length > 3500, reduce signal extraction limits in `_extract_signal()` (max 200 chars per field). The footer hint already guides users to detail views. |

### F6: Dirty working tree before restart

| Field | Value |
|-------|-------|
| **Symptom** | `git status --short` shows uncommitted changes. |
| **Cause** | Incomplete work was not committed before restart attempt. |
| **Safe diagnosis** | Run: `git status --short` and review each changed file. |
| **Safe fix** | Review changes. Commit approved changes: `git add <files> && git commit -m "..."`. Stash unapproved changes: `git stash`. Then restart. Never restart with unknown dirty files. |

### F7: Accidental secret exposure

| Field | Value |
|-------|-------|
| **Symptom** | Token or admin ID appears in logs, Telegram output, commit diff, or report. |
| **Cause** | Debug code, `print()` statement, or misconfigured logging output secret values. |
| **Safe diagnosis** | Search for patterns: `grep -riE 'TOKEN|SECRET|API_KEY' reports/ logs/ telegram_bot/` (in file contents, not variable names). |
| **Safe fix** | **IMMEDIATE**: Revoke the exposed token via BotFather. Generate a new one. Remove the exposed value from all outputs, logs, and commits (`git reset --soft` if not yet pushed). Patch the code that printed it. Restart with new token. |

---

## Manual Telegram Verification

After any bot restart, run this exact checklist in Telegram.

### Checklist

Send each command in order. Mark ✅ for pass, ❌ for fail.

| # | Command | Expected Result | Pass/Fail |
|---|---------|-----------------|-----------|
| 1 | `/arabic` | "تم تفعيل اللغة العربية ✅" | ☐ |
| 2 | `/status` | Branch name, HEAD hash, tree CLEAN/DIRTY | ☐ |
| 3 | `/queue` | Queue status (empty or list of items) | ☐ |
| 4 | `/agents` | Starts with "🤖 غرفة تحكم وكلاء ZILFIT", ~20 lines | ☐ |
| 5 | `/agents_product` | Z-Product detail: status, task, paths, escalation | ☐ |
| 6 | `/agents_design` | Z-Design detail: status, task, paths, escalation | ☐ |
| 7 | `/agents_qa` | Z-QA detail: status, task, paths, escalation | ☐ |
| 8 | `/agents_ops` | Z-Ops detail: status, task, paths, escalation | ☐ |
| 9 | `/agents_research` | Z-Research detail: status, task, paths, escalation | ☐ |
| 10 | `/agents_claims` | Z-Claims detail: status, task, paths, escalation | ☐ |
| 11 | `/agents_cad` | Z-CAD detail (مستقبلي): status, paths, escalation | ☐ |
| 12 | `/agents_sim` | Z-Sim detail (مستقبلي): status, paths, escalation | ☐ |

### /qwen Safety Verification

| # | Command | Expected Result | Pass/Fail |
|---|---------|-----------------|-----------|
| 13 | `/qwen git status` | Auto-executes (classified as read-only), shows git output | ☐ |
| 14 | `/qwen Read-only` | Returns "❌ مهمة ممنوعة" — does NOT create pending item | ☐ |
| 15 | `/queue` | Should NOT contain "Read-only" as a pending item | ☐ |

**Critical expectation:** `/qwen git status` is safe and read-only — it runs `git status` as a shell command via the safe read-only path. `/qwen Read-only` is classified as forbidden because it is a natural-language phrase that does not map to a safe command, and the classifier rejects it. After step 15, the queue must not contain any "Read-only" entry.

---

## Commit Safety

**These rules apply to all commits in the ZILFIT repository.**

1. **Never commit before `git status` review** — always run `git status --short` and review every changed file. Understand what each change does before adding it.

2. **Commit only expected files** — the commit should contain only the files relevant to the current phase's scope. Do not accidentally include debug files, temp files, or unrelated changes.

3. **No production/main merge without Sultan approval** — never merge to `main` branch without explicit Sultan approval. All work must be on feature/phase branches.

4. **No deletion without Sultan approval** — never commit a file deletion without explicit Sultan approval. Deletions are irreversible and may remove in-progress work.

5. **Arabic implementation report required before commit** — before any commit, produce a short Arabic report summarizing:
   - ما تم إنجازه (what was done)
   - الملفات المعدّلة (files changed)
   - المخاطر (risks)
   - نتائج التحقق (verification results)
   - هل من الآمن الـ commit (whether commit is safe)

6. **Do not commit secrets** — verify with `git diff --staged` that no token, key, or secret is included in the commit.

7. **Review diff before commit** — run `git diff` and read every line. Ensure no debug code, print statements, or temporary changes are committed.

---

## Future Phase B6 Candidates

**Design only. No implementation in B5.**

The following improvements are proposed for future Phase B6. Each is a design note, not a committed feature.

| Candidate | Description | Priority |
|-----------|-------------|----------|
| **Safer startup preflight in run.sh** | Add automatic preflight checks to `telegram_bot/run.sh` that verify TOKEN=SET, ADMINS=SET, and repo exists before launching Python. Log "PASS/FAIL" without printing values. | High |
| **Optional `/ops_restart_request` command** | Design a read-only command that signals Z-Ops to prepare a restart. The command would verify env vars, git status, and tmux state, then return a "ready to restart" or "blocked" status. Does not restart the bot itself. | Medium |
| **Agent health heartbeat file** | Each agent writes a heartbeat file (e.g., `reports/ops/heartbeat_{agent}.json`) with timestamp and status. The `/agents` dashboard reads these as additional status signals. | Medium |
| **Local action audit log redaction** | Ensure `reports/telegram_actions/actions_*.jsonl` never contains sensitive data. Add a redaction layer that scrubs token-like patterns before writing log entries. | High |
| **Shorter `/agents` summary if Telegram truncates** | If the compact overview still approaches the 4096-char limit, provide a fallback "ultra-compact" mode showing only agent names and status icons (no filenames). | Low |

**None of these are implemented in B5.** B5 is documentation and runbook only.

---

## Document Changelog

| Date | Phase | Change |
|------|-------|--------|
| 2026-05-09 | B5 | Initial creation — operations runbook, safety rules, restart procedure, failure modes, verification checklist |

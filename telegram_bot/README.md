# ZILFIT Telegram Command Center v2

Read-only mobile control + safe Qwen execution bridge + Arabic scheduled reports.

## Architecture

- Single Python 3 script, polling mode (no webhook, no SSL).
- Runs in userland (tmux session), not systemd or cron.
- Read-only by default. Write/execute commands need two-phase approval.
- Background scheduler sends Arabic reports 4x/day.

## Security

- **Admin allowlist only** — `ZILFIT_TELEGRAM_ADMIN_IDS` (comma-separated Telegram user IDs).
- Unknown users receive zero response (not even "unauthorized").
- Bot token from environment variable only — never stored in files or committed.
- No public group/supergroup access by default.

### Forbidden commands (hard-blocked)

These patterns are **never** allowed, even with `/approve`:
- `.env`, `API_KEY`, `SECRET`, `TOKEN` references
- `rm -rf`, `rm -r`, destructive file operations
- `chmod 777`
- `curl | bash`, `wget | sh` (pipe to shell)
- `systemctl`, `crontab -e/-r`, `shutdown`, `reboot`, `killall`, `pkill`
- `sudo`, `pip install`, `apt-get`, `yum`
- Anything touching production tunnels or billing

### Safe commands (auto-executed)

Read-only commands execute immediately without approval:
- `git status`, `git log`, `git branch`, `git show`, `git diff`, `git tag`
- `ls`, `find`, `cat`, `grep`, `rg`, `sed -n`, `tail`, `head`, `wc`
- `python3 tests/*`, `bash tests/*`
- `echo`, `date`, `whoami`, `pwd`, `uname`, `hostname`, `uptime`, `df`, `tree`, `stat`, `file`, `diff`

### Requiring approval

Any command not in the safe list but not forbidden (e.g. `git checkout`, `mkdir`, `cp`) requires:
1. `/qwen <command>` → proposes the command with an ID
2. `/approve <id>` → executes it
3. `/cancel <id>` → cancels it

## Setup

1. Create a bot via [@BotFather](https://t.me/BotFather) on Telegram. Get the token.
2. Find your Telegram user ID (send a message to [@userinfobot](https://t.me/userinfobot)).
3. Set environment variables:
   ```bash
   export ZILFIT_TELEGRAM_BOT_TOKEN='123456:ABC-DEF...'
   export ZILFIT_TELEGRAM_ADMIN_IDS='987654321'
   ```
4. Install dependency:
   ```bash
   pip3 install pyTelegramBotAPI
   ```
5. Run:
   ```bash
   # Foreground test
   bash telegram_bot/run.sh

   # Or in tmux for persistent operation (recommended)
   tmux new -s zilfit-bot 'bash telegram_bot/run.sh'
   ```

## Commands

### 📊 Reports (read-only)

| Command | Description |
|---------|-------------|
| `/status` | Git branch, HEAD commit, working tree clean/dirty |
| `/nightly` | Latest nightly check result |
| `/tests` | Run all shell tests, report PASS/FAIL |
| `/agents` | Agent roles, active projects, last run times |
| `/research` | Autopull research stats |
| `/claims` | Forbidden medical/clinical term scan |
| `/demo` | List demo files |
| `/report` | Full Arabic daily report (immediate, all sections) |

### 🔧 Qwen Bridge (safe execution)

| Command | Description |
|---------|-------------|
| `/qwen <task>` | Propose a command/task for review |
| `/queue` | Show pending approval items |
| `/approve <id>` | Execute an approved pending command |
| `/cancel <id>` | Cancel a pending command |

### 🌐 Language

| Command | Description |
|---------|-------------|
| `/arabic` | Force Arabic output for your session |
| `/english` | Force English output for your session |

### ℹ️ Info

| Command | Description |
|---------|-------------|
| `/help` | Command list |
| `/start` | Same as /help |

## Scheduled Reports

Arabic reports are sent automatically **4 times per day** (UTC):

| Time (UTC) | Time (AST / UTC+3) |
|------------|---------------------|
| 08:00 | 11:00 |
| 12:00 | 15:00 |
| 16:00 | 19:00 |
| 21:00 | 00:00 |

Each report includes:
- Branch and HEAD
- Working tree CLEAN/DIRTY
- Latest nightly result
- Tests summary
- Agents status
- Research/autopull status
- Claims/compliance scan
- Recommended next action

Reports are sent to **all admin IDs** automatically.

## Environment Variables

| Variable | Required | Format |
|----------|----------|--------|
| `ZILFIT_TELEGRAM_BOT_TOKEN` | Yes | Bot token from @BotFather |
| `ZILFIT_TELEGRAM_ADMIN_IDS` | Yes | Comma-separated Telegram user IDs |
| `ZILFIT_REPO_ROOT` | No | Path to repo (default: `/root/hermes/zilfit-ip-core`) |

## Audit Log

Every Qwen bridge action is logged to:
```
reports/telegram_actions/actions_YYYYMMDD.jsonl
```

Each line is a JSON object with: event type, timestamp, user ID, task, command, result.

## Boundaries

- **Engineering-only.** No medical, diagnostic, therapeutic, clinical, pain, disease, or treatment claims.
- **Read-only by default.** Write/execute commands need `/qwen` → `/approve` flow.
- **No destructive commands.** `.env`, `rm -rf`, `chmod 777`, `curl|bash` are hard-blocked.
- **No systemd, no cron changes.** Bot runs in tmux with internal scheduler.

## Dependencies

- Python 3.7+
- `pyTelegramBotAPI>=4.15`
- No other packages required (scheduler uses stdlib `threading` + `time`)

# ZILFIT Telegram Command Center v1

Read-only mobile control for ZILFIT/Hermes operations via Telegram.

## Architecture

- Single Python 3 script, polling mode (no webhook, no SSL).
- Runs in userland (tmux session), not systemd or cron.
- Zero write operations — reads only git status, reports, and research files.

## Security

- **Admin allowlist only** — `ZILFIT_TELEGRAM_ADMIN_IDS` (comma-separated Telegram user IDs).
- Unknown users receive zero response (not even "unauthorized").
- Bot token from environment variable only — never stored in files or committed.
- No public group/supergroup access by default.

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

   # Or in tmux for persistent operation
   tmux new -s zilfit-bot 'bash telegram_bot/run.sh'
   ```

## Commands

| Command | Description |
|---------|-------------|
| `/status` | Git branch, HEAD commit, working tree clean/dirty |
| `/nightly` | Latest nightly check result (timestamp, branch, test status) |
| `/tests` | Run all 38 shell tests, report PASS/FAIL/TOTAL |
| `/agents` | Agent roles, active projects, last nightly/quality/agent timestamps |
| `/research` | Autopull research stats (count, date, API errors, status) |
| `/claims` | Forbidden medical/clinical term scan across reports |
| `/demo` | List demo HTML files and reference patch |
| `/help` | Command list |

## Environment Variables

| Variable | Required | Format |
|----------|----------|--------|
| `ZILFIT_TELEGRAM_BOT_TOKEN` | Yes | Bot token from @BotFather |
| `ZILFIT_TELEGRAM_ADMIN_IDS` | Yes | Comma-separated Telegram user IDs |
| `ZILFIT_REPO_ROOT` | No | Path to repo (default: `/root/hermes/zilfit-ip-core`) |

## Boundaries

- **Engineering-only.** No medical, diagnostic, therapeutic, clinical, pain, disease, or treatment claims.
- **Read-only v1.** No git write, no file creation, no service control, no cron changes.
- **No destructive commands.** `/delete`, `/reset`, `/merge main` are not implemented.

## v2 Planned

- Two-phase approval flow for safe write commands (propose → confirm with nonce).
- Per-command allowlists.
- Audit log (`telegram_bot/audit_log.jsonl`).
- Optional daily summary push (cron-driven, read-then-send only).

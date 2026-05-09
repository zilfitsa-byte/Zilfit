#!/usr/bin/env bash
# ZILFIT Telegram Command Center — Launch Script
# Run from repo root: bash telegram_bot/run.sh
# Or from tmux: tmux new -s zilfit-bot 'bash telegram_bot/run.sh'
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
cd "$REPO_ROOT"

echo "⬡ ZILFIT Telegram Command Center v1"
echo "===================================="

# Validate required env vars
if [ -z "${ZILFIT_TELEGRAM_BOT_TOKEN:-}" ]; then
  echo "ERROR: ZILFIT_TELEGRAM_BOT_TOKEN is not set."
  echo "  export ZILFIT_TELEGRAM_BOT_TOKEN='your-bot-token-here'"
  exit 1
fi

if [ -z "${ZILFIT_TELEGRAM_ADMIN_IDS:-}" ]; then
  echo "ERROR: ZILFIT_TELEGRAM_ADMIN_IDS is not set."
  echo "  export ZILFIT_TELEGRAM_ADMIN_IDS='123456789'"
  exit 1
fi

# Check Python dependency
if ! python3 -c "import telebot" 2>/dev/null; then
  echo "Installing dependency: pyTelegramBotAPI"
  pip3 install pyTelegramBotAPI
fi

echo "Repo:     $REPO_ROOT"
echo "Admins:   $ZILFIT_TELEGRAM_ADMIN_IDS"
echo "Starting bot…"
echo ""

python3 telegram_bot/bot.py

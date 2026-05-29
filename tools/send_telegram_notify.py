#!/usr/bin/env python3
"""
ZILFIT Telegram Notification Utility

Minimal utility to send Telegram messages for:
  - Daily brief delivery
  - Agent reports
  - QA alerts
  - Claims-safety warnings

Usage:
  # Safe test message
  python tools/send_telegram_notify.py --test

  # Custom message
  python tools/send_telegram_notify.py --message "Z-QA: all tests passed"

Environment variables (required):
  TELEGRAM_BOT_TOKEN  — Bot token from @BotFather
  TELEGRAM_CHAT_ID     — Target chat ID

Exit codes:
  0  — Message sent successfully
  1  — Missing credentials or network error
  2  — Validation / usage error
"""

import json
import os
import sys
import urllib.request
import urllib.error
import urllib.parse
import argparse


def get_credentials():
    """Read Telegram credentials from environment variables only."""
    token = os.environ.get("TELEGRAM_BOT_TOKEN", "").strip()
    chat_id = os.environ.get("TELEGRAM_CHAT_ID", "").strip()

    if not token:
        print("ERROR: TELEGRAM_BOT_TOKEN environment variable is not set.", file=sys.stderr)
        print("  Export it before running this script:", file=sys.stderr)
        print("    export TELEGRAM_BOT_TOKEN='<your-bot-token>'", file=sys.stderr)
        return None, None
    if not chat_id:
        print("ERROR: TELEGRAM_CHAT_ID environment variable is not set.", file=sys.stderr)
        print("  Export it before running this script:", file=sys.stderr)
        print("    export TELEGRAM_CHAT_ID='<your-chat-id>'", file=sys.stderr)
        return None, None

    return token, chat_id


def send_message(token, chat_id, text, parse_mode="Markdown"):
    """Send a text message via Telegram Bot API.

    Returns (True, response_data) on success or (False, error_string) on failure.
    """
    url = f"https://api.telegram.org/bot{token}/sendMessage"
    body = urllib.parse.urlencode({
        "chat_id": chat_id,
        "text": text,
        "parse_mode": parse_mode,
    }).encode("utf-8")

    req = urllib.request.Request(url, data=body, method="POST")
    req.add_header("Content-Type", "application/x-www-form-urlencoded")

    try:
        with urllib.request.urlopen(req, timeout=15) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            if data.get("ok"):
                return True, data
            else:
                desc = data.get("description", "Unknown error")
                return False, f"Telegram API error: {desc}"
    except urllib.error.HTTPError as e:
        return False, f"HTTP error {e.code}: {e.reason}"
    except urllib.error.URLError as e:
        return False, f"Network error: {e.reason}"
    except Exception as e:
        return False, f"Unexpected error: {e}"


def build_test_message():
    """Build a safe test message identifying this as ZILFIT infrastructure."""
    return (
        "🟢 *ZILFIT — Telegram Notify Test*\n\n"
        "This is a safe test message.\n"
        "No production content. Infrastructure check only.\n\n"
        "_Future uses_: daily brief, agent reports, QA alerts, claims warnings."
    )


def main():
    parser = argparse.ArgumentParser(
        description="ZILFIT Telegram notification utility"
    )
    parser.add_argument(
        "--test", action="store_true",
        help="Send a safe test message"
    )
    parser.add_argument(
        "--message", type=str, default=None,
        help="Send a custom message"
    )
    args = parser.parse_args()

    if not args.test and args.message is None:
        parser.print_help()
        print("\nNo action specified. Use --test or --message.", file=sys.stderr)
        return 2

    token, chat_id = get_credentials()
    if token is None:
        return 1

    if args.test:
        text = build_test_message()
    else:
        text = args.message

    ok, result = send_message(token, chat_id, text)
    if ok:
        print("OK: Telegram message sent successfully.")
        return 0
    else:
        print(f"FAIL: {result}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())

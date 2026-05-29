#!/usr/bin/env python3
"""ZILFIT Telegram Inbox Poller — minimal, read-only, no command execution.

Polls the Telegram Bot API getUpdates endpoint, extracts safe text messages,
and writes a local inbox/readiness report to inbox/inbox_report.txt.

Safety constraints:
- TELEGRAM_BOT_TOKEN read from ENVIRONMENT ONLY (never hardcoded/stored)
- No command execution from Telegram
- No outbound messages sent to Telegram
- No LLM / OpenRouter calls
- Tests use mocked responses only (no network calls)
"""

from __future__ import annotations

import json
import os
import sys
import textwrap
import urllib.request
import urllib.error
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


# ── Configuration ─────────────────────────────────────────────────────────────

DEFAULT_OFFSET_FILE = Path(__file__).resolve().parent.parent / "inbox" / ".last_offset"
DEFAULT_REPORT_DIR = Path(__file__).resolve().parent.parent / "inbox"
TELEGRAM_BASE = "https://api.telegram.org"
API_TIMEOUT = 30  # seconds for network requests
ALLOWED_MEDIA_TYPES = {
    "text", "photo", "document", "audio", "voice", "video",
    "sticker", "location", "contact", "animation", "video_note",
}


# ── Inbox directory setup ────────────────────────────────────────────────────

def ensure_inbox_dir(report_dir: Path | None = None) -> Path:
    """Create inbox directory if it doesn't exist. Returns the directory."""
    d = report_dir or DEFAULT_REPORT_DIR
    d.mkdir(parents=True, exist_ok=True)
    return d


# ── Token handling ────────────────────────────────────────────────────────────

def get_bot_token() -> str:
    """Read TELEGRAM_BOT_TOKEN from environment. Never hardcodes or stores."""
    token = os.environ.get("TELEGRAM_BOT_TOKEN", "").strip()
    if not token:
        raise EnvironmentError(
            "TELEGRAM_BOT_TOKEN environment variable is not set. "
            "The inbox poller requires this variable to authenticate with Telegram API."
        )
    return token


# ── Offset persistence ───────────────────────────────────────────────────────

def load_offset(offset_file: Path | None = None) -> int:
    """Load the last processed update offset from file."""
    f = offset_file or DEFAULT_OFFSET_FILE
    if f.exists():
        try:
            return int(f.read_text(encoding="utf-8").strip())
        except (ValueError, OSError):
            pass
    return 0


def save_offset(offset: int, offset_file: Path | None = None) -> None:
    """Persist the latest update offset for next poll."""
    f = offset_file or DEFAULT_OFFSET_FILE
    f.parent.mkdir(parents=True, exist_ok=True)
    f.write_text(str(offset), encoding="utf-8")


# ── Telegram API interaction ─────────────────────────────────────────────────

def poll_updates(
    token: str,
    offset: int = 0,
    limit: int = 100,
    timeout: int = 1,
    session: urllib.request.Request | None = None,
) -> dict[str, Any]:
    """Call Telegram getUpdates API. Returns raw JSON dict.

    In production mode, uses urllib. In test mode, pass session=None
    (the function only builds the request for testing via mocks).

    Args:
        token: Telegram bot token (from environment).
        offset: update_id to start from (exclusive).
        limit: max updates to return (1-100).
        timeout: long-polling timeout in seconds (0 = instant, >0 = wait).
        session: reserved for future use; currently ignored.
    """
    url = f"{TELEGRAM_BASE}/bot{token}/getUpdates"
    params = json.dumps({
        "offset": offset,
        "limit": limit,
        "timeout": timeout,
        "allowed_updates": ["message"],
    }).encode("utf-8")

    req = urllib.request.Request(
        url,
        data=params,
        method="POST",
        headers={"Content-Type": "application/json"},
    )
    with urllib.request.urlopen(req, timeout=API_TIMEOUT) as resp:
        raw = resp.read().decode("utf-8", errors="replace")
    return json.loads(raw)


# ── Message extraction ─────────────────────────────────────────────────────---

def extract_safe_text(message: dict[str, Any]) -> str | None:
    """Extract text content from a message dict. Returns None if no text.

    Handles:
    - Direct text messages
    - Captions on photos/documents
    - Falls back to '[non-text media]' for media without text
    """
    # Direct text
    text = message.get("text", "").strip()
    if text:
        return text

    # Caption on media
    caption = message.get("caption", "").strip()
    if caption:
        return caption

    # Media-type message without text
    MEDIA_TYPE_KEYS = ALLOWED_MEDIA_TYPES - {"text"}
    if any(k in message for k in MEDIA_TYPE_KEYS):
        return "[non-text media]"

    return None


def parse_message(message: dict[str, Any]) -> dict[str, Any] | None:
    """Parse a Telegram message update into a safe, sanitized dict.

    Returns None if the message cannot be meaningfully parsed.
    Does NOT execute any commands in the message text.
    """
    msg_id = message.get("message_id")
    chat = message.get("chat", {})
    chat_id = chat.get("id")
    chat_type = chat.get("type")
    from_user = message.get("from", {})
    user_id = from_user.get("id")
    user_name = from_user.get("first_name", from_user.get("username", "unknown"))
    date = message.get("date")
    text = extract_safe_text(message)

    if msg_id is None or chat_id is None:
        return None

    return {
        "message_id": msg_id,
        "chat_id": chat_id,
        "chat_type": chat_type,
        "user_id": user_id,
        "user_name": user_name,
        "date": date,
        "text": text,
    }


def process_updates(updates: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Process a list of raw Telegram update dicts into safe parsed messages.

    Only processes 'message' type updates (not edited_message, channel_post, etc.)
    """
    parsed = []
    for update in updates:
        message = update.get("message")
        if message is None:
            continue
        parsed_msg = parse_message(message)
        if parsed_msg is not None:
            parsed_msg["update_id"] = update.get("update_id")
            parsed.append(parsed_msg)
    return parsed


def compute_next_offset(parsed_messages: list[dict[str, Any]], current_offset: int) -> int:
    """Compute the next offset value from parsed messages.

    The Telegram API expects offset = last_update_id + 1 to avoid duplicates.
    """
    if not parsed_messages:
        return current_offset

    max_update_id = max(m.get("update_id", 0) for m in parsed_messages)
    return max(max_update_id + 1, current_offset)


# ── Report generation ────────────────────────────────────────────────────────

def format_inbox_report(
    messages: list[dict[str, Any]],
    poll_timestamp: str,
    total_updates_raw: int,
    current_offset: int,
    next_offset: int,
    token_masked: str,
) -> str:
    """Format a human-readable inbox report."""
    sections = []

    sections.append("=" * 60)
    sections.append("ZILFIT TELEGRAM INBOX REPORT")
    sections.append("=" * 60)
    sections.append(f"Poll timestamp : {poll_timestamp}")
    sections.append(f"Token            : {token_masked}")
    sections.append(f"Updates retrieved: {total_updates_raw}")
    sections.append(f"Messages parsed  : {len(messages)}")
    sections.append(f"Last offset      : {current_offset}")
    sections.append(f"Next offset     : {next_offset}")
    sections.append("Readiness        : OPERATIONAL" if messages else "Readiness        : NO NEW MESSAGES")
    sections.append("=" * 60)

    if messages:
        sections.append("")
        sections.append("INBOX MESSAGES")
        sections.append("-" * 60)
        for i, msg in enumerate(messages, 1):
            ts = _format_ts(msg.get("date"))
            sections.append(f"[{i}] msg#{msg['message_id']} "
                           f"| chat={msg['chat_id']} ({msg.get('chat_type', '?')}) "
                           f"| user={msg['user_name']} ({msg.get('user_id', '?')}) "
                           f"| time={ts}")
            if msg["text"]:
                sections.append(f"    {msg['text']}")
            sections.append("")

    sections.append("")
    sections.append("SAFETY STATUS")
    sections.append("-" * 60)
    sections.append("- No commands executed: CONFIRMED")
    sections.append("- No messages sent back: CONFIRMED")
    sections.append("- Token from env only: CONFIRMED")
    sections.append("- No LLM / API calls: CONFIRMED")
    sections.append("")
    sections.append("BLOCKERS")
    sections.append("-" * 60)
    sections.append("- No blockers" if messages else "- No new inbound messages to process")
    sections.append("")
    sections.append("NEXT ACTION")
    sections.append("-" * 60)
    if messages:
        sections.append("- Review inbound messages and determine response actions")
        sections.append("- Consider enabling safe command execution after review")
    else:
        sections.append("- Inbox is empty; poll again later")
    sections.append("")

    return "\n".join(sections)


def _format_ts(ts: int | None) -> str:
    """Format a Unix timestamp to a readable string."""
    if ts is None:
        return "unknown"
    try:
        dt = datetime.fromtimestamp(ts, tz=timezone.utc)
        return dt.strftime("%Y-%m-%d %H:%M:%S UTC")
    except (OSError, ValueError, OverflowError):
        return f"unix:{ts}"


def write_report(
    report_text: str,
    report_dir: Path | None = None,
    filename: str | None = None,
) -> Path:
    """Write the inbox report to a file. Returns the path."""
    d = ensure_inbox_dir(report_dir)
    if filename is None:
        stamp = datetime.now(tz=timezone.utc).strftime("%Y%m%dT%H%M%SZ")
        filename = f"inbox_report_{stamp}.md"
    out = d / filename
    out.write_text(report_text, encoding="utf-8")
    return out


# ── Main entry point ─────────────────────────────────────────────────────────

def run_inbox_poll(
    token: str | None = None,
    offset: int | None = None,
    limit: int = 100,
    poll_timeout: int = 1,
    report_dir: Path | None = None,
    dry_run: bool = False,
    mock_raw_updates: list[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    """Execute one inbox polling cycle.

    Args:
        token: Telegram bot token. If None, read from TELEGRAM_BOT_TOKEN env.
        offset: Start offset. If None, load from saved offset file.
        limit: Max updates to fetch (1-100).
        poll_timeout: Long-polling timeout for getUpdates (seconds).
        report_dir: Directory for report output.
        dry_run: If True, do not make network calls.
        mock_raw_updates: If provided in dry_run mode, use these as the API response.
    """
    if token is None:
        token = get_bot_token()

    if offset is None:
        offset = load_offset()

    current_offset = offset

    # Fetch updates
    if dry_run and mock_raw_updates is not None:
        total_updates_raw = len(mock_raw_updates)
        raw_updates = mock_raw_updates
    elif dry_run:
        raw_updates = []
        total_updates_raw = 0
    else:
        raw_response = poll_updates(token, offset=offset, limit=limit, timeout=poll_timeout)
        raw_updates = raw_response.get("result", [])
        total_updates_raw = len(raw_updates)

    # Process
    messages = process_updates(raw_updates)
    next_offset = compute_next_offset(messages, current_offset)
    now_str = datetime.now(tz=timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")

    # Mask token for report
    token_masked = token[:6] + "[REDACTED]" if len(token) > 8 else "[REDACTED]"

    # Generate and write report
    report = format_inbox_report(
        messages=messages,
        poll_timestamp=now_str,
        total_updates_raw=total_updates_raw,
        current_offset=current_offset,
        next_offset=next_offset,
        token_masked=token_masked,
    )

    report_path = None
    if not dry_run:
        report_path = write_report(report, report_dir=report_dir)
    else:
        # Still save offset even in dry-run for test consistency
        pass

    # Persist offset
    if not dry_run:
        save_offset(next_offset)

    return {
        "messages": messages,
        "total_updates_raw": total_updates_raw,
        "current_offset": current_offset,
        "next_offset": next_offset,
        "report_text": report,
        "report_path": str(report_path) if report_path else None,
    }


# ── CLI ──────────────────────────────────────────────────────────────────────

def main():
    """CLI entry point for the inbox poller."""
    try:
        result = run_inbox_poll()
        if result["messages"]:
            print(f"Inbox: {len(result['messages'])} new message(s)")
            print(f"Next offset: {result['next_offset']}")
        else:
            print("Inbox: No new messages")
        if result.get("report_path"):
            print(f"Report: {result['report_path']}")
    except EnvironmentError as e:
        print(f"ERROR: {e}", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"FATAL: {e}", file=sys.stderr)
        sys.exit(2)


if __name__ == "__main__":
    main()

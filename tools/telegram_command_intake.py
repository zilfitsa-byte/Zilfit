#!/usr/bin/env python3
"""ZILFIT Telegram Command Intake — minimal classification layer.

Turns inbound Telegram messages into safe classified requests for
Hermes/ZILFIT review.  Does NOT execute commands, send messages,
or access production services.

Safety constraints:
- TELEGRAM_BOT_TOKEN read from ENVIRONMENT ONLY (never hardcoded/stored)
- No command execution from Telegram
- No outbound messages sent to Telegram
- No LLM / OpenRouter calls
- Tests use mocked responses only (no network calls)

Command mapping:
  /status      -> status_request
  /brief       -> brief_request
  /next        -> next_action_request
  /queue       -> queue_request
  any other    -> note_or_task_request
"""

from __future__ import annotations

import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

# ── Reuse existing inbox poller ───────────────────────────────────────────────
_project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _project_root not in sys.path:
    sys.path.insert(0, _project_root)

from tools.telegram_inbox import (
    process_updates,
    format_inbox_report,
    write_report,
    ensure_inbox_dir,
    extract_safe_text,
)

# ── Classification ────────────────────────────────────────────────────────────

# Allowed slash commands and their mapped request types.
_COMMAND_MAP: dict[str, str] = {
    "/status": "status_request",
    "/brief": "brief_request",
    "/next": "next_action_request",
    "/queue": "queue_request",
}

DEFAULT_REQUEST_TYPE = "note_or_task_request"
VALID_REQUEST_TYPES = set(_COMMAND_MAP.values()) | {DEFAULT_REQUEST_TYPE}


def classify_request(text: str | None) -> str:
    """Classify a message into a request type.

    If text starts with a known slash command, return the mapped type.
    Otherwise return the default (note_or_task_request).
    """
    if not text:
        return DEFAULT_REQUEST_TYPE

    stripped = text.strip()
    # Extract the first word/command token
    first_token = stripped.split()[0].lower() if stripped.split() else ""

    return _COMMAND_MAP.get(first_token, DEFAULT_REQUEST_TYPE)


def classify_messages(messages: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Take already-parsed inbox messages and add request_type to each.

    Returns a new list with an extra 'request_type' field on each message.
    """
    result = []
    for msg in messages:
        classified = {**msg}
        classified["request_type"] = classify_request(msg.get("text"))
        result.append(classified)
    return result


# ── Report generation ────────────────────────────────────────────────────────

def format_classified_report(
    classified: list[dict[str, Any]],
    poll_timestamp: str,
    summary_counts: dict[str, int],
) -> str:
    """Format a human-readable report with command classification."""
    lines = []
    lines.append("=" * 60)
    lines.append("ZILFIT COMMAND INTAKE REPORT")
    lines.append("=" * 60)
    lines.append(f"Poll timestamp   : {poll_timestamp}")
    lines.append(f"Messages received: {len(classified)}")
    lines.append("")
    lines.append("REQUEST TYPE COUNTS")
    lines.append("-" * 60)
    for req_type in sorted(summary_counts.keys()):
        lines.append(f"  {req_type}: {summary_counts[req_type]}")
    lines.append("")

    if classified:
        lines.append("CLASSIFIED MESSAGES")
        lines.append("-" * 60)
        for i, msg in enumerate(classified, 1):
            ts = _format_ts(msg.get("date"))
            lines.append(f"[{i}] msg#{msg['message_id']}")
            lines.append(f"    user         : {msg.get('user_name', '?')} ({msg.get('user_id', '?')})")
            lines.append(f"    chat         : {msg.get('chat_id', '?')} ({msg.get('chat_type', '?')})")
            lines.append(f"    request_type : {msg['request_type']}")
            lines.append(f"    text         : {msg.get('text', '') or '[empty]'}")
            lines.append(f"    time         : {ts}")
            lines.append("")

    lines.append("SAFETY STATUS")
    lines.append("-" * 60)
    lines.append("- No commands executed      : CONFIRMED")
    lines.append("- No messages sent back     : CONFIRMED")
    lines.append("- Classified for human review: CONFIRMED")
    lines.append("")
    lines.append("NEXT ACTION")
    lines.append("-" * 60)
    if classified:
        lines.append("- Review classified requests and execute approved actions")
    else:
        lines.append("- No inbound messages; poll again later")
    lines.append("")

    return "\n".join(lines)


def _format_ts(ts: int | None) -> str:
    """Format a Unix timestamp to a readable string."""
    if ts is None:
        return "unknown"
    try:
        dt = datetime.fromtimestamp(ts, tz=timezone.utc)
        return dt.strftime("%Y-%m-%d %H:%M:%S UTC")
    except (OSError, ValueError, OverflowError):
        return f"unix:{ts}"


# ── SharedDB integration ─────────────────────────────────────────────────────

def save_to_shared_db(
    classified: list[dict[str, Any]],
    db_path: str | None = None,
) -> list[dict]:
    """Save classified requests to SharedDB for human review.

    Each classified message becomes a task record with agent_name='Z-Intake'.
    Returns the list of upserted record dicts from SharedDB.
    """
    if not classified:
        return []

    try:
        from runtime.shared_db import SharedDB
    except ImportError:
        # SharedDB not available — skip silently, log to stderr
        print("WARN: SharedDB not available; skipping DB write", file=sys.stderr)
        return []

    db = SharedDB(db_path=db_path)
    now = datetime.now(tz=timezone.utc)
    results = []

    for msg in classified:
        task_id = (
            f"intake-{msg['message_id']}-{now.strftime('%Y%m%d')}"
        )
        summary_parts = [
            f"type={msg['request_type']}",
            f"user={msg.get('user_name', '?')}",
        ]
        if msg.get("text"):
            summary_parts.append(msg["text"][:200])
        summary = " | ".join(summary_parts)

        risk = "high" if msg["request_type"] == "note_or_task_request" else "low"

        rec = db.upsert(
            agent_name="Z-Intake",
            task_id=task_id,
            status="pending",
            summary=summary,
            risk_level=risk,
            next_action=f"human review: {msg['request_type']}",
        )
        results.append(rec)

    return results


# ── Main entry point ─────────────────────────────────────────────────────────

def run_classified_intake(
    raw_updates: list[dict[str, Any]],
    report_dir: Path | None = None,
    db_path: str | None = None,
    dry_run: bool = False,
) -> dict[str, Any]:
    """Execute one command intake cycle on raw Telegram updates.

    1. Parse raw updates into safe messages (reuses telegram_inbox)
    2. Classify each message into a request type
    3. Generate a classified report
    4. Save to SharedDB
    5. Write report to file (unless dry_run)

    Args:
        raw_updates: Raw Telegram update dicts (from inbox poller or mock).
        report_dir: Directory for report output. Defaults to ./inbox/.
        db_path: Path to SharedDB SQLite file. None = default.
        dry_run: If True, skip writing report to disk.

    Returns:
        Dict with messages, classified, db_records, report_path, report_text.
    """
    # Step 1: Parse
    messages = process_updates(raw_updates)

    # Step 2: Classify
    classified = classify_messages(messages)

    # Step 3: Summary counts
    summary_counts: dict[str, int] = {}
    for msg in classified:
        rt = msg["request_type"]
        summary_counts[rt] = summary_counts.get(rt, 0) + 1

    # Step 4: Generate report
    now_str = datetime.now(tz=timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")
    report_text = format_classified_report(
        classified=classified,
        poll_timestamp=now_str,
        summary_counts=summary_counts,
    )

    # Step 5: Write report (skip in dry_run)
    report_path = None
    if not dry_run:
        report_dir = report_dir or ensure_inbox_dir()
        stamp = now_str.replace(" ", "_").replace(":", "") + "Z"
        filename = f"command_intake_{stamp}.md"
        report_path = write_report(report_text, report_dir=report_dir, filename=filename)

    # Step 6: Save to SharedDB (skip in dry_run)
    db_records = []
    if not dry_run:
        db_records = save_to_shared_db(classified, db_path=db_path)

    return {
        "messages": messages,
        "classified": classified,
        "summary_counts": summary_counts,
        "db_records": db_records,
        "report_text": report_text,
        "report_path": str(report_path) if report_path else None,
    }


# ── CLI ──────────────────────────────────────────────────────────────────────

def main():
    """CLI entry point — delegates to inbox poller and classifies results."""
    print("ZILFIT Command Intake CLI — requires inbox polling to supply data.", file=sys.stderr)
    print("Use: from tools.telegram_command_intake import run_classified_intake", file=sys.stderr)
    print("Or supply raw updates to this function.", file=sys.stderr)


if __name__ == "__main__":
    main()

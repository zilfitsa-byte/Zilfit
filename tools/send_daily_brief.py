#!/usr/bin/env python3
"""
ZILFIT Daily Brief — Manual Telegram Sender

Reads the latest daily report from reports/daily/, builds a brief using
the config-driven BriefBuilder, and sends via Telegram.

Uses daily_brief_builder (BriefBuilder) for parsing and formatting —
the Telegram template and all section formatting come from
config/daily_brief_config.yaml.

Usage:
  # Dry-run: build brief but don't send
  python tools/send_daily_brief.py --dry-run

  # Send latest report as brief
  python tools/send_daily_brief.py

  # Send with custom report path
  python tools/send_daily_brief.py --report-file reports/daily/latest.md

  # Send today's brief for a specific date
  python tools/send_daily_brief.py --date 2026-05-16

Environment variables (required):
  TELEGRAM_BOT_TOKEN  — Bot token from @BotFather
  TELEGRAM_CHAT_ID     — Target chat ID

Exit codes:
  0  — Success (sent or dry-run complete)
  1  — No report found, missing credentials, or send failure
  2  — Validation / usage error
"""

import glob
import os
import re
import sys

# Add project root to path so we can import send_telegram_notify
_project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _project_root not in sys.path:
    sys.path.insert(0, _project_root)

from tools.send_telegram_notify import get_credentials, send_message
from tools.daily_brief_builder import BriefBuilder, load_config


def find_latest_report(date=None):
    """Find the most recent daily report .md file.

    If date is provided, looks for reports matching that date.
    Otherwise, returns the most recently modified .md in reports/daily/.
    """
    report_dir = os.path.join(_project_root, "reports", "daily")
    if not os.path.isdir(report_dir):
        return None, "reports/daily/ directory not found"

    if date:
        pattern = os.path.join(report_dir, f"{date}*.md")
        candidates = sorted(glob.glob(pattern), key=os.path.getmtime, reverse=True)
        if candidates:
            return candidates[0], None
        return None, f"No report found for date {date}"

    all_reports = glob.glob(os.path.join(report_dir, "*.md"))
    if not all_reports:
        return None, "No .md reports in reports/daily/"

    latest = max(all_reports, key=os.path.getmtime)
    return latest, None


def parse_report_brief(filepath, builder=None):
    """Extract key fields from a daily report using the BriefBuilder.

    Delegates parsing to BriefBuilder.build_from_report() which uses the
    config-driven extraction. Falls back to the legacy ad-hoc parser if
    the builder is not provided (for backward compatibility with existing
    tests that do not supply a builder).

    Returns a brief dict.
    """
    if builder is not None:
        return builder.build_from_report(filepath)

    # Legacy fallback for existing tests that call this function directly
    brief = {
        "date": "Unknown",
        "status": "\u2753",
        "files_touched": "N/A",
        "summary": "No summary found.",
        "risks": "No risks reported.",
        "blockers": "No blockers.",
        "next_action": "No recommendation.",
    }

    try:
        with open(filepath, "r", encoding="utf-8") as f:
            content = f.read()
    except Exception as e:
        brief["summary"] = f"Failed to read report: {e}"
        return brief

    basename = os.path.basename(filepath)
    date_match = re.match(r"(\d{4}-\d{2}-\d{2})", basename)
    if date_match:
        brief["date"] = date_match.group(1)

    status_patterns = [
        r"Status:\s*\u2705\s*COMPLETED",
        r"Status:\s*COMPLETED",
        r"status.*completed",
    ]
    for pat in status_patterns:
        if re.search(pat, content, re.IGNORECASE):
            brief["status"] = "\u2705 \u0645\u0643\u062a\u0645\u0644"
            break
    else:
        if "\u2705" in content:
            brief["status"] = "\u2705 \u0646\u062c\u062d"
        elif "\u274c" in content or "FAILED" in content.upper():
            brief["status"] = "\u274c \u0641\u0634\u0644"
        elif "\u26a0\ufe0f" in content or "warning" in content.lower():
            brief["status"] = "\u26a0\ufe0f \u062a\u0646\u0628\u064a\u0647"

    files_section = re.search(
        r"(?:##?\s*Files\s*(?:Touched|Changed))\s*\n(.*?)(?=##|\Z)",
        content, re.DOTALL | re.IGNORECASE,
    )
    if files_section:
        file_lines = [
            line.strip()
            for line in files_section.group(1).strip().split("\n")
            if line.strip() and "|" in line and "`" in line
        ]
        if file_lines:
            brief["files_touched"] = str(len(file_lines))

    summary_patterns = [
        r"(?:##?\s*Summary|##?\s*What was done)\s*\n(.*?)(?=##|\Z)",
    ]
    for pat in summary_patterns:
        m = re.search(pat, content, re.DOTALL | re.IGNORECASE)
        if m:
            brief["summary"] = m.group(1).strip()[:300]
            break

    blocker_patterns = [
        r"(?:##?\s*Blocker)\s*\n(.*?)(?=##|\Z)",
    ]
    for pat in blocker_patterns:
        m = re.search(pat, content, re.DOTALL | re.IGNORECASE)
        if m:
            brief["blockers"] = m.group(1).strip()[:200]
            break

    next_patterns = [
        r"(?:##?\s*Next\s*(?:Recommended\s*)?Actions?)\s*\n(.*?)(?=##|\Z)",
    ]
    for pat in next_patterns:
        m = re.search(pat, content, re.DOTALL | re.IGNORECASE)
        if m:
            brief["next_action"] = m.group(1).strip()[:300]
            break

    return brief


def format_telegram_brief(brief, builder=None):
    """Format a brief dict into a Telegram message string.

    When builder is provided, delegates to BriefBuilder.format()
    which uses the config-driven telegram_template. Otherwise
    uses the legacy ad-hoc formatter (backward compatible).
    """
    if builder is not None:
        return builder.format(brief)

    # Legacy fallback for existing tests
    date = brief.get("date", "Unknown")
    status = brief.get("status", "\u2753")
    summary = brief.get("summary", "No summary found.")
    files = brief.get("files_touched", "N/A")
    blockers = brief.get("blockers", "No blockers.")
    next_act = brief.get("next_action", "No recommendation.")

    summary_preview = summary[:150] + ("..." if len(summary) > 150 else "")
    next_preview = next_act[:120] + ("..." if len(next_act) > 120 else "")
    summary_preview = summary_preview.replace("\n", " ").strip()
    next_preview = next_preview.replace("\n", " ").strip()

    return (
        f"\U0001f4cb *ZILFIT \u2014 \u0646\u0628\u0636\u0629 \u064a\u0648\u0645\u064a\u0629* | {date}\\n\\n"
        f"\u0627\u0644\u062d\u0627\u0644\u0629: {status}\\n\\n"
        f"\u0627\u0644\u0645\u0644\u0641\u0627\u062a \u0645\u0639\u062f\u0651\u0644\u0629: {files}\\n\\n"
        f"{summary_preview}\\n\\n"
        f"\u26a0\ufe0f \u0627\u0644\u0639\u0648\u0627\u0626\u0642: {blockers[:80]}\\n\\n"
        f"\u27a1\ufe0f \u0627\u0644\u062a\u0627\u0644\u064a: {next_preview}\\n\\n"
        f"_ZILFIT Cloud \U0001f1f8\U0001f1e6 \u2014 \u0647\u0646\u062f\u0633\u0629 \u0641\u0642\u0637_"
    )


def main():
    import argparse

    parser = argparse.ArgumentParser(
        description="ZILFIT Daily Brief \u2014 sends latest report summary via Telegram"
    )
    parser.add_argument(
        "--dry-run", action="store_true",
        help="Build and display the brief without sending"
    )
    parser.add_argument(
        "--report-file", type=str, default=None,
        help="Path to a specific report file"
    )
    parser.add_argument(
        "--date", type=str, default=None,
        help="Look for reports matching a specific date (YYYY-MM-DD)"
    )
    parser.add_argument(
        "--config-file", type=str, default=None,
        help="Path to brief config YAML (default: config/daily_brief_config.yaml)"
    )
    args = parser.parse_args()

    # Find report
    if args.report_file:
        if not os.path.isfile(args.report_file):
            print(f"ERROR: Report file not found: {args.report_file}", file=sys.stderr)
            return 1
        report_path = args.report_file
    else:
        report_path, err = find_latest_report(date=args.date)
        if err:
            print(f"ERROR: {err}", file=sys.stderr)
            return 1

    print(f"Report: {report_path}")

    # Load config and create the BriefBuilder
    config_path = args.config_file
    if config_path is None:
        config_path = os.path.join(_project_root, "config", "daily_brief_config.yaml")
    config = load_config(config_path)
    builder = BriefBuilder(config)

    # Parse brief using the config-driven builder
    brief = parse_report_brief(report_path, builder=builder)

    # Validate
    valid, errors = builder.validate(brief)
    if not valid:
        print("WARNING: Brief validation issues:")
        for e in errors:
            print(f"  - {e}")

    # Format using the config-driven template
    message = format_telegram_brief(brief, builder=builder)

    if args.dry_run:
        print("\n--- DRY RUN ---")
        print(message.replace("\\\\n", "\\n").replace("\\n", "\n"))
        print("--- END DRY RUN ---")
        return 0

    # Get credentials
    token, chat_id = get_credentials()
    if token is None:
        return 1

    # Send
    ok, result = send_message(token, chat_id, message)
    if ok:
        print("OK: Daily brief sent via Telegram.")
        return 0
    else:
        print(f"FAIL: {result}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())

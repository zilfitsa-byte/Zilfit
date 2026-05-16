#!/usr/bin/env python3
"""
ZILFIT Daily Brief — Manual Telegram Sender

Reads the latest daily report from reports/daily/, extracts key fields,
formats a short Arabic brief, and sends via Telegram using
send_telegram_notify.py pattern (stdlib only).

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


def find_latest_report(date=None):
    """Find the most recent daily report .md file.

    If date is provided, looks for reports matching that date.
    Otherwise, returns the most recently modified .md in reports/daily/.
    """
    report_dir = os.path.join(_project_root, "reports", "daily")
    if not os.path.isdir(report_dir):
        return None, "reports/daily/ directory not found"

    if date:
        # Look for reports matching the specific date
        pattern = os.path.join(report_dir, f"{date}*.md")
        candidates = sorted(glob.glob(pattern), key=os.path.getmtime, reverse=True)
        if candidates:
            return candidates[0], None
        return None, f"No report found for date {date}"

    # Get most recent report
    all_reports = glob.glob(os.path.join(report_dir, "*.md"))
    if not all_reports:
        return None, "No .md reports in reports/daily/"

    latest = max(all_reports, key=os.path.getmtime)
    return latest, None


def parse_report_brief(filepath):
    """Extract key fields from a daily report for the Telegram brief.

    Returns a dict with: date, status, files_touched, summary, risks, blockers.
    """
    brief = {
        "date": "Unknown",
        "status": "❓",
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

    # Extract date from filename or report content
    basename = os.path.basename(filepath)
    date_match = re.match(r"(\d{4}-\d{2}-\d{2})", basename)
    if date_match:
        brief["date"] = date_match.group(1)

    # Extract status
    status_patterns = [
        r"Status:\s*✅\s*COMPLETED",
        r"Status:\s*COMPLETED",
        r"status.*completed",
        r"الحالة:.*مكتمل",
    ]
    for pat in status_patterns:
        if re.search(pat, content, re.IGNORECASE):
            brief["status"] = "✅ مكتمل"
            break
    else:
        if "✅" in content:
            brief["status"] = "✅ نجح"
        elif "❌" in content or "FAILED" in content.upper():
            brief["status"] = "❌ فشل"
        elif "⚠️" in content or "warning" in content.lower():
            brief["status"] = "⚠️ تنبيه"

    # Extract files touched section
    files_section = re.search(
        r"(?:##?\s*Files\s*(?:Touched|Changed)|##?\s*الملفات\s*(?:المضافة|المعدلة))\s*\n(.*?)(?=##|\Z)",
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

    # Extract summary / what was done
    summary_patterns = [
        r"(?:##?\s*Summary|##?\s*What was done|##?\s*الإنجاز)\s*\n(.*?)(?=##|\Z)",
    ]
    for pat in summary_patterns:
        m = re.search(pat, content, re.DOTALL | re.IGNORECASE)
        if m:
            brief["summary"] = m.group(1).strip()[:300]
            break

    # Extract blockers
    blocker_patterns = [
        r"(?:##?\s*Blocker|##?\s*العوائق|##?\s*الكتل)\s*\n(.*?)(?=##|\Z)",
    ]
    for pat in blocker_patterns:
        m = re.search(pat, content, re.DOTALL | re.IGNORECASE)
        if m:
            brief["blockers"] = m.group(1).strip()[:200]
            break

    # Extract next actions
    next_patterns = [
        r"(?:##?\s*Next\s*(?:Recommended\s*)?Actions?|##?\s*الخطوة\s*(?:التالية|القادمة))\s*\n(.*?)(?=##|\Z)",
    ]
    for pat in next_patterns:
        m = re.search(pat, content, re.DOTALL | re.IGNORECASE)
        if m:
            brief["next_action"] = m.group(1).strip()[:300]
            break

    return brief


def format_telegram_brief(brief):
    """Format the brief dict into a Telegram-friendly Arabic message."""
    date = brief["date"]
    status = brief["status"]
    summary = brief["summary"]
    files = brief["files_touched"]
    blockers = brief["blockers"]
    next_act = brief["next_action"]

    # Truncate long text for Telegram message limits
    summary_preview = summary[:150] + ("..." if len(summary) > 150 else "")
    next_preview = next_act[:120] + ("..." if len(next_act) > 120 else "")

    # Clean up blockquotes and markdown for Telegram
    summary_preview = summary_preview.replace("\n", " ").strip()
    next_preview = next_preview.replace("\n", " ").strip()

    return (
        f"📋 *ZILFIT — نبضة يومية* | {date}\\n\\n"
        f"الحالة: {status}\\n\\n"
        f"الملفات معدّلة: {files}\\n\\n"
        f"{summary_preview}\\n\\n"
        f"⚠️ العوائق: {blockers[:80]}\\n\\n"
        f"➡️ التالي: {next_preview}\\n\\n"
        f"_ZILFIT Cloud 🇸🇦 — هندسة فقط_"
    )


def main():
    import argparse

    parser = argparse.ArgumentParser(
        description="ZILFIT Daily Brief — sends latest report summary via Telegram"
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

    # Parse brief
    brief = parse_report_brief(report_path)

    # Format message
    message = format_telegram_brief(brief)

    if args.dry_run:
        print("\n--- DRY RUN ---")
        print(message.replace("\\n", "\n"))
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

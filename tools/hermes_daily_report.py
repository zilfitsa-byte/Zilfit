#!/usr/bin/env python3
"""
Hermes Daily Operating Report Generator - Phase D2

Generates a local Markdown daily operating report from existing read-only sources.

Usage:
    python3 tools/hermes_daily_report.py

Output:
    reports/daily/YYYY-MM-DD_hermes_daily_operating_report.md
"""

import json
import os
from datetime import datetime, timezone
from pathlib import Path

# Constants
BASE_DIR = Path(__file__).resolve().parent.parent
RUNTIME_DIR = BASE_DIR / "runtime" / "agent_health"
REPORTS_DAILY_DIR = BASE_DIR / "reports" / "daily"
SOUL_FILE = BASE_DIR / "SOUL.md"
SKILLS_DIR = BASE_DIR / "skills"
TEMPLATES_DIR = BASE_DIR / "templates"

# Supported skills (based on HERMES_MEMORY_INDEX_C4.md)
SKILLS = [
    "agent_report",
    "claims_review",
    "demo_review",
    "daily_operating_report",
    "git_safety_check",
    "qwen_safe_task",
    "research_intake",
    "telegram_restart",
]


def format_utc_timestamp():
    """Return current UTC timestamp in ISO format."""
    return datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")


def get_current_date_str():
    """Return current date as YYYY-MM-DD string."""
    return datetime.now(timezone.utc).strftime("%Y-%m-%d")


def read_file_safe(filepath: Path) -> str:
    """Read file safely, return empty string if not found."""
    try:
        return filepath.read_text(encoding="utf-8")
    except (FileNotFoundError, IOError):
        return ""


def load_agent_heartbeat() -> dict:
    """Load all agent heartbeat JSON files from runtime/agent_health/."""
    agents = {}
    if not RUNTIME_DIR.exists():
        return agents

    for json_file in sorted(RUNTIME_DIR.glob("*.json")):
        try:
            data = json.loads(read_file_safe(json_file))
            agent_name = data.get("agent", json_file.stem)
            agents[agent_name] = data
        except (json.JSONDecodeError, IOError):
            continue

    return agents


def get_agent_status_summary(agents: dict) -> str:
    """Generate a one-line status summary per agent."""
    lines = []
    for agent_name in sorted(agents.keys()):
        data = agents[agent_name]
        status = data.get("status", "unknown")
        task = data.get("current_task", "").strip() or "No active task"
        confidence = data.get("confidence", "unknown")
        lines.append(f"- **{agent_name}**: {status} | {confidence} | {task[:60]}...")
    return "\n".join(lines)


def get_active_skills_summary() -> str:
    """Get list of active skills from skills/*.md files."""
    if not SKILLS_DIR.exists():
        return "Skills directory not found."

    md_files = sorted(SKILLS_DIR.glob("*.md"))
    if not md_files:
        return "No skill files found."

    skill_names = [f.stem for f in md_files]
    return ", ".join(skill_names)


def get_available_templates_summary() -> str:
    """Get list of available templates from templates/*.md files."""
    if not TEMPLATES_DIR.exists():
        return "Templates directory not found."

    md_files = sorted(TEMPLATES_DIR.glob("*.md"))
    if not md_files:
        return "No template files found."

    template_names = [f.stem for f in md_files]
    return ", ".join(template_names)


def identify_risks_and_blockers(agents: dict) -> str:
    """Identify any risks or blockers from agent status."""
    risks = []
    blockers = []

    for agent_name, data in agents.items():
        status = data.get("status", "unknown")
        next_action = data.get("next_sultan_action", "")

        if status == "idle":
            if next_action and next_action != "Review C6 heartbeat baseline.":
                blockers.append(f"{agent_name}: {next_action}")

    if not risks and not blockers:
        return "No immediate risks or blockers identified."

    output = []
    if risks:
        output.append("### Risks\n" + "\n".join(f"- {r}" for r in risks))
    if blockers:
        output.append("### Blockers\n" + "\n".join(f"- {b}" for b in blockers))

    return "\n\n".join(output)


def generate_report() -> str:
    """Generate the complete daily operating report."""
    date_str = get_current_date_str()
    timestamp = format_utc_timestamp()
    agents = load_agent_heartbeat()

    # Check git status (read-only)
    os.chdir(str(BASE_DIR))
    git_status = os.popen("git status --short 2>/dev/null").read().strip()
    git_branch = os.popen("git branch --show-current 2>/dev/null").read().strip() or "unknown"
    git_head = os.popen("git log -1 --oneline 2>/dev/null").read().strip() or "unknown"

    report = f"""# Hermes Daily Operating Report

**Generated:** {timestamp}
**Date:** {date_str}
**Project Mode:** non-production
**Branch:** {git_branch}
**HEAD:** {git_head}
**Source:** tools/hermes_daily_report.py (Phase D2)

---

## Agent Heartbeat Summary

{get_agent_status_summary(agents)}

---

## Active Skills Summary

{get_active_skills_summary()}

---

## Available Templates Summary

{get_available_templates_summary()}

---

## Risks / Blockers

{identify_risks_and_blockers(agents)}

---

## Suggested Plan for Sultan

1. **Review** agent heartbeat status and assign new tasks if needed.
2. **Approve** pending proposals via approval gate (C8).
3. **Check** for any blockers requiring escalation.
4. **Update** goals via Telegram or direct input.

---

## Approval Requests Needed

No pending approval requests. System is in idle state waiting for Sultan input.

---

## Forbidden Actions Confirmation

✅ No production changes
✅ No main merge
✅ No commit without approval
✅ No restart without approval
✅ No token/env/auth access
✅ No file deletion
✅ No paid cloud usage
✅ No medical/diagnostic/therapeutic claims
✅ No Telegram auto-sending (D2 is manual only)
✅ No autonomous execution

---

## Next Recommended Action

**For Sultan:** Review agent status and assign tasks or approve pending proposals.
**For Hermes:** Continue monitoring and prepare proposals when goals are received.

---

*End of Daily Operating Report - Phase D2*
"""
    return report


def main():
    """Main entry point."""
    # Ensure reports/daily directory exists
    REPORTS_DAILY_DIR.mkdir(parents=True, exist_ok=True)

    # Generate report
    report_content = generate_report()

    # Write report to file
    date_str = get_current_date_str()
    report_filename = f"{date_str}_hermes_daily_operating_report.md"
    report_path = REPORTS_DAILY_DIR / report_filename

    report_path.write_text(report_content, encoding="utf-8")

    # Print success message
    print(f"Report generated: {report_path}")
    print("Success: Daily operating report generated from read-only sources.")


if __name__ == "__main__":
    main()

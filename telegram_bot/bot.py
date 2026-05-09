#!/usr/bin/env python3
"""
ZILFIT Telegram Command Center v1
Read-only mobile control for ZILFIT/Hermes operations.
"""

import glob
import os
import subprocess
import sys
import textwrap
from pathlib import Path

# ── Telegram library ──
try:
    import telebot
except ImportError:
    print("ERROR: pyTelegramBotAPI not installed. Run: pip3 install pyTelegramBotAPI")
    sys.exit(1)

# ═══════════════════════════════════════════════════════════
# CONFIG
# ═══════════════════════════════════════════════════════════

def load_config():
    token = os.environ.get("ZILFIT_TELEGRAM_BOT_TOKEN", "").strip()
    if not token:
        print("ERROR: ZILFIT_TELEGRAM_BOT_TOKEN is not set.")
        sys.exit(1)

    admin_ids_raw = os.environ.get("ZILFIT_TELEGRAM_ADMIN_IDS", "").strip()
    if not admin_ids_raw:
        print("ERROR: ZILFIT_TELEGRAM_ADMIN_IDS is not set.")
        sys.exit(1)

    try:
        admin_ids = {int(x.strip()) for x in admin_ids_raw.split(",") if x.strip()}
    except ValueError:
        print("ERROR: ZILFIT_TELEGRAM_ADMIN_IDS must be comma-separated integers.")
        sys.exit(1)

    repo_root = os.environ.get("ZILFIT_REPO_ROOT", "/root/hermes/zilfit-ip-core")
    if not Path(repo_root).is_dir():
        print(f"ERROR: ZILFIT_REPO_ROOT does not exist: {repo_root}")
        sys.exit(1)

    return {
        "token": token,
        "admin_ids": admin_ids,
        "repo_root": repo_root,
    }

# ═══════════════════════════════════════════════════════════
# SECURITY: Admin gate
# ═══════════════════════════════════════════════════════════

def is_admin(message, admin_ids):
    """Check if message sender is in admin allowlist."""
    uid = message.from_user.id
    if uid not in admin_ids:
        # Silently ignore — no reply to unknown users
        return False
    return True

# ═══════════════════════════════════════════════════════════
# READER: File utilities
# ═══════════════════════════════════════════════════════════

def latest_file(directory, pattern="*.json"):
    """Return the most recently modified file matching pattern, or None."""
    files = glob.glob(os.path.join(directory, pattern))
    if not files:
        return None
    return max(files, key=os.path.getmtime)

def read_file_safe(path, max_bytes=4000):
    """Read file safely, truncate for Telegram 4096 char limit."""
    try:
        data = Path(path).read_text(encoding="utf-8", errors="replace")
        if len(data) > max_bytes:
            data = data[:max_bytes] + "\n\n… (truncated)"
        return data.strip()
    except Exception as e:
        return f"Error reading file: {e}"

def run_cmd(cmd, cwd=None, timeout=60):
    """Run a shell command safely, return stdout+stderr."""
    try:
        result = subprocess.run(
            cmd, shell=True, cwd=cwd,
            capture_output=True, text=True, timeout=timeout
        )
        out = (result.stdout + result.stderr).strip()
        return out[:4000] if out else "(empty)"
    except subprocess.TimeoutExpired:
        return f"Command timed out after {timeout}s"
    except Exception as e:
        return f"Command error: {e}"

# ═══════════════════════════════════════════════════════════
# COMMAND HANDLERS
# ═══════════════════════════════════════════════════════════

def cmd_status(cfg):
    """Git status + HEAD info."""
    repo = cfg["repo_root"]
    status = run_cmd("git status --short", cwd=repo)
    head = run_cmd("git log -1 --format='%h %ci %s'", cwd=repo)
    branch = run_cmd("git branch --show-current", cwd=repo)
    tree = "CLEAN" if status == "(empty)" else "DIRTY"
    return (
        f"⬡ ZILFIT Status\n"
        f"Branch: `{branch}`\n"
        f"HEAD: {head}\n"
        f"Working tree: {tree}\n"
        f"Changes: {status}"
    )

def cmd_nightly(cfg):
    """Latest nightly check report."""
    repo = cfg["repo_root"]
    f = latest_file(f"{repo}/reports/nightly", "nightly_check_*.json")
    if not f:
        return "⬡ Nightly: No reports found."
    import json
    try:
        data = json.loads(Path(f).read_text())
        ts = data.get("timestamp_utc", "?")
        branch = data.get("branch", "?")
        clean = "YES" if data.get("working_tree_clean") else "NO"
        tests = data.get("test_status", "?")
        return (
            f"⬡ Latest Nightly Check\n"
            f"Timestamp: `{ts}`\n"
            f"Branch: `{branch}`\n"
            f"Tree clean: {clean}\n"
            f"Test status: {tests}"
        )
    except Exception as e:
        return f"⬡ Nightly: Parse error — {e}"

def cmd_tests(cfg):
    """Run all 38 shell tests, report summary."""
    repo = cfg["repo_root"]
    out = run_cmd(
        "PASS=0; FAIL=0; for t in $(find tests -name '*.sh' -type f | sort); do "
        "if bash \"$t\" >/dev/null 2>&1; then PASS=$((PASS+1)); "
        "else FAIL=$((FAIL+1)); fi; done; "
        "echo \"PASS=$PASS FAIL=$FAIL TOTAL=$((PASS+FAIL))\"",
        cwd=repo, timeout=120
    )
    return f"⬡ Test Results\n{out}"

def cmd_agents(cfg):
    """Agent roles + last report timestamps."""
    repo = cfg["repo_root"]
    # Read active projects
    ap = read_file_safe(f"{repo}/agents/ACTIVE_PROJECTS.md", 1500)
    # Last nightly
    nl = latest_file(f"{repo}/reports/nightly", "*.json")
    nl_ts = os.path.basename(nl).replace("nightly_check_", "").replace(".json", "") if nl else "none"
    # Last quality
    qf = latest_file(f"{repo}/reports/quality", "*.json")
    q_ts = os.path.basename(qf).replace("quality_gate_", "").replace(".json", "") if qf else "none"
    # Last agent run
    af = latest_file(f"{repo}/reports/agent_runs", "*.md")
    a_ts = os.path.basename(af).replace("command_center_", "").replace(".md", "") if af else "none"
    return (
        f"⬡ Agent System\n\n"
        f"Active projects:\n```\n{ap}\n```\n"
        f"Last nightly: `{nl_ts}`\n"
        f"Last quality gate: `{q_ts}`\n"
        f"Last agent run: `{a_ts}`"
    )

def cmd_research(cfg):
    """Autopull research stats."""
    repo = cfg["repo_root"]
    # Latest raw JSON
    rf = latest_file(f"{repo}/research/autopull", "*_raw.json")
    # Latest markdown
    mf = latest_file(f"{repo}/research/daily", "*_autopull.md")
    if not rf:
        return "⬡ Research: No autopull data found."
    import json
    try:
        data = json.loads(Path(rf).read_text())
        count = data.get("result_count", 0)
        today = data.get("today", "?")
        errors = len(data.get("errors", []))
        date_str = os.path.basename(rf).replace("_autopull_raw.json", "")
        md_info = ""
        if mf:
            md_name = os.path.basename(mf).replace("_autopull.md", "")
            md_info = f"\nSummary: `{md_name}`"
        return (
            f"⬡ Research Autopull\n"
            f"Date: `{date_str}`\n"
            f"Results: {count}\n"
            f"API errors: {errors}\n"
            f"Status: NEEDS_REVIEW{md_info}"
        )
    except Exception as e:
        return f"⬡ Research: Parse error — {e}"

def cmd_claims(cfg):
    """Scan for forbidden medical/clinical terms."""
    repo = cfg["repo_root"]
    # Same scan pattern as ops/quality/run_quality_gate.sh
    out = run_cmd(
        "rg -n -i 'treats|treating|treatment for|cures|diagnoses|"
        "diagnostic result|prevents disease|prevention of disease|"
        "regulates hormones|medical grade|clinical result|"
        "therapeutic effect|pain reduction|heals|healing|patient outcome' "
        "simulation_reports/ reports/ 2>/dev/null | "
        "rg -v -i 'no medical|non-medical|not medical|no clinical|"
        "non-clinical|not clinical|no diagnostic|non-diagnostic|"
        "not diagnostic|no therapeutic|non-therapeutic|not therapeutic|"
        "unsafe wording|forbidden|negative|expected validator failure|"
        "must not|does not validate' || true",
        cwd=repo, timeout=30
    )
    if out == "(empty)":
        return "⬡ Claims Scan: PASS — No forbidden terms found."
    lines = out.split("\n")
    if len(lines) > 20:
        out = "\n".join(lines[:20]) + f"\n\n… and {len(lines)-20} more lines"
    return f"⬡ Claims Scan: REVIEW REQUIRED\n```\n{out}\n```"

def cmd_demo(cfg):
    """List demo files."""
    repo = cfg["repo_root"]
    demos = run_cmd("ls -lh demo/livefit_demo_v*.html 2>/dev/null", cwd=repo)
    legacy = run_cmd("ls -lh demo/legacy/ 2>/dev/null", cwd=repo)
    patch = run_cmd("ls -lh patch_livefit.py 2>/dev/null", cwd=repo)
    v4 = run_cmd("ls -lh demo/livefit_demo_v4.html 2>/dev/null", cwd=repo)
    return (
        f"⬡ Demo Artifacts\n\n"
        f"Versions:\n```\n{demos if demos != '(empty)' else 'none'}\n```\n"
        f"Current (v4): `{v4 if v4 != '(empty)' else 'not found'}`\n"
        f"Legacy backups: `{legacy if legacy != '(empty)' else 'none'}`\n"
        f"Reference patch: `{patch if patch != '(empty)' else 'none'}`"
    )

def cmd_help(*_args):
    """List all commands."""
    return textwrap.dedent("""\
    ⬡ ZILFIT Command Center v1

    /status   — Git branch, HEAD, working tree state
    /nightly  — Latest nightly check result
    /tests    — Run all 38 shell tests, show PASS/FAIL
    /agents   — Agent roles, active projects, last run times
    /research — Autopull research stats and status
    /claims   — Forbidden medical/clinical term scan
    /demo     — List demo files and versions
    /help     — This message
    /start    — Same as /help

    Read-only. No write or execute commands in v1.""")

# ═══════════════════════════════════════════════════════════
# DISPATCHER
# ═══════════════════════════════════════════════════════════

COMMANDS = {
    "status": cmd_status,
    "nightly": cmd_nightly,
    "tests": cmd_tests,
    "agents": cmd_agents,
    "research": cmd_research,
    "claims": cmd_claims,
    "demo": cmd_demo,
    "help": cmd_help,
    "start": cmd_help,
}

def handle_message(message, bot, cfg):
    """Route incoming message to command handler."""
    if not message.text or not message.text.startswith("/"):
        return
    if not is_admin(message, cfg["admin_ids"]):
        return

    cmd = message.text.split()[0].lstrip("/").lower()
    handler = COMMANDS.get(cmd)
    if not handler:
        bot.reply_to(message, f"Unknown command. Send /help for options.")
        return

    try:
        if cmd == "help":
            result = handler()
        else:
            result = handler(cfg)
        bot.reply_to(message, result)
    except Exception as e:
        bot.reply_to(message, f"⬡ Error: {e}")

# ═══════════════════════════════════════════════════════════
# MAIN
# ═══════════════════════════════════════════════════════════

def main():
    cfg = load_config()
    bot = telebot.TeleBot(cfg["token"], parse_mode=None)

    print(f"⬡ ZILFIT Command Center v1 started")
    print(f"   Repo: {cfg['repo_root']}")
    print(f"   Admin IDs: {cfg['admin_ids']}")
    print(f"   Polling…")

    @bot.message_handler(func=lambda m: True)
    def on_message(message):
        handle_message(message, bot, cfg)

    bot.infinity_polling()

if __name__ == "__main__":
    main()

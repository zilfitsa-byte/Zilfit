#!/usr/bin/env python3
"""
ZILFIT Telegram Command Center v2
Read-only mobile control + safe Qwen execution bridge + Arabic scheduled reports.
"""

import glob
import json
import os
import re
import subprocess
import sys
import textwrap
import threading
import time
import uuid
from datetime import datetime, timezone
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
# MARKDOWN ESCAPING (Telegram-safe)
# ═══════════════════════════════════════════════════════════

def escape_md(text):
    """Escape MarkdownV2 special chars so Telegram doesn't choke."""
    # When parse_mode=None (our mode), we send plain text.
    # But backticks are still useful for code. Keep them as-is.
    # Just strip any potential HTML-like content that could confuse.
    return text

def safe_reply(bot, message, text, max_len=4000):
    """Reply with truncated text, Telegram-safe."""
    if len(text) > max_len:
        text = text[:max_len] + "\n\n… (مقتطع / truncated)"
    try:
        bot.reply_to(message, text)
    except Exception:
        # Fallback: try without any special chars
        cleaned = re.sub(r'[_*`\\]', '', text)
        bot.reply_to(message, cleaned[:max_len])

# ═══════════════════════════════════════════════════════════
# LANGUAGE STATE
# ═══════════════════════════════════════════════════════════

# Track users who forced Arabic output
_arabic_users = set()

def force_arabic(uid):
    _arabic_users.add(uid)

def unforce_arabic(uid):
    _arabic_users.discard(uid)

def is_arabic(uid):
    return uid in _arabic_users

# ═══════════════════════════════════════════════════════════
# PENDING COMMANDS (Qwen bridge)
# ═══════════════════════════════════════════════════════════

_pending_commands = {}  # id -> {cmd, proposed, status, requester, timestamp}
_pending_lock = threading.Lock()

AUDIT_DIR = Path("reports/telegram_actions")

def ensure_audit_dir():
    AUDIT_DIR.mkdir(parents=True, exist_ok=True)

def audit_log(entry_dict):
    """Append one JSON line to the audit log."""
    ensure_audit_dir()
    log_file = AUDIT_DIR / f"actions_{datetime.now(timezone.utc).strftime('%Y%m%d')}.jsonl"
    entry_dict["ts"] = datetime.now(timezone.utc).isoformat()
    log_file.write_text(json.dumps(entry_dict, ensure_ascii=False) + "\n", encoding="utf-8")

def add_pending(requester_uid, task_text, proposed_cmd):
    """Add a pending command, return its id."""
    cmd_id = str(uuid.uuid4())[:8]
    with _pending_lock:
        _pending_commands[cmd_id] = {
            "id": cmd_id,
            "task": task_text,
            "proposed_cmd": proposed_cmd,
            "status": "pending",
            "requester_uid": requester_uid,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }
    audit_log({"event": "pending_created", "id": cmd_id, "task": task_text, "proposed": proposed_cmd, "requester": requester_uid})
    return cmd_id

def approve_pending(cmd_id):
    """Mark a pending command as approved."""
    with _pending_lock:
        item = _pending_commands.get(cmd_id)
        if not item:
            return None, "Command not found."
        if item["status"] != "pending":
            return None, f"Command already {item['status']}."
        item["status"] = "approved"
    audit_log({"event": "approved", "id": cmd_id})
    return item, None

def cancel_pending(cmd_id):
    """Cancel a pending command."""
    with _pending_lock:
        item = _pending_commands.get(cmd_id)
        if not item:
            return None, "Command not found."
        if item["status"] != "pending":
            return None, f"Command already {item['status']}."
        item["status"] = "cancelled"
    audit_log({"event": "cancelled", "id": cmd_id})
    return item, None

def get_pending_list():
    """Return list of pending commands."""
    with _pending_lock:
        return [v for v in _pending_commands.values() if v["status"] == "pending"]

# ═══════════════════════════════════════════════════════════
# SAFE COMMANDS ALLOWLIST (Qwen bridge)
# ═══════════════════════════════════════════════════════════

# Read-only commands that never need approval
READONLY_PREFIXES = [
    "git status",
    "git log",
    "git branch",
    "git show",
    "git diff",
    "git tag",
    "ls ",
    "ls\n",
    "ls\t",
    "find ",
    "cat ",
    "grep ",
    "rg ",
    "sed -n",
    "tail ",
    "head ",
    "wc ",
    "python3 tests/",
    "bash tests/",
    "echo ",
    "date",
    "whoami",
    "pwd",
    "uname",
    "hostname",
    "uptime",
    "df ",
    "du -s",
    "tree ",
    "stat ",
    "file ",
    "diff ",
    "comm ",
    "sort ",
    "uniq ",
    "cut ",
    "tr ",
    "rev ",
]

# Forbidden patterns — NEVER allow these
FORBIDDEN_PATTERNS = [
    r"\.env",
    r"API.?KEY",
    r"SECRET",
    r"TOKEN",
    r"rm\s+(-rf?|--recursive)",
    r"rm\s+-",
    r"chmod\s+777",
    r"curl.*\|\s*(bash|sh)",
    r"wget.*\|\s*(bash|sh)",
    r"curl.*\|.*sh",
    r"rm\s+.*\.env",
    r"rm\s+.*secrets",
    r"rm\s+.*auth",
    r"mkfs",
    r"dd\s+if=",
    r">/dev/sd",
    r"production",
    r"systemctl\s+(stop|start|restart|disable|enable)",
    r"crontab\s+(-e|-r)",
    r"shutdown",
    r"reboot",
    r"killall",
    r"pkill",
    r"pip\s+install",
    r"pip3\s+install",
    r"apt[-_]get",
    r"yum\s+",
    r"sudo\s+",
]

def is_readonly(cmd):
    """Check if command is read-only and auto-allowed."""
    cmd_stripped = cmd.strip()
    for prefix in READONLY_PREFIXES:
        if cmd_stripped.startswith(prefix):
            return True
    return False

def is_forbidden(cmd):
    """Check if command matches any forbidden pattern."""
    for pattern in FORBIDDEN_PATTERNS:
        if re.search(pattern, cmd, re.IGNORECASE):
            return True
    return False

def classify_command(cmd):
    """
    Classify a command.
    Returns: ('safe', 'needs_approval', 'forbidden', reason)
    """
    cmd_stripped = cmd.strip()

    if is_forbidden(cmd_stripped):
        return "forbidden", "❌ هذا الأمر ممنوع (forbidden — touches security/auth/destructive ops)"

    if is_readonly(cmd_stripped):
        return "safe", "✅ أمر آمن — تنفيذ مباشر (safe read-only command)"

    return "needs_approval", "⚠️ يحتاج موافقة — يحتاج موافقة صريحة (needs explicit approval)"

# ═══════════════════════════════════════════════════════════
# ARABIC REPORT GENERATOR
# ═══════════════════════════════════════════════════════════

def generate_arabic_report(cfg):
    """Generate a comprehensive Arabic report."""
    repo = cfg["repo_root"]

    # Branch and HEAD
    branch = run_cmd("git branch --show-current", cwd=repo, timeout=10).strip()
    head = run_cmd("git log -1 --format='%h — %ci — %s'", cwd=repo, timeout=10).strip()
    status_short = run_cmd("git status --short", cwd=repo, timeout=10)
    tree_state = "نظيف ✅" if status_short == "(empty)" else "متغير ⚠️"

    # Nightly result
    nl_file = latest_file(f"{repo}/reports/nightly", "nightly_check_*.json")
    if nl_file:
        try:
            nl_data = json.loads(Path(nl_file).read_text())
            nl_ts = nl_data.get("timestamp_utc", "غير متوفر")
            nl_branch = nl_data.get("branch", "?")
            nl_clean = "نعم ✅" if nl_data.get("working_tree_clean") else "لا ⚠️"
            nl_tests = nl_data.get("test_status", "?")
            if nl_tests == "pass":
                nl_tests_ar = "ناجحة ✅"
            elif nl_tests == "fail":
                nl_tests_ar = "فاشلة ❌"
            else:
                nl_tests_ar = str(nl_tests)
            nightly_info = (
                f"آخر تقرير ليلي:\n"
                f"  الوقت: {nl_ts}\n"
                f"  الفرع: {nl_branch}\n"
                f"  الشجرة نظيفة: {nl_clean}\n"
                f"  نتيجة الاختبارات: {nl_tests_ar}"
            )
        except Exception as e:
            nightly_info = f"خطأ في قراءة التقرير الليلي: {e}"
    else:
        nightly_info = "لا يوجد تقرير ليلي بعد"

    # Tests summary
    test_out = run_cmd(
        "PASS=0; FAIL=0; for t in $(find tests -name '*.sh' -type f | sort); do "
        "if bash \"$t\" >/dev/null 2>&1; then PASS=$((PASS+1)); "
        "else FAIL=$((FAIL+1)); fi; done; "
        "echo \"PASS=$PASS FAIL=$FAIL TOTAL=$((PASS+FAIL))\"",
        cwd=repo, timeout=120
    )
    # Parse test result
    test_summary_ar = test_out
    if "PASS=" in test_out:
        parts = {}
        for part in test_out.split():
            if "=" in part:
                k, v = part.split("=", 1)
                parts[k] = v
        passed = parts.get("PASS", "?")
        failed = parts.get("FAIL", "?")
        total = parts.get("TOTAL", "?")
        test_summary_ar = f"ناجح: {passed} | فاشل: {failed} | المجموع: {total}"

    # Agents status
    ap_file = f"{repo}/agents/ACTIVE_PROJECTS.md"
    if Path(ap_file).exists():
        ap_content = read_file_safe(ap_file, 600)
        # Strip markdown heading
        lines = ap_content.split("\n")
        project_lines = [l for l in lines if l.strip() and not l.startswith("#")]
        agents_info = "المشاريع النشطة:\n" + "\n".join(f"  {l}" for l in project_lines[:10])
    else:
        agents_info = "غير متوفر"

    # Research/autopull status
    rf = latest_file(f"{repo}/research/autopull", "*_raw.json")
    mf = latest_file(f"{repo}/research/daily", "*_autopull.md")
    if rf:
        try:
            rdata = json.loads(Path(rf).read_text())
            r_count = rdata.get("result_count", 0)
            r_date = os.path.basename(rf).replace("_autopull_raw.json", "")
            r_errors = len(rdata.get("errors", []))
            research_info = f"تاريخ: {r_date} | نتائج: {r_count} | أخطاء API: {r_errors} | الحالة: بحاجة لمراجعة"
        except Exception:
            research_info = "خطأ في قراءة بيانات البحث"
    else:
        research_info = "لا توجد بيانات بحث تلقائي"

    if mf:
        research_info += f"\nملخص: {os.path.basename(mf).replace('_autopull.md', '')}"

    # Claims/compliance status
    claims_out = run_cmd(
        "rg -c -i 'treats|treating|treatment for|cures|diagnoses|"
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
    if claims_out == "(empty)":
        claims_info = "فحص الادعاءات: سليم ✅ — لا توجد مصطلحات محظورة"
    else:
        lines = claims_out.strip().split("\n")
        claims_info = f"فحص الادعاءات: يحتاج مراجعة ⚠️\n  عدد الملفات المخالفة: {len(lines)}"
        if len(lines) > 5:
            claims_info += "\n  (أول 5 نتائج فقط)"
            lines = lines[:5]
        claims_info += "\n" + "\n".join(f"    {l}" for l in lines)

    # Recommended next action
    if tree_state == "متغير ⚠️":
        next_action = "⚡ الإجراء التالي: العمل-tree متغير — يُرجى مراجعة التغييرات أو الالتزام بها"
    elif "FAIL" in test_out and test_summary_ar != "ناجح: 0 | فاشل: 0":
        next_action = "⚡ الإجراء التالي: هناك اختبارات فاشلة — يُرجى إصلاحها قبل المتابعة"
    elif "FAIL" not in test_out or "FAIL=0" in test_out:
        next_action = "✅ الإجراء التالي: كل شيء طبيعي — متابعة جدول العمل اليومي"
    else:
        next_action = "📋 الإجراء التالي: مراجعة التقرير والتحقق من الحالة"

    # Assemble full report
    report = (
        "═══════════════════════════════\n"
        "📊 تقرير ZILFIT اليومي\n"
        f"⏰ {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M UTC')}\n"
        "═══════════════════════════════\n\n"
        f"🌿 الفرع: {branch if branch else '(غير متوفر)'}\n"
        f"📌 HEAD: {head if head else '(غير متوفر)'}\n"
        f"📁 حالة الشجرة: {tree_state}\n\n"
        f"🌙 التقرير الليلي:\n{nightly_info}\n\n"
        f"🧪 ملخص الاختبارات:\n{test_summary_ar}\n\n"
        f"🤖 حالة الوكلاء:\n{agents_info}\n\n"
        f"🔬 البحث والسحب التلقائي:\n{research_info}\n\n"
        f"🛡️ فحص الادعاءات/الامتثال:\n{claims_info}\n\n"
        f"{next_action}"
    )

    return report

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

def cmd_status_ar(cfg):
    """Arabic version of status."""
    repo = cfg["repo_root"]
    branch = run_cmd("git branch --show-current", cwd=repo)
    head = run_cmd("git log -1 --format='%h — %ci — %s'", cwd=repo)
    status_short = run_cmd("git status --short", cwd=repo)
    tree = "نظيف ✅" if status_short == "(empty)" else "متغير ⚠️"
    return (
        f"⬡ حالة ZILFIT\n"
        f"الفرع: `{branch}`\n"
        f"HEAD: {head}\n"
        f"حالة الشجرة: {tree}\n"
        f"التغييرات: {status_short}"
    )

def cmd_nightly(cfg):
    """Latest nightly check report."""
    repo = cfg["repo_root"]
    f = latest_file(f"{repo}/reports/nightly", "nightly_check_*.json")
    if not f:
        return "⬡ Nightly: No reports found."
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

def cmd_nightly_ar(cfg):
    """Arabic nightly."""
    repo = cfg["repo_root"]
    f = latest_file(f"{repo}/reports/nightly", "nightly_check_*.json")
    if not f:
        return "⬡ ليلي: لا توجد تقارير"
    try:
        data = json.loads(Path(f).read_text())
        ts = data.get("timestamp_utc", "?")
        branch = data.get("branch", "?")
        clean = "نعم ✅" if data.get("working_tree_clean") else "لا ⚠️"
        tests_raw = data.get("test_status", "?")
        tests = "ناجحة ✅" if tests_raw == "pass" else ("فاشلة ❌" if tests_raw == "fail" else str(tests_raw))
        return (
            f"⬡ التقرير الليلي\n"
            f"الوقت: `{ts}`\n"
            f"الفرع: `{branch}`\n"
            f"الشجرة نظيفة: {clean}\n"
            f"الاختبارات: {tests}"
        )
    except Exception as e:
        return f"⬡ ليلي: خطأ في القراءة — {e}"

def cmd_tests(cfg):
    """Run all shell tests, report summary."""
    repo = cfg["repo_root"]
    out = run_cmd(
        "PASS=0; FAIL=0; for t in $(find tests -name '*.sh' -type f | sort); do "
        "if bash \"$t\" >/dev/null 2>&1; then PASS=$((PASS+1)); "
        "else FAIL=$((FAIL+1)); fi; done; "
        "echo \"PASS=$PASS FAIL=$FAIL TOTAL=$((PASS+FAIL))\"",
        cwd=repo, timeout=120
    )
    return f"⬡ Test Results\n{out}"

def cmd_tests_ar(cfg):
    """Arabic tests summary."""
    repo = cfg["repo_root"]
    out = run_cmd(
        "PASS=0; FAIL=0; for t in $(find tests -name '*.sh' -type f | sort); do "
        "if bash \"$t\" >/dev/null 2>&1; then PASS=$((PASS+1)); "
        "else FAIL=$((FAIL+1)); fi; done; "
        "echo \"PASS=$PASS FAIL=$FAIL TOTAL=$((PASS+FAIL))\"",
        cwd=repo, timeout=120
    )
    parts = {}
    for part in out.split():
        if "=" in part:
            k, v = part.split("=", 1)
            parts[k] = v
    passed = parts.get("PASS", "?")
    failed = parts.get("FAIL", "?")
    total = parts.get("TOTAL", "?")
    return f"⬡ نتائج الاختبارات\nناجح: {passed} | فاشل: {failed} | المجموع: {total}"

def cmd_agents(cfg):
    """Agent roles + last report timestamps."""
    repo = cfg["repo_root"]
    ap = read_file_safe(f"{repo}/agents/ACTIVE_PROJECTS.md", 1500)
    nl = latest_file(f"{repo}/reports/nightly", "*.json")
    nl_ts = os.path.basename(nl).replace("nightly_check_", "").replace(".json", "") if nl else "none"
    qf = latest_file(f"{repo}/reports/quality", "*.json")
    q_ts = os.path.basename(qf).replace("quality_gate_", "").replace(".json", "") if qf else "none"
    af = latest_file(f"{repo}/reports/agent_runs", "*.md")
    a_ts = os.path.basename(af).replace("command_center_", "").replace(".md", "") if af else "none"
    return (
        f"⬡ Agent System\n\n"
        f"Active projects:\n```\n{ap}\n```\n"
        f"Last nightly: `{nl_ts}`\n"
        f"Last quality gate: `{q_ts}`\n"
        f"Last agent run: `{a_ts}`"
    )

def cmd_agents_ar(cfg):
    """Arabic agents status."""
    repo = cfg["repo_root"]
    ap = read_file_safe(f"{repo}/agents/ACTIVE_PROJECTS.md", 1500)
    nl = latest_file(f"{repo}/reports/nightly", "*.json")
    nl_ts = os.path.basename(nl).replace("nightly_check_", "").replace(".json", "") if nl else "لا يوجد"
    qf = latest_file(f"{repo}/reports/quality", "*.json")
    q_ts = os.path.basename(qf).replace("quality_gate_", "").replace(".json", "") if qf else "لا يوجد"
    af = latest_file(f"{repo}/reports/agent_runs", "*.md")
    a_ts = os.path.basename(af).replace("command_center_", "").replace(".md", "") if af else "لا يوجد"
    return (
        f"⬡ نظام الوكلاء\n\n"
        f"المشاريع النشطة:\n```\n{ap}\n```\n"
        f"آخر تقرير ليلي: `{nl_ts}`\n"
        f"آخر فحص جودة: `{q_ts}`\n"
        f"آخر تشغيل وكيل: `{a_ts}`"
    )

def cmd_research(cfg):
    """Autopull research stats."""
    repo = cfg["repo_root"]
    rf = latest_file(f"{repo}/research/autopull", "*_raw.json")
    mf = latest_file(f"{repo}/research/daily", "*_autopull.md")
    if not rf:
        return "⬡ Research: No autopull data found."
    try:
        data = json.loads(Path(rf).read_text())
        count = data.get("result_count", 0)
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

def cmd_research_ar(cfg):
    """Arabic research."""
    repo = cfg["repo_root"]
    rf = latest_file(f"{repo}/research/autopull", "*_raw.json")
    mf = latest_file(f"{repo}/research/daily", "*_autopull.md")
    if not rf:
        return "⬡ بحث: لا توجد بيانات سحب تلقائي"
    try:
        data = json.loads(Path(rf).read_text())
        count = data.get("result_count", 0)
        errors = len(data.get("errors", []))
        date_str = os.path.basename(rf).replace("_autopull_raw.json", "")
        md_info = ""
        if mf:
            md_info = f"\nملخص: `{os.path.basename(mf).replace('_autopull.md', '')}`"
        return (
            f"⬡ البحث والسحب التلقائي\n"
            f"التاريخ: `{date_str}`\n"
            f"النتائج: {count}\n"
            f"أخطاء API: {errors}\n"
            f"الحالة: بحاجة لمراجعة{md_info}"
        )
    except Exception as e:
        return f"⬡ بحث: خطأ في القراءة — {e}"

def cmd_claims(cfg):
    """Scan for forbidden medical/clinical terms."""
    repo = cfg["repo_root"]
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

def cmd_claims_ar(cfg):
    """Arabic claims scan."""
    repo = cfg["repo_root"]
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
        return "⬡ فحص الادعاءات: سليم ✅ — لا توجد مصطلحات محظورة"
    lines = out.split("\n")
    if len(lines) > 20:
        out = "\n".join(lines[:20]) + f"\n\n… و {len(lines)-20} سطور إضافية"
    return f"⬡ فحص الادعاءات: يحتاج مراجعة ⚠️\n```\n{out}\n```"

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

def cmd_demo_ar(cfg):
    """Arabic demo listing."""
    repo = cfg["repo_root"]
    demos = run_cmd("ls -lh demo/livefit_demo_v*.html 2>/dev/null", cwd=repo)
    v4 = run_cmd("ls -lh demo/livefit_demo_v4.html 2>/dev/null", cwd=repo)
    if demos == "(empty)":
        demos_info = "لا توجد"
    else:
        demos_info = demos
    return (
        f"⬡ ملفات العرض التوضيحي\n\n"
        f"الإصدارات:\n```\n{demos_info}\n```\n"
        f"الحالي (v4): `{v4 if v4 != '(empty)' else 'غير موجود'}`"
    )

def cmd_help(*_args):
    """List all commands."""
    return textwrap.dedent("""\
    ⬡ ZILFIT Command Center v2

    📊 تقارير
    /status   — Git branch, HEAD, working tree state
    /nightly  — Latest nightly check result
    /tests    — Run all shell tests, show PASS/FAIL
    /agents   — Agent roles, active projects, last run times
    /research — Autopull research stats
    /claims   — Forbidden medical/clinical term scan
    /demo     — List demo files and versions
    /report   — Full Arabic daily report (immediate)

    🔧 Qwen Bridge (safe execution)
    /qwen <task>  — Propose a command for review
    /queue        — Show pending approval items
    /approve <id> — Execute an approved pending command
    /cancel <id>  — Cancel a pending command

    🌐 Language
    /arabic   — Force Arabic output for your session
    /english  — Force English output for your session

    ℹ️ Info
    /help     — This message
    /start    — Same as /help

    Read-only by default. Write commands need /approve.""")

def cmd_help_ar(*_args):
    """Arabic help."""
    return textwrap.dedent("""\
    ⬡ مركز تحكم ZILFIT v2

    📊 التقارير
    /status   — فرع Git، HEAD، حالة الشجرة
    /nightly  — آخر تقرير ليلي
    /tests    — تشغيل كل الاختبارات
    /agents   — حالة الوكلاء والمشاريع النشطة
    /research — إحصائيات البحث التلقائي
    /claims   — فحص المصطلحات الطبية المحظورة
    /demo     — ملفات العرض التوضيحي
    /report   — تقرير يومي شامل بالعربية (فوري)

    🔧 جسر Qwen (تنفيذ آمن)
    /qwen <مهمة>  — اقتراح أمر للمراجعة
    /queue        — عرض العناصر المنتظرة للموافقة
    /approve <id> — تنفيذ أمر تمت الموافقة عليه
    /cancel <id>  — إلغاء أمر معلق

    🌐 اللغة
    /arabic   — فرض الإخراج بالعربية
    /english  — فرض الإخراج بالإنجليزية

    ℹ️ معلومات
    /help     — هذه الرسالة
    /start    — نفس /help

    القراءة فقط افتراضياً. أوامر الكتابة تحتاج /approve.""")

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

    parts = message.text.strip().split(None, 1)
    cmd = parts[0].lstrip("/").lower()
    arg = parts[1] if len(parts) > 1 else None

    # ── Language commands ──
    if cmd == "arabic":
        force_arabic(message.from_user.id)
        bot.reply_to(message, "تم تفعيل اللغة العربية ✅\nأرسل /english للعودة للإنجليزية")
        return

    if cmd == "english":
        unforce_arabic(message.from_user.id)
        bot.reply_to(message, "Language switched to English ✅")
        return

    # ── Determine output language ──
    arabic_mode = is_arabic(message.from_user.id)

    # ── Report command (v2) ──
    if cmd == "report":
        report = generate_arabic_report(cfg)
        safe_reply(bot, message, report)
        audit_log({"event": "manual_report", "user": message.from_user.id, "lang": "arabic"})
        return

    # ── Qwen bridge commands (v2) ──
    if cmd == "qwen":
        if not arg:
            safe_reply(bot, message, "الاستخدام: /qwen <وصف المهمة>\nمثال: /qwen git log --oneline -5")
            return
        task_text = arg.strip()
        audit_log({"event": "qwen_requested", "user": message.from_user.id, "task": task_text})

        # Try to extract a shell command from the task
        # If the task itself looks like a command, use it directly
        # Otherwise, propose a plan
        classification, reason = classify_command(task_text)

        if classification == "forbidden":
            safe_reply(bot, message, f"❌ أمر ممنوع\n\n{reason}\n\nالمهمة: {task_text}")
            return

        if classification == "safe":
            # Execute safe read-only command directly
            safe_reply(bot, message, f"✅ {reason}\n\nالأمر: {task_text}\n\nجاري التنفيذ...")
            result = run_cmd(task_text, cwd=cfg["repo_root"], timeout=30)
            safe_reply(bot, message, f"النتيجة:\n```\n{result}\n```")
            audit_log({"event": "qwen_executed_safe", "user": message.from_user.id, "task": task_text, "result_len": len(result)})
            return

        # Needs approval
        cmd_id = add_pending(message.from_user.id, task_text, task_text)
        safe_reply(bot, message,
            f"⚠️ الأمر يحتاج موافقة\n\n"
            f"المهمة: {task_text}\n"
            f"الأمر المقترح: `{task_text}`\n"
            f"المعرّف: `{cmd_id}`\n\n"
            f"للموافقة: /approve {cmd_id}\n"
            f"للإلغاء: /cancel {cmd_id}")
        return

    if cmd == "queue":
        pending = get_pending_list()
        if not pending:
            safe_reply(bot, message, "📋 قائمة الانتظار فارغة ✅")
            return
        lines = ["📋 عناصر بانتظار الموافقة:\n"]
        for p in pending:
            lines.append(
                f"🆔 `{p['id']}`\n"
                f"   المهمة: {p['task']}\n"
                f"   الطلب: {p['timestamp'][:19]}\n"
            )
        safe_reply(bot, message, "\n".join(lines))
        return

    if cmd == "approve":
        if not arg:
            safe_reply(bot, message, "الاستخدام: /approve <id>")
            return
        item, err = approve_pending(arg.strip())
        if err:
            safe_reply(bot, message, f"❌ {err}")
            return
        # Execute the approved command
        proposed = item["proposed_cmd"]
        audit_log({"event": "executing_approved", "id": arg.strip(), "cmd": proposed})
        safe_reply(bot, message, f"⚡ تنفيذ الأمر الموافق عليه:\n`{proposed}`\n\nجاري التنفيذ...")
        result = run_cmd(proposed, cwd=cfg["repo_root"], timeout=60)
        safe_reply(bot, message, f"النتيجة:\n```\n{result}\n```")
        audit_log({"event": "execution_done", "id": arg.strip(), "result_len": len(result)})
        return

    if cmd == "cancel":
        if not arg:
            safe_reply(bot, message, "الاستخدام: /cancel <id>")
            return
        item, err = cancel_pending(arg.strip())
        if err:
            safe_reply(bot, message, f"❌ {err}")
            return
        safe_reply(bot, message, f"✅ تم إلغاء الأمر `{arg.strip()}`")
        return

    # ── Standard commands ──
    handler = COMMANDS.get(cmd)
    if not handler:
        if arabic_mode:
            bot.reply_to(message, "أمر غير معروف. أرسل /help للخيارات.")
        else:
            bot.reply_to(message, "Unknown command. Send /help for options.")
        return

    try:
        # Pick language variant
        if arabic_mode:
            ar_handler = COMMANDS.get(cmd + "_ar")
            if ar_handler:
                result = ar_handler(cfg)
            else:
                result = handler(cfg)
        else:
            result = handler(cfg)
        safe_reply(bot, message, result)
    except Exception as e:
        safe_reply(bot, message, f"⬡ Error: {e}")

# ═══════════════════════════════════════════════════════════
# SCHEDULED ARABIC REPORTS (4x per day)
# ═══════════════════════════════════════════════════════════

# Report times in UTC: 08:00, 12:00, 16:00, 21:00
# If server uses local time other than UTC, adjust here.
REPORT_HOURS_UTC = [8, 12, 16, 21]

def scheduler_loop(bot, cfg):
    """
    Simple polling scheduler — checks every 60 seconds.
    Sends Arabic report at scheduled times (once per slot).
    Runs in a background thread.
    """
    last_sent_slots = set()
    print("⬡ Scheduler thread started (reports at UTC 08:00, 12:00, 16:00, 21:00)")

    while True:
        try:
            now_utc = datetime.now(timezone.utc)
            hour = now_utc.hour
            minute = now_utc.minute
            slot_key = f"{now_utc.date()}_{hour}"

            if hour in REPORT_HOURS_UTC and minute == 0 and slot_key not in last_sent_slots:
                # Send reports to all admin users
                print(f"⬡ Sending scheduled Arabic report for {now_utc.isoformat()}")
                report = generate_arabic_report(cfg)
                for admin_id in cfg["admin_ids"]:
                    try:
                        bot.send_message(admin_id, report)
                    except Exception as e:
                        print(f"⬡ Failed to send report to {admin_id}: {e}")
                last_sent_slots.add(slot_key)
                audit_log({"event": "scheduled_report_sent", "slot": slot_key, "admins_count": len(cfg["admin_ids"])})

            # Clean old slots (keep only today)
            today_prefix = str(now_utc.date())
            last_sent_slots = {s for s in last_sent_slots if s.startswith(today_prefix)}

        except Exception as e:
            print(f"⬡ Scheduler error: {e}")

        time.sleep(60)

# ═══════════════════════════════════════════════════════════
# MAIN
# ═══════════════════════════════════════════════════════════

def main():
    cfg = load_config()
    bot = telebot.TeleBot(cfg["token"], parse_mode=None)

    print(f"⬡ ZILFIT Command Center v2 started")
    print(f"   Repo: {cfg['repo_root']}")
    print(f"   Admin IDs: {cfg['admin_ids']}")
    print(f"   Scheduled reports: UTC {REPORT_HOURS_UTC}")
    print(f"   Polling…")

    # Start scheduler thread
    scheduler_thread = threading.Thread(
        target=scheduler_loop, args=(bot, cfg), daemon=True
    )
    scheduler_thread.start()

    @bot.message_handler(func=lambda m: True)
    def on_message(message):
        handle_message(message, bot, cfg)

    bot.infinity_polling()

if __name__ == "__main__":
    main()

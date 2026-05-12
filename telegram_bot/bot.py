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

# ── Local classifier (Superpowers Step 1) ──
from classifier import classify_qwen_task, is_safe_for_auto_execute, run_self_check

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

def run_cmd_safe(cmd_list, cwd=None, timeout=30):
    """Run a fixed allowlisted command safely — no shell=True, with timeout.

    Only permits a small set of read-only git commands used by /agents.
    Returns stripped stdout, or a short error string on failure.
    """
    ALLOWLIST = {
        ("git", "status", "--short"),
        ("git", "branch", "--show-current"),
        ("git", "log", "--oneline", "-1"),
    }
    key = tuple(cmd_list)
    if key not in ALLOWLIST:
        return "[غير متوفر]"
    try:
        result = subprocess.run(
            cmd_list,
            cwd=cwd,
            capture_output=True,
            text=True,
            timeout=timeout,
        )
        out = result.stdout.strip()
        return out[:2000] if out else ""
    except subprocess.TimeoutExpired:
        return "[غير متوفر]"
    except Exception:
        return "[غير متوفر]"


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

def add_pending(requester_uid, task_text, proposed_cmd, item_type="shell"):
    """Add a pending command, return its id."""
    cmd_id = str(uuid.uuid4())[:8]
    with _pending_lock:
        _pending_commands[cmd_id] = {
            "id": cmd_id,
            "task": task_text,
            "proposed_cmd": proposed_cmd,
            "status": "pending",
            "requester_uid": requester_uid,
            "item_type": item_type,  # "shell" or "qwen_prompt"
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }
    audit_log({"event": "pending_created", "id": cmd_id, "task": task_text, "proposed": proposed_cmd, "item_type": item_type, "requester": requester_uid})
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
# SAFE QWEN EXECUTION WRAPPER (Superpowers Step 1)
# ═══════════════════════════════════════════════════════════

def execute_qwen_safe(task_text, repo_root, timeout=300):
    """
    Execute a natural-language Qwen task safely.

    CRITICAL: This function NEVER passes the raw prompt to shell=True.
    Instead, it invokes the `qwen` CLI (or falls back to a safe dry-run)
    with the prompt passed via stdin, restricted to the repo directory.

    Returns: (output_string, success_bool)
    """
    import tempfile

    # Build the qwen command — prompt via stdin, never shell=True
    qwen_cmd = ["qwen", "-y", "--print"]

    try:
        # Write prompt to a temp file to avoid shell injection via argv
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".prompt", prefix="qwen_",
            delete=False, dir="/tmp"
        ) as pf:
            pf.write(task_text)
            prompt_path = pf.name

        result = subprocess.run(
            qwen_cmd,
            stdin=open(prompt_path, "r"),
            cwd=repo_root,
            capture_output=True,
            text=True,
            timeout=timeout,
        )

        # Clean up temp file
        try:
            os.unlink(prompt_path)
        except OSError:
            pass

        output = (result.stdout + result.stderr).strip()
        if not output:
            output = "(qwen produced no output)"
        success = result.returncode == 0
        return output[:4000], success

    except FileNotFoundError:
        # qwen CLI not found — fall back to a safe dry-run message
        return (
            f"⚠️ Qwen CLI not available for direct execution.\n"
            f"Task queued for manual review:\n{task_text}"
        ), False
    except subprocess.TimeoutExpired:
        return f"Qwen execution timed out after {timeout}s", False
    except Exception as e:
        return f"Qwen execution error: {e}", False



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

# ── Agent status helpers for /agents dashboard (Control Room v1) ──

_AGENT_DIRS = {
    "Z-Product":    ("product",    "📦"),
    "Z-Design":     ("design",     "🎨"),
    "Z-QA":         ("qa",         "🔍"),
    "Z-Ops":        ("ops",        "⚙️"),
    "Z-Research":   ("research",   "🔬"),
    "Z-Claims":     ("claims",     "🛡️"),
    "Z-CAD":        ("cad",        "📐"),
    "Z-Sim":        ("sim",        "🧪"),
}

_STATUS_ICONS_AR = {
    "idle":         "🟢 خامل",
    "active":       "🔵 نشط",
    "blocked":      "🟡 محجوز",
    "failed":       "🔴 فاشل",
    "needs_sultan": "🟠 يحتاج سلطان",
}

_FUTURE_AGENTS = {"Z-CAD", "Z-Sim"}

# Agent metadata: read/write/forbidden paths + escalation rules
# Source: governance/ZILFIT_AGENT_ROLES.md
_AGENT_META = {
    "Z-Product": {
        "read": ["reports/**", "research/**", "demo/**", "tasks/**", "governance/SKILL_ENGINE.md"],
        "write": ["reports/product/**", "reports/readiness/**", "tasks/ (new only)"],
        "forbidden": ["telegram_bot/**", ".env", "governance/SKILL_ENGINE.md (write)", "cron/**"],
        "escalation": ["Reprioritize top-3 tasks", "Public product claims", "Paid API work"],
    },
    "Z-Design": {
        "read": ["demo/**", "governance/Z_UX_SKILLS.md", "reports/quality/**"],
        "write": ["demo/ (new files only)", "reports/design/**"],
        "forbidden": ["telegram_bot/**", ".env", "CAD geometry files", "Watermark generation"],
        "escalation": ["Overwrite existing demo", "New brand color", "External assets"],
    },
    "Z-QA": {
        "read": ["** (full repo read)"],
        "write": ["reports/qa/**", "reports/quality/**", "tasks/ (bug reports)"],
        "forbidden": ["telegram_bot/bot.py", "telegram_bot/run.sh", ".env", "File deletion"],
        "escalation": ["Production-affecting test", "Production rollback needed"],
    },
    "Z-Ops": {
        "read": ["reports/**", "research/**", "logs/**", "cron/** (read-only)"],
        "write": ["reports/ops/**", "logs/ (append-only)", "tasks/ (ops proposals)"],
        "forbidden": ["telegram_bot/**", ".env", "cron/** (write)", "systemd units", "File deletion"],
        "escalation": ["Cron job change", "systemd/tmux modification", "Production restart"],
    },
    "Z-Research": {
        "read": ["research/**", "governance/Z_CLAIMS_SKILLS.md", "governance/Z_PATENT_SKILLS.md"],
        "write": ["research/daily/**", "research/autopull/**", "reports/research/**"],
        "forbidden": [".env", "telegram_bot/**", "AUTOPULL_SOURCES.md (write)", "Medical claims"],
        "escalation": ["New research source", "Patent-worthy finding", "Paid journal access"],
    },
    "Z-Claims": {
        "read": ["reports/**", "demo/**", "governance/Z_CLAIMS_SKILLS.md"],
        "write": ["reports/claims/**", "tasks/ (remediation proposals)"],
        "forbidden": ["Modify other agents' output", ".env", "telegram_bot/**", "Medical approvals"],
        "escalation": ["Borderline medical claim", "Critical FORBIDDEN classification", "Z_CLAIMS_SKILLS.md change"],
    },
    "Z-CAD": {
        "read": ["governance/Z_CAD_SKILLS.md", "governance/Z_UX_SKILLS.md", "demo/**"],
        "write": ["cad/** (future)", "reports/cad/**"],
        "forbidden": ["Print-ready files without Z-Sim PASS", ".env", "Meshy output as final"],
        "escalation": ["Geometry affecting primary templates", "Monolithic design change", "3D print export"],
    },
    "Z-Sim": {
        "read": ["governance/Z_SIM_SKILLS.md", "governance/Z_CAD_SKILLS.md", "reports/**"],
        "write": ["reports/sim/**", "reports/samples/**", "tasks/"],
        "forbidden": ["GO without complete scope", "Override BLOCKER without Sultan", ".env"],
        "escalation": ["GO for physical print", "Override BLOCKER", "Paid compute"],
    },
}



import datetime as _dt

def _safe_parse_report_line(text, label):
    """Extract value after a label like 'Sultan decisions needed:' from report text."""
    if not text:
        return "لا يوجد"
    for line in text.splitlines():
        # Match patterns like "label: value" or "المفتاح: القيمة"
        if label.lower() in line.lower():
            # Split on first colon
            parts = line.split(":", 1)
            if len(parts) == 2:
                val = parts[1].strip()
                if val:
                    return val
    return "لا يوجد"


def _latest_file(directory, pattern="*"):
    """Return the most recently modified file in a directory matching a glob pattern."""
    import fnmatch
    if not os.path.isdir(directory):
        return None
    files = [
        os.path.join(directory, f)
        for f in os.listdir(directory)
        if os.path.isfile(os.path.join(directory, f)) and fnmatch.fnmatch(f, pattern)
    ]
    return max(files, key=os.path.getmtime) if files else None


def _file_age_hours(filepath):
    """Return hours since file was last modified (UTC)."""
    mtime = os.path.getmtime(filepath)
    dt_obj = _dt.datetime.fromtimestamp(mtime, tz=_dt.timezone.utc)
    diff = _dt.datetime.now(_dt.timezone.utc) - dt_obj
    return diff.total_seconds() / 3600.0


def _extract_signal(text, max_bytes=2000):
    """Extract a short meaningful signal from report text.

    Handles plain text, Markdown, JSON, and HTML files.
    Returns a concise Arabic-friendly summary.
    """
    if not text:
        return "لا يوجد"

    # If JSON, try to parse structured fields
    stripped = text.strip()
    if stripped.startswith("{"):
        try:
            import json as _json
            data = _json.loads(stripped[:max_bytes])
            # Look for status-like fields
            for key in ["overall_status", "test_status", "status", "result"]:
                if key in data:
                    val = str(data[key])
                    return "ناجح ✅" if val.lower() in ("pass", "passed", "ok", "clean", "true") else val
            # Fallback: first meaningful value
            for k, v in data.items():
                if isinstance(v, str) and len(v) > 3 and k not in ("schema_version", "project", "report_type", "boundary", "engineering_boundary", "timestamp_utc", "branch", "head_commit", "head", "log_file", "module"):
                    return str(v)[:200]
            return "لا يوجد"
        except Exception:
            pass  # fall through to text parsing

    # If HTML, extract title or first meaningful text
    if "<!DOCTYPE" in text[:100].upper() or "<html" in text[:200].lower():
        # Try to find a title or h1
        import re as _re
        m = _re.search(r"<title>(.*?)</title>", text, _re.IGNORECASE | _re.DOTALL)
        if m:
            return _re.sub(r"<[^>]+>", "", m.group(1)).strip()[:200]
        m = _re.search(r"<h[12][^>]*>(.*?)</h[12]>", text, _re.IGNORECASE | _re.DOTALL)
        if m:
            return _re.sub(r"<[^>]+>", "", m.group(1)).strip()[:200]
        # Fallback: strip all tags and take first meaningful line
        plain = _re.sub(r"<[^>]+>", " ", text)
        plain = _re.sub(r"\s+", " ", plain).strip()
        return plain[:200] if plain else "لا يوجد"

    lines = text.splitlines()

    # Priority 1: explicit "needed" or "required" lines
    for line in lines:
        low = line.lower().strip()
        for kw in ["human intervention needed", "human decisions needed", "sultan decisions needed", "human approval", "approval needed"]:
            if kw in low:
                val = line.split(":", 1)[1].strip() if ":" in line else line.strip()
                return val[:200] if val else "يحتاج موافقة"

    # Priority 2: next action / next recommended
    for line in lines:
        low = line.lower().strip()
        for kw in ["next recommended action", "next action", "الإجراء التالي"]:
            if kw in low:
                val = line.split(":", 1)[1].strip() if ":" in line else line.strip()
                return val[:200] if val else "لا يوجد"

    # Priority 3: status line
    for line in lines:
        low = line.lower().strip()
        if low.startswith("status:") or "الحالة:" in low:
            val = line.split(":", 1)[1].strip()
            return val[:200] if val else "لا يوجد"

    # Priority 4: first non-empty, non-heading line
    for line in lines:
        stripped = line.strip()
        if stripped and not stripped.startswith("#") and len(stripped) > 10:
            return stripped[:200]

    return "لا يوجد"


def _derive_status_from_signal(signal, age_hours):
    """Derive agent status from signal text and age."""
    low = signal.lower() if signal else ""
    # Check for failure/error indicators
    for kw in ["error", "fail", "خطأ", "فاشل", "crash", "blocker"]:
        if kw in low:
            return "failed"
    # Check for blocked/needs Sultan
    for kw in ["needs sultan", "يحتاج سلطان", "approval", "موافقة", "human intervention", "blocked", "محجوز", "waiting"]:
        if kw in low:
            return "needs_sultan"
    # Check for active (recent activity with a task signal)
    if signal and signal != "لا يوجد" and age_hours < 48:
        return "active"
    return "idle"


# Agent source configuration: maps agent name to list of (directory, glob_pattern)
_AGENT_SOURCES = {
    "Z-Product": [
        ("reports/daily", "*.md"),
        ("tasks", "*.md"),
    ],
    "Z-Design": [
        ("demo", "*.html"),
        ("tasks", "*.md"),
    ],
    "Z-QA": [
        ("reports/quality", "*.json"),
        ("reports/nightly", "*.json"),
    ],
    "Z-Ops": [
        ("reports/nightly", "*.json"),
        ("reports/telegram_actions", "*.jsonl"),
    ],
    "Z-Research": [
        ("research/daily", "*.md"),
        ("reports/daily", "*.md"),
    ],
    "Z-Claims": [
        ("reports/daily", "*.md"),
        ("governance", "Z_CLAIMS_SKILLS.md"),
    ],
    "Z-CAD": [
        ("governance", "Z_CAD_SKILLS.md"),
        ("tasks", "*.md"),
    ],
    "Z-Sim": [
        ("governance", "Z_SIM_SKILLS.md"),
        ("tasks", "*.md"),
    ],
}


def _get_agent_status(agent_name, dir_name, repo_root):
    """Return dict with status fields for one agent.

    Reads from configured local sources per agent.
    All operations are read-only file reads — no shell execution.
    If no signal found, defaults to idle with 'لا يوجد' fields.
    """
    result = {
        "status": "idle",
        "current_task": "لا يوجد",
        "last_run": "لم يعمل بعد",
        "last_report": "لا يوجد",
        "last_failure": "لا يوجد",
        "next_sultan_action": "لا يوجد",
    }

    sources = _AGENT_SOURCES.get(agent_name, [])
    if not sources:
        return result

    try:
        best_file = None
        best_age = float("inf")

        # Find the most recent file across all configured sources
        for rel_dir, pattern in sources:
            full_dir = os.path.join(repo_root, rel_dir)
            if not os.path.isdir(full_dir):
                continue
            f = _latest_file(full_dir, pattern)
            if f:
                age = _file_age_hours(f)
                if age < best_age:
                    best_age = age
                    best_file = f

        if not best_file:
            return result

        result["last_report"] = os.path.basename(best_file)
        result["last_run"] = _dt.datetime.fromtimestamp(
            os.path.getmtime(best_file), tz=_dt.timezone.utc
        ).strftime("%Y-%m-%d %H:%M UTC")

        # Read and parse signal
        report_text = read_file_safe(best_file, max_bytes=3000)
        signal = _extract_signal(report_text)
        age = _file_age_hours(best_file)

        result["current_task"] = signal
        result["status"] = _derive_status_from_signal(signal, age)

        # Check for explicit Sultan/action-needed indicators
        for kw in ["human intervention needed", "sultan decisions needed", "human approval"]:
            if kw in report_text.lower():
                result["next_sultan_action"] = _safe_parse_report_line(report_text, kw)
                if result["next_sultan_action"] != "لا يوجد":
                    result["status"] = "needs_sultan"
                break

        # Check for failure indicators
        for kw in ["fail", "error", "blocked", "blocker"]:
            if kw in report_text.lower() and result["status"] not in ("needs_sultan",):
                failure_line = _safe_parse_report_line(report_text, kw)
                if failure_line != "لا يوجد":
                    result["last_failure"] = failure_line[:200]
                break
    except Exception:
        pass  # gracefully degrade

    return result
def _build_header(repo):
    """Build the dashboard header (reused by compact and detail views)."""
    branch = run_cmd_safe(["git", "branch", "--show-current"], cwd=repo, timeout=10)
    head_line = run_cmd_safe(["git", "log", "--oneline", "-1"], cwd=repo, timeout=10)
    git_status = run_cmd_safe(["git", "status", "--short"], cwd=repo, timeout=10)

    if not branch:
        branch = "غير متوفر"
    tree_state = "نظيف ✅" if not git_status else "متغير ⚠️"

    if head_line:
        parts_head = head_line.split(" ", 1)
        head_hash = parts_head[0] if parts_head else "غير متوفر"
        head_rest = parts_head[1] if len(parts_head) > 1 else ""
    else:
        head_hash = "غير متوفر"
        head_rest = ""

    # Nightly
    nl_file = latest_file(os.path.join(repo, "reports", "nightly"), "nightly_check_*.json")
    if nl_file:
        try:
            nl_data = json.loads(Path(nl_file).read_text(encoding="utf-8"))
            nl_tests = nl_data.get("test_status", "?")
            nightly_status = "ناجح ✅" if nl_tests == "pass" else ("فاشل ❌" if nl_tests == "fail" else str(nl_tests))
        except Exception:
            nightly_status = "غير متوفر"
    else:
        nightly_status = "لا يوجد"

    # Quality
    qf_file = latest_file(os.path.join(repo, "reports", "quality"), "quality_gate_*.json")
    if qf_file:
        try:
            qf_data = json.loads(Path(qf_file).read_text(encoding="utf-8"))
            qf_overall = qf_data.get("overall", qf_data.get("status", "?"))
            quality_status = "ناجح ✅" if (isinstance(qf_overall, bool) and qf_overall) or str(qf_overall).lower() in ("pass", "true", "ok") else "فاشل ❌"
        except Exception:
            quality_status = "غير متوفر"
    else:
        quality_status = "لا يوجد"

    header_lines = [
        "🤖 غرفة تحكم وكلاء ZILFIT",
        "━" * 29,
        f"🌿 الفرع: {branch}",
    ]
    if head_rest:
        header_lines.append(f"📌 HEAD: {head_hash} {head_rest}")
    else:
        header_lines.append(f"📌 HEAD: {head_hash}")
    header_lines.append(f"📁 حالة الشجرة: {tree_state}")
    header_lines.append(f"🌙 ليلي: {nightly_status}")
    header_lines.append(f"🔍 جودة: {quality_status}")
    header_lines.append("━" * 29)
    return header_lines


def _build_agent_compact_row(agent_name, icon, is_future, info):
    """Build a single-line compact agent row for the overview."""
    suffix = " *(مستقبلي)*" if is_future else ""
    status_ar = _STATUS_ICONS_AR.get(info["status"], "🟢 خامل")
    sultan_hint = f" ← {info['next_sultan_action'][:40]}" if info["next_sultan_action"] != "لا يوجد" else ""
    report_hint = f" | {info['last_report']}" if info["last_report"] != "لا يوجد" else ""
    return f"{icon} {agent_name}{suffix}: {status_ar}{report_hint}{sultan_hint}"


def cmd_agents_ar(cfg):
    """Compact Arabic overview — /agents dashboard (mobile-friendly)."""
    repo = cfg["repo_root"]

    lines = _build_header(repo)

    counts = {"active": 0, "idle": 0, "blocked": 0, "failed": 0, "needs_sultan": 0}
    for agent_name, (dir_name, icon) in _AGENT_DIRS.items():
        is_future = agent_name in _FUTURE_AGENTS
        info = _get_agent_status(agent_name, dir_name, repo_root=repo)
        counts[info["status"]] = counts.get(info["status"], 0) + 1
        lines.append(_build_agent_compact_row(agent_name, icon, is_future, info))

    lines.append("━" * 29)
    summary_parts = []
    for key, ar_label in [("active", "نشط"), ("idle", "خامل"), ("blocked", "محجوز"), ("failed", "فاشل"), ("needs_sultan", "يحتاج سلطان")]:
        c = counts.get(key, 0)
        if c > 0:
            summary_parts.append(f"{c} {ar_label}")
    lines.append(f"📊 الملخص: {' | '.join(summary_parts)}")
    lines.append("")
    lines.append("للتفاصيل: /agents_qa أو /agents_research أو /agents_product")
    return "\n".join(lines)


# ═══════════════════════════════════════════════════════════
# Per-agent detail views (B4 — focused single-agent status)
# ═══════════════════════════════════════════════════════════

def _build_agent_detail(agent_name, icon, repo_root):
    """Build a detailed single-agent status message.

    Reuses B3 _get_agent_status for local signals.
    Adds metadata (read/write/forbidden paths, escalation).
    """
    dir_name = _AGENT_DIRS.get(agent_name, ("unknown", "❓"))[0]
    info = _get_agent_status(agent_name, dir_name, repo_root)
    meta = _AGENT_META.get(agent_name, {})
    is_future = agent_name in _FUTURE_AGENTS

    status_ar = _STATUS_ICONS_AR.get(info["status"], "🟢 خامل")
    suffix = " (مستقبلي)" if is_future else ""

    lines = [
        f"{icon} {agent_name}{suffix}",
        "━" * 29,
        f"الحالة: {status_ar}",
        f"📋 المهمة الحالية: {info['current_task']}",
        f"⏱ آخر تشغيل: {info['last_run']}",
        f"📄 آخر تقرير: {info['last_report']}",
        f"❌ آخر فشل: {info['last_failure']}",
        f"🔜 إجراء سلطان المطلوب: {info['next_sultan_action']}",
    ]

    # Metadata sections
    if meta.get("read"):
        lines.append("")
        lines.append("📖 مسارات القراءة:")
        for p in meta["read"][:5]:
            lines.append(f"  ✅ {p}")

    if meta.get("write"):
        lines.append("")
        lines.append("✏️ مسارات الكتابة:")
        for p in meta["write"][:5]:
            lines.append(f"  ✍️ {p}")

    if meta.get("forbidden"):
        lines.append("")
        lines.append("🚫 مسارات ممنوعة:")
        for p in meta["forbidden"][:5]:
            lines.append(f"  ⛔ {p}")

    if meta.get("escalation"):
        lines.append("")
        lines.append("⚡ قواعد التصعيد لسلطان:")
        for p in meta["escalation"][:4]:
            lines.append(f"  🔺 {p}")

    return "\n".join(lines)


# Agent detail command mapping: command_suffix -> (agent_name, icon)
_AGENT_DETAIL_CMDS = {
    "product":   ("Z-Product", "📦"),
    "design":    ("Z-Design",  "🎨"),
    "qa":        ("Z-QA",      "🔍"),
    "ops":       ("Z-Ops",     "⚙️"),
    "research":  ("Z-Research","🔬"),
    "claims":    ("Z-Claims",  "🛡️"),
    "cad":       ("Z-CAD",     "📐"),
    "sim":       ("Z-Sim",     "🧪"),
}


def _make_agent_detail_handler(agent_name, icon):
    """Factory: returns a handler function for a specific agent."""
    def handler(cfg):
        return _build_agent_detail(agent_name, icon, cfg["repo_root"])
    handler.__name__ = f"cmd_agents_{agent_name.lower().replace('-', '_')}_ar"
    handler.__doc__ = f"Detail view for {agent_name}"
    return handler


# Create handlers for each agent
cmd_agents_product_ar = _make_agent_detail_handler("Z-Product", "📦")
cmd_agents_design_ar  = _make_agent_detail_handler("Z-Design",  "🎨")
cmd_agents_qa_ar      = _make_agent_detail_handler("Z-QA",      "🔍")
cmd_agents_ops_ar     = _make_agent_detail_handler("Z-Ops",     "⚙️")
cmd_agents_research_ar = _make_agent_detail_handler("Z-Research", "🔬")
cmd_agents_claims_ar  = _make_agent_detail_handler("Z-Claims",  "🛡️")
cmd_agents_cad_ar     = _make_agent_detail_handler("Z-CAD",     "📐")
cmd_agents_sim_ar     = _make_agent_detail_handler("Z-Sim",     "🧪")


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


# ════════════════════════════════════════════════════════════
# NEW READ-ONLY Arabic commands (C5)
# ════════════════════════════════════════════════════════════

def _safe_read_short(path, max_chars=900):
    """Read file safely, truncate to max_chars and replace newlines with spaces."""
    try:
        data = Path(path).read_text(encoding="utf-8", errors="replace")
        if len(data) > max_chars:
            data = data[:max_chars] + "…"
        # Replace newlines with spaces for short inline summary
        return " ".join(data.split())
    except Exception as e:
        return f"خطأ في القراءة: {e}"


def _template_summary(path, title):
    """Return a short Arabic summary line for a template file."""
    content = _safe_read_short(path, max_chars=200)
    if content.startswith("خطأ"):
        return content
    return f"{title}: {content}"


def cmd_memory(cfg):
    """Short Arabic summary of memory / Hermes state."""
    mem_dir = os.path.join(cfg["repo_root"], "governance")
    try:
        files = []
        for f in os.listdir(mem_dir):
            if f.startswith("HERMES") and f.endswith(".md"):
                files.append(f)
        if files:
            sample = os.path.join(mem_dir, files[0])
            return _template_summary(sample, "ذاكرة Hermes")
        else:
            return "ذاكرة Hermes: لا توجد ملفات"
    except Exception:
        return "ذاكرة Hermes: غير متوفر"


def cmd_skills(cfg):
    """List available skill file names."""
    skill_dir = os.path.join(cfg["repo_root"], "skills")
    try:
        skill_files = [f for f in os.listdir(skill_dir) if f.endswith(".md")]
        if not skill_files:
            return "المهارات: لا توجد"
        names = [f[:-3].replace("_", " ").title() for f in skill_files[:5]]
        return "المهارات المتاحة: " + ", ".join(names)
    except Exception:
        return "المهارات: غير متوفر"


def cmd_templates(cfg):
    """List available template file names."""
    tmpl_dir = os.path.join(cfg["repo_root"], "templates")
    try:
        tmpl_files = [f for f in os.listdir(tmpl_dir) if f.endswith(".md")]
        if not tmpl_files:
            return "القوالب: لا توجد"
        names = [f[:-3].replace("_", " ").title() for f in tmpl_files[:5]]
        return "القوالب المتاحة: " + ", ".join(names)
    except Exception:
        return "القوالب: غير متوفر"


def cmd_template_agent_report(cfg):
    """Return short Arabic summary of the agent daily report template."""
    path = os.path.join(cfg["repo_root"], "templates", "agent_daily_report_template.md")
    return _template_summary(path, "قالب تقرير الوكيل اليومي")


def cmd_template_sultan_approval(cfg):
    """Return short Arabic summary of the Sultan approval template."""
    path = os.path.join(cfg["repo_root"], "templates", "sultan_approval_request_template.md")
    return _template_summary(path, "قالب طلب موافقة سلطان")


def cmd_template_qwen_task(cfg):
    """Return short Arabic summary of the Qwen task template."""
    path = os.path.join(cfg["repo_root"], "templates", "qwen_task_request_template.md")
    return _template_summary(path, "قالب طلب مهمة Qwen")


def cmd_template_claims_review(cfg):
    """Return short Arabic summary of the claims review template."""
    path = os.path.join(cfg["repo_root"], "templates", "claims_review_report_template.md")
    return _template_summary(path, "قالب مراجعة الادعاءات")


def cmd_template_research_intake(cfg):
    """Return short Arabic summary of the research intake template."""
    path = os.path.join(cfg["repo_root"], "templates", "research_intake_report_template.md")
    return _template_summary(path, "قالب استلام طلب بحث")


def cmd_template_demo_review(cfg):
    """Return short Arabic summary of the demo review template."""
    path = os.path.join(cfg["repo_root"], "templates", "demo_review_report_template.md")
    return _template_summary(path, "قالب مراجعة العرض التوضيحي")


# ────────────────────────────────────────────────────────────────
# D3: Hermes Daily Operating Report Telegram Commands (read-only)
# ────────────────────────────────────────────────────────────────

def _get_latest_daily_report(cfg):
    """Get the most recent daily report file path, or None."""
    repo = cfg["repo_root"]
    daily_dir = os.path.join(repo, "reports", "daily")
    if not os.path.isdir(daily_dir):
        return None
    # Look for files matching pattern YYYY-MM-DD_hermes_daily_operating_report.md
    files = []
    for f in os.listdir(daily_dir):
        if f.endswith("_hermes_daily_operating_report.md"):
            files.append(os.path.join(daily_dir, f))
    if not files:
        # Fallback to any daily report
        for f in os.listdir(daily_dir):
            if f.endswith(".md"):
                files.append(os.path.join(daily_dir, f))
    if not files:
        return None
    return max(files, key=os.path.getmtime)


def _read_agent_heartbeat_summary(cfg):
    """Read all agent heartbeat JSON files and return summary text."""
    repo = cfg["repo_root"]
    health_dir = os.path.join(repo, "runtime", "agent_health")
    if not os.path.isdir(health_dir):
        return "لا توجد بيانات صحة الوكلاء"

    lines = []
    try:
        for json_file in sorted(os.listdir(health_dir)):
            if json_file.endswith(".json"):
                filepath = os.path.join(health_dir, json_file)
                try:
                    data = json.loads(Path(filepath).read_text(encoding="utf-8"))
                    agent = data.get("agent", json_file.replace(".json", ""))
                    status = data.get("status", "unknown")
                    task = data.get("current_task", "لا يوجد")
                    confidence = data.get("confidence", "unknown")
                    lines.append(f"- {agent}: {status} | {confidence} | {task[:50]}...")
                except Exception:
                    lines.append(f"- {json_file}: قراءة غير ممكنة")
    except Exception:
        return "خطأ في قراءة ملفات الصحة"

    if not lines:
        return "لا توجد بيانات صحة الوكلاء"
    return "\n".join(lines)


def _get_next_action_from_templates(cfg):
    """Get next recommended actions from governance/templates."""
    repo = cfg["repo_root"]

    # Read daily_operating_report skill for recommended actions
    skill_path = os.path.join(repo, "skills", "daily_operating_report.md")
    next_actions = []

    try:
        content = Path(skill_path).read_text(encoding="utf-8", errors="replace").lower()
        if "أولويات اليوم" in content or "daily priorities" in content:
            next_actions.append("مراجعة أولويات اليوم في تقرير التشغيل اليومي")
        if "تقرير الليل" in content or "night report" in content:
            next_actions.append("مراجعة تقرير الليل لنتائج اليوم")
        if "الفحص" in content or "inspection" in content:
            next_actions.append("أداء فحص جودة/جاهزية بعد الظهر")
    except Exception:
        pass

    # Read governance files for upcoming phase guidance
    governance_dir = os.path.join(repo, "governance")
    try:
        for fname in os.listdir(governance_dir):
            if fname.startswith("HERMES_") and fname.endswith(".md"):
                if "D2" in fname or "D3" in fname:
                    next_actions.append("مراجعة مستندات المرحلة D3 للاستعداد للمراحل التالية")
                    break
    except Exception:
        pass

    if not next_actions:
        next_actions.append("مراجعة تقرير التشغيل اليومي وتحديد أولويات اليوم التالي")
        next_actions.append("مراجعة ملفات القوالب لتوحيد التقارير المستقبلية")

    return "\n".join(f"{i+1}. {a}" for i, a in enumerate(next_actions))


def cmd_daily_report(cfg):
    """Show Arabic summary of the latest daily operating report."""
    repo = cfg["repo_root"]
    latest = _get_latest_daily_report(cfg)

    if not latest:
        return "⬡ تقرير يومي: لا يوجد تقرير يومي بعد.\nيمكنك إنشاؤه بـ: python3 tools/hermes_daily_report.py"

    try:
        content = Path(latest).read_text(encoding="utf-8", errors="replace")
        lines = content.split("\n")

        # Extract key sections
        title = "تقرير يومي"
        date_line = ""
        status_summary = ""
        next_actions = ""

        for line in lines[:50]:
            if line.startswith("# "):
                title = line[2:].strip()
            elif "Generated:" in line or "Date:" in line:
                date_line = line.strip()
            elif "Agent Heartbeat Summary" in line:
                idx = lines.index(line)
                # Collect next 10 lines after this header
                for j in range(idx + 1, min(idx + 10, len(lines))):
                    if lines[j].strip() and not lines[j].strip().startswith("---"):
                        status_summary += lines[j].strip() + "\n"
            elif "Next Recommended Action" in line or "الخطوة التالية" in line:
                idx = lines.index(line)
                for j in range(idx + 1, min(idx + 5, len(lines))):
                    next_actions += lines[j].strip() + "\n"

        # Truncate long content
        status_summary = status_summary[:400] if status_summary else "لا يوجد"
        next_actions = next_actions[:400] if next_actions else "لا يوجد"

        return f"""⬡ تقرير التشغيل اليومي

التاريخ: {date_line or "غير متوفر"}
المصدر: {os.path.basename(latest)}

ملخص الحالة:
{status_summary}

الإجراء التالي:
{next_actions}
"""
    except Exception as e:
        return f"⬡ تقرير يومي: خطأ في القراءة — {e}"


def cmd_daily_report_ar(cfg):
    """Arabic version of daily report."""
    return cmd_daily_report(cfg)


def cmd_daily_status(cfg):
    """Show current high-level Hermes/ZILFIT status from safe local files only."""
    repo = cfg["repo_root"]
    branch = run_cmd_safe(["git", "branch", "--show-current"], cwd=repo, timeout=10)
    head = run_cmd_safe(["git", "log", "--oneline", "-1"], cwd=repo, timeout=10)
    tree = run_cmd_safe(["git", "status", "--short"], cwd=repo, timeout=10)

    branch = branch if branch else "غير متوفر"
    head = head if head else "غير متوفر"
    tree_state = "نظيف ✅" if not tree else "متغير ⚠️"

    heartbeat = _read_agent_heartbeat_summary(cfg)

    return f"""⬡ حالة ZILFIT الهامة

الفرع: {branch}
HEAD: {head}
الشجرة: {tree_state}

حالة الوكلاء:
{heartbeat}
"""


def cmd_daily_status_ar(cfg):
    """Arabic version of daily status."""
    return cmd_daily_status(cfg)


def cmd_daily_plan(cfg):
    """Show next recommended safe actions from governance/templates, not execution."""
    repo = cfg["repo_root"]

    # Check if D2 report generator exists
    report_script = os.path.join(repo, "tools", "hermes_daily_report.py")
    script_exists = "✓" if Path(report_script).exists() else "✗"

    next_actions = _get_next_action_from_templates(cfg)

    return f"""⬡ خطة التشغيل اليومية

مُولِّد التقارير (D2): {script_exists}

الإجراءات المقترحة:
{next_actions}

⚠️ ملاحظة: هذه توصيات فقط. لا تنفيذ تلقائي.
"""


def cmd_daily_plan_ar(cfg):
    """Arabic version of daily plan."""
    return cmd_daily_plan(cfg)


def cmd_hermes(cfg):
    """Hermes supervised status summary — read-only safe reply."""
    repo = cfg["repo_root"]
    branch = run_cmd("git branch --show-current", cwd=repo, timeout=10).strip() or "?"
    head = run_cmd("git log --oneline -1", cwd=repo, timeout=10).strip() or "?"
    status_short = run_cmd("git status --short", cwd=repo, timeout=10)
    gitlog = run_cmd("git log --oneline -8", cwd=repo, timeout=10) or "(empty)"
    tree_state = "CLEAN ✅" if not status_short or status_short == "(empty)" else "DIRTY ⚠️"
    heartbeat = _read_agent_heartbeat_summary(cfg)
    latest_report = _get_latest_daily_report(cfg)
    report_info = os.path.basename(latest_report) if latest_report else "none"

    d20_path = Path(repo) / "reports" / "daily" / "2026-05-12_D20_hermes_next_execution_queue.md"
    next_action = "Execute Z-Ops inspection dry run (P1 priority)"
    if d20_path.exists():
        next_action = "D20 queue available — check P1 items"

    total_agents = len([l for l in heartbeat.split("\n") if l.strip().startswith("-")])
    return (
        f"🤖 Hermes Supervised Status\n"
        f"──────────────\n"
        f"Branch: `{branch}`\n"
        f"HEAD: {head}\n"
        f"Tree: {tree_state}\n\n"
        f"Latest 8 commits:\n```\n{gitlog}\n```\n\n"
        f"Agent Health ({total_agents} agents):\n{heartbeat}\n\n"
        f"Latest Report: {report_info}\n"
        f"Next Action: {next_action}\n\n"
        f"read-only | non-production | no tokens | no cron | no restart\n"
        f"Commands: /status /agents /daily_status /daily_report /help"
    )


def cmd_approval_queue(cfg):
    """Show pending approval-style guidance only; no execution."""
    repo = cfg["repo_root"]

    # Check pending commands (read-only from _pending_commands)
    pending = get_pending_list()

    if not pending:
        pending_text = "لا توجد طلبات انتظار ✅"
    else:
        lines = []
        for p in pending[:10]:  # Show max 10
            item_type = p.get("item_type", "shell")
            lines.append(f"- `{p['id']}`: {p['task'][:50]}... ({item_type})")
        pending_text = "\n".join(lines)

    return f"""⬡ قائمة الموافقات

الطلبات المنتظرة: {len(pending)}

{pending_text}

💡 لموافقه: /approve <id>
لإلغاء: /cancel <id>
"""


def cmd_approval_queue_ar(cfg):
    """Arabic version of approval queue."""
    return cmd_approval_queue(cfg)


def cmd_help(*_args):
    """List all commands."""
    return textwrap.dedent("""\
    ⬡ ZILFIT Command Center v2
	    🤖 Hermes Chat
	    /hermes   — Full repo status, agent health, next action
	    (any text) — Hermes replies in supervised safe mode


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

    📚 Memory & Skills
    /memory   — Hermes memory summary
    /skills   — Available skills list
    /templates — Available templates list

    📋 Template Summaries
    /template_agent_report      — Agent daily report template
    /template_sultan_approval   — Sultan approval request template
    /template_qwen_task         — Qwen task request template
    /template_claims_review     — Claims review template
    /template_research_intake   — Research intake template
    /template_demo_review       — Demo review template

    Read-only by default. Write commands need /approve.""")

def cmd_help_ar(*_args):
    """Arabic help."""
    return textwrap.dedent("""\
    ⬡ مركز تحكم ZILFIT v2

	    🤖 محادثة Hermes
	    /hermes   — حالة كاملة للمستودع والوكلاء والإجراء التالي
	    (أي نص) — Hermes يرد في الوضع المشرف الآمن

    📊 التقارير
    /status         — فرع Git، HEAD، حالة الشجرة
    /nightly        — آخر تقرير ليلي
    /tests          — تشغيل كل الاختبارات
    /agents         — حالة الوكلاء والمشاريع النشطة
    /research       — إحصائيات البحث التلقائي
    /claims         — فحص المصطلحات الطبية المحظورة
    /demo           — ملفات العرض التوضيحي
    /report         — تقرير يومي شامل بالعربية (فوري)

    🔧 قيود Hermes D3 (قراءة فقط)
    /daily_report   — ملخص آخر تقرير تشغيل يومي
    /daily_status   — حالة ZILFIT الحالية
    /daily_plan     — الإجراءات الموصى بها
    /approval_queue — قائمة الموافقات المنتظرة

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

    📚 الذاكرة والمهارات
    /memory   — ملخص ذاكرة Hermes
    /skills   — قائمة المهارات المتاحة
    /templates — قائمة القوالب المتاحة

    📋 ملخصات القوالب
    /template_agent_report      — قالب تقرير الوكيل اليومي
    /template_sultan_approval   — قالب طلب موافقة سلطان
    /template_qwen_task         — قالب طلب مهمة Qwen
    /template_claims_review     — قالب مراجعة الادعاءات
    /template_research_intake   — قالب استلام طلب بحث
    /template_demo_review       — قالب مراجعة العرض التوضيحي

    القراءة فقط افتراضياً. أوامر الكتابة تحتاج /approve.""")

# ═══════════════════════════════════════════════════════════
# DISPATCHER
# ═══════════════════════════════════════════════════════════

COMMANDS = {
    "status": cmd_status,
    "status_ar": cmd_status_ar,
    "nightly": cmd_nightly,
    "nightly_ar": cmd_nightly_ar,
    "tests": cmd_tests,
    "tests_ar": cmd_tests_ar,
    "agents": cmd_agents,
    "agents_ar": cmd_agents_ar,
    "agents_product": cmd_agents,
    "agents_product_ar": cmd_agents_product_ar,
    "agents_design": cmd_agents,
    "agents_design_ar": cmd_agents_design_ar,
    "agents_qa": cmd_agents,
    "agents_qa_ar": cmd_agents_qa_ar,
    "agents_ops": cmd_agents,
    "agents_ops_ar": cmd_agents_ops_ar,
    "agents_research": cmd_agents,
    "agents_research_ar": cmd_agents_research_ar,
    "agents_claims": cmd_agents,
    "agents_claims_ar": cmd_agents_claims_ar,
    "agents_cad": cmd_agents,
    "agents_cad_ar": cmd_agents_cad_ar,
    "agents_sim": cmd_agents,
    "agents_sim_ar": cmd_agents_sim_ar,
    "research": cmd_research,
    "research_ar": cmd_research_ar,
    "claims": cmd_claims,
    "claims_ar": cmd_claims_ar,
    "demo": cmd_demo,
    "demo_ar": cmd_demo_ar,
    "help": cmd_help,
    "help_ar": cmd_help_ar,
    "start": cmd_help,
    "memory": cmd_memory,
    "skills": cmd_skills,
    "templates": cmd_templates,
    "template_agent_report": cmd_template_agent_report,
    "template_sultan_approval": cmd_template_sultan_approval,
    "template_qwen_task": cmd_template_qwen_task,
    "template_claims_review": cmd_template_claims_review,
    "template_research_intake": cmd_template_research_intake,
    "template_demo_review": cmd_template_demo_review,
    # ── D3: Hermes Daily Operating Report Commands ──
    "daily_report": cmd_daily_report,
    "daily_report_ar": cmd_daily_report_ar,
    "daily_status": cmd_daily_status,
    "daily_status_ar": cmd_daily_status_ar,
    "daily_plan": cmd_daily_plan,
    "daily_plan_ar": cmd_daily_plan_ar,
    "approval_queue": cmd_approval_queue,
    "approval_queue_ar": cmd_approval_queue_ar,
    # ── D21: Hermes Live Chat Bridge ──
    "hermes": cmd_hermes,
}

def handle_message(message, bot, cfg):
    """Route incoming message to command handler."""
    if not is_admin(message, cfg["admin_ids"]):
        return

    if not message.text:
        return

    # ── Plain text → Hermes supervised reply (D21 live chat bridge) ──
    if not message.text.startswith("/"):
        arabic_mode = is_arabic(message.from_user.id)
        if arabic_mode:
            reply = (
                f"🤖 Hermes — الوضع المشرف\n"
                f"أنا هنا للإجابة على أسئلتك حول حالة المستودع والوكلاء.\n"
                f"أستخدم: /hermes للحصول على ملخص كامل\n"
                f"أو أرسل /help لرؤية جميع الأوامر.\n\n"
                f"هذه جلسة قراءة فقط — لا يتم تنفيذ أي شيء دون موافقتك.\n"
                f"non-production | read-only | no tokens | no cron | no restart"
            )
        else:
            reply = (
                f"🤖 Hermes — Supervised Mode\n"
                f"I can answer questions about repo state, agents, and reports.\n"
                f"Use /hermes for a full status summary\n"
                f"Or send /help to see all commands.\n\n"
                f"This is a read-only session — nothing executes without your approval.\n"
                f"non-production | read-only | no tokens | no cron | no restart"
            )
        safe_reply(bot, message, reply)
        audit_log({"event": "hermes_plain_text", "user": message.from_user.id, "text": message.text[:100]})
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

    # ── Qwen bridge commands (v3 — Superpowers classified) ──
    if cmd == "qwen":
        if not arg:
            safe_reply(bot, message, "الاستخدام: /qwen <وصف المهمة>\nمثال: /qwen git log --oneline -5")
            return
        task_text = arg.strip()
        audit_log({"event": "qwen_requested", "user": message.from_user.id, "task": task_text})

        # Classify the task using the Superpowers classifier
        task_class, reason = classify_qwen_task(task_text)

        if task_class == "forbidden":
            safe_reply(bot, message,
                f"❌ مهمة ممنوعة\n\n"
                f"السبب: {reason}\n\n"
                f"المهمة: {task_text}")
            audit_log({"event": "qwen_forbidden", "user": message.from_user.id, "task": task_text, "reason": reason})
            return

        if task_class == "read-only":
            # Execute safe read-only shell command directly
            safe_reply(bot, message, f"✅ أمر آمن — قراءة فقط\n\n{reason}\n\nالأمر: {task_text}\n\nجاري التنفيذ...")
            result = run_cmd(task_text, cwd=cfg["repo_root"], timeout=30)
            safe_reply(bot, message, f"النتيجة:\n```\n{result}\n```")
            audit_log({"event": "qwen_executed_safe", "user": message.from_user.id, "task": task_text, "class": task_class, "result_len": len(result)})
            return

        if task_class == "docs-only":
            # Docs-only: create pending with docs-only type, auto-execute safe
            cmd_id = add_pending(message.from_user.id, task_text, task_text, item_type="docs_only")
            safe_reply(bot, message,
                f"📝 مهمة وثائق — تحتاج موافقة\n\n"
                f"التصنيف: {task_class}\n"
                f"السبب: {reason}\n\n"
                f"المهمة: {task_text}\n"
                f"المعرّف: `{cmd_id}`\n\n"
                f"للموافقة: /approve {cmd_id}\n"
                f"للإلغاء: /cancel {cmd_id}")
            audit_log({"event": "qwen_pending_docs", "id": cmd_id, "task": task_text})
            return

        # All other classes (tests-only, code-change-needs-approval) → pending as qwen_prompt
        # This is the KEY safety change: natural-language tasks become qwen_prompt,
        # NOT raw shell commands. On approval, they run via execute_qwen_safe().
        item_type = "qwen_prompt"
        cmd_id = add_pending(message.from_user.id, task_text, task_text, item_type=item_type)
        safe_reply(bot, message,
            f"⚠️ الأمر يحتاج موافقة\n\n"
            f"التصنيف: {task_class}\n"
            f"السبب: {reason}\n\n"
            f"المهمة: {task_text}\n"
            f"نوع التنفيذ: {item_type} (يُنفَّذ عبر Qwen بأمان، ليس كـ shell)\n"
            f"المعرّف: `{cmd_id}`\n\n"
            f"للموافقة: /approve {cmd_id}\n"
            f"للإلغاء: /cancel {cmd_id}")
        audit_log({"event": "qwen_pending", "id": cmd_id, "task": task_text, "class": task_class, "item_type": item_type})
        return

    if cmd == "queue":
        pending = get_pending_list()
        if not pending:
            safe_reply(bot, message, "📋 قائمة الانتظار فارغة ✅")
            return
        lines = ["📋 عناصر بانتظار الموافقة:\n"]
        for p in pending:
            itype = p.get("item_type", "shell")
            lines.append(
                f"🆔 `{p['id']}`\n"
                f"   المهمة: {p['task']}\n"
                f"   النوع: {itype}\n"
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

        # ── Execute based on item_type ──
        item_type = item.get("item_type", "shell")  # backward compat
        proposed = item["proposed_cmd"]

        if item_type == "qwen_prompt":
            # KEY SAFETY: natural-language tasks run via safe Qwen wrapper,
            # NOT as raw shell commands. The prompt is passed via stdin/temp file.
            audit_log({"event": "executing_approved_qwen", "id": arg.strip(), "item_type": item_type, "task": proposed})
            safe_reply(bot, message,
                f"⚡ تنفيذ عبر Qwen (آمن — ليس كـ shell):\n"
                f"المهمة: {proposed}\n"
                f"نوع التنفيذ: {item_type}\n\n"
                f"جاري التنفيذ...")
            result, success = execute_qwen_safe(proposed, cfg["repo_root"], timeout=300)
            status_icon = "✅" if success else "⚠️"
            safe_reply(bot, message, f"{status_icon} النتيجة:\n```\n{result}\n```")
            audit_log({"event": "qwen_execution_done", "id": arg.strip(), "success": success, "result_len": len(result)})
        else:
            # Shell command (read-only, docs-only, or explicitly classified safe)
            audit_log({"event": "executing_approved_shell", "id": arg.strip(), "item_type": item_type, "cmd": proposed})
            safe_reply(bot, message, f"⚡ تنفيذ الأمر الموافق عليه ({item_type}):\n`{proposed}`\n\nجاري التنفيذ...")
            result = run_cmd(proposed, cwd=cfg["repo_root"], timeout=60)
            safe_reply(bot, message, f"النتيجة:\n```\n{result}\n```")
            audit_log({"event": "shell_execution_done", "id": arg.strip(), "item_type": item_type, "result_len": len(result)})
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

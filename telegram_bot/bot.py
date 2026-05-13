#!/usr/bin/env python3
import json
import os
import time
import traceback
import urllib.request
import urllib.error
from pathlib import Path

try:
    import telebot
except Exception as e:
    raise SystemExit(f"Missing dependency telebot: {e}")


def load_env(path=".env"):
    p = os.path.abspath(path)
    if not os.path.exists(p):
        return
    with open(p, "r", encoding="utf-8", errors="replace") as f:
        for raw in f:
            line = raw.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            k, v = line.split("=", 1)
            k = k.strip()
            v = v.strip()
            if len(v) >= 2 and ((v[0] == v[-1] == '"') or (v[0] == v[-1] == "'")):
                v = v[1:-1]
            if k and k not in os.environ:
                os.environ[k] = v


load_env()

BOT_TOKEN = (
    os.environ.get("ZILFIT_TELEGRAM_BOT_TOKEN")
    or os.environ.get("TELEGRAM_BOT_TOKEN")
    or ""
).strip()

OPENROUTER_KEY = (
    os.environ.get("HERMES_LLM_API_KEY")
    or os.environ.get("OPENROUTER_API_KEY")
    or ""
).strip()

OPENROUTER_URL = (
    os.environ.get("HERMES_LLM_BASE_URL")
    or "https://openrouter.ai/api/v1/chat/completions"
).strip()

OPENROUTER_MODEL = (
    os.environ.get("HERMES_LLM_MODEL")
    or "inclusionai/ring-2.6-1t:free"
).strip()

if not BOT_TOKEN:
    raise SystemExit("Missing ZILFIT_TELEGRAM_BOT_TOKEN in .env")

if not OPENROUTER_KEY:
    raise SystemExit("Missing HERMES_LLM_API_KEY in .env")

bot = telebot.TeleBot(BOT_TOKEN, parse_mode=None)


SYSTEM_PROMPT = """أنت Hermes، مساعد ZILFIT التشغيلي عبر تيليجرام.
أجب بالعربية بشكل مباشر وعملي.
لا تستخدم أوامر محلية.
لا تدعي أنك فحصت السيرفر أو الملفات إلا إذا أرسل المستخدم نتائج فعلية داخل المحادثة.
إذا طلب المستخدم تنفيذ عمل تقني، أعطه أمر واحد آمن وواضح ثم اطلب منه النتيجة.
ركّز على ZILFIT، Hermes، OpenRouter، وإدارة المشروع.
"""


def load_project_context() -> str:
    """Return live ZILFIT/Hermes context. Do not rely on old hardcoded D20/D21 reports."""
    import subprocess
    from pathlib import Path

    def run(cmd, timeout=8):
        try:
            return subprocess.check_output(
                cmd,
                shell=True,
                cwd=Path(__file__).resolve().parents[1],
                stderr=subprocess.STDOUT,
                text=True,
                timeout=timeout,
            ).strip()
        except Exception as e:
            return f"ERROR: {e}"

    root = Path(__file__).resolve().parents[1]

    branch = run("git branch --show-current")
    head = run("git log -1 --oneline --decorate")
    status = run("git status --short")
    tree_state = "CLEAN" if not status else "DIRTY"

    bot_proc = run("ps -eo pid,ppid,etime,cmd | grep -E 'telegram_bot/bot.py|zilfit_master_bot.py' | grep -v grep || true")
    tmux_state = run("tmux ls 2>/dev/null || true")

    env_lines = []
    env_path = root / ".env"
    if env_path.exists():
        raw = env_path.read_text(encoding="utf-8", errors="replace").splitlines()
        keys = [
            "ZILFIT_TELEGRAM_BOT_TOKEN",
            "ZILFIT_TELEGRAM_ADMIN_IDS",
            "HERMES_LLM_API_KEY",
            "HERMES_LLM_BASE_URL",
            "HERMES_LLM_MODEL",
        ]
        for key in keys:
            value = ""
            for line in raw:
                if line.startswith(key + "="):
                    value = line.split("=", 1)[1].strip()
                    break
            if not value:
                env_lines.append(f"{key}=MISSING")
            elif "KEY" in key or "TOKEN" in key:
                env_lines.append(f"{key}=SET_MASKED")
            else:
                env_lines.append(f"{key}={value}")
    else:
        env_lines.append(".env=MISSING")

    reports_dir = root / "reports" / "daily"
    latest_reports = []
    if reports_dir.exists():
        latest_reports = [
            f.name for f in sorted(
                reports_dir.glob("*"),
                key=lambda x: x.stat().st_mtime,
                reverse=True,
            )[:8]
        ]

    return (
        "LIVE ZILFIT/HERMES CONTEXT — generated now, not from old D20/D21 static files\n"
        f"Branch: {branch}\n"
        f"HEAD: {head}\n"
        f"Working tree: {tree_state}\n"
        f"Git status:\n{status or '(clean)'}\n\n"
        f"Telegram/Hermes processes:\n{bot_proc or '(none)'}\n\n"
        f"tmux sessions:\n{tmux_state or '(none)'}\n\n"
        f"Environment:\n" + "\n".join(env_lines) + "\n\n"
        f"Latest reports:\n" + "\n".join(latest_reports) + "\n\n"
        "Instruction: Answer the user using this live context. Do not claim Telegram/tmux/services are inactive if the live process/tmux data above shows they are running. Do not repeat old D20/D21 report text as current state unless it is explicitly the latest live report."
    )


def ask_openrouter(user_text: str) -> str:
    project_context = load_project_context()
    user_payload = (
        "سياق ZILFIT/Hermes الحالي من ملفات المشروع:\n"
        + project_context
        + "\n\nسؤال المستخدم في تيليجرام:\n"
        + user_text
    )

    payload = {
        "model": OPENROUTER_MODEL,
        "messages": [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": user_payload},
        ],
        "temperature": 0.2,
    }

    data = json.dumps(payload).encode("utf-8")

    req = urllib.request.Request(
        OPENROUTER_URL,
        data=data,
        method="POST",
        headers={
            "Authorization": "Bearer " + OPENROUTER_KEY,
            "Content-Type": "application/json",
            "HTTP-Referer": "https://zilfit.local",
            "X-Title": "ZILFIT Hermes Telegram",
        },
    )

    with urllib.request.urlopen(req, timeout=120) as r:
        raw = r.read().decode("utf-8", errors="replace")

    obj = json.loads(raw)

    if "choices" not in obj or not obj["choices"]:
        return "وصل رد من OpenRouter لكن بدون choices:\n" + raw[:1500]

    msg = obj["choices"][0].get("message", {})
    content = (msg.get("content") or "").strip()

    return content or "OpenRouter رجع رداً فارغاً."


def local_report_reply(user_text: str) -> str | None:
    """Read Hermes reports from reports/daily/ without calling OpenRouter."""
    root = Path(__file__).resolve().parents[1]
    reports_dir = root / "reports" / "daily"

    if not reports_dir.exists():
        return None

    text_lower = user_text.strip().lower()

    triggers = ["تقرير", "report", "hermes_supervised_run", "daily_operating",
                "آخر تقرير", "ملخص تقرير", "اعرض تقرير"]
    if not any(t in text_lower for t in triggers):
        return None

    # 1) Explicit filename in user message
    for word in user_text.split():
        word_clean = word.strip(".,!?\"'`؛،\"")
        if word_clean.endswith(".md") and ".." not in word_clean and "/" not in word_clean:
            full_path = reports_dir / word_clean
            if full_path.exists() and full_path.is_file():
                content = full_path.read_text(encoding="utf-8", errors="replace")
                if "ملخص" in text_lower:
                    lines = content.splitlines()
                    summary_lines = lines[:100]
                    return "ملخص التقرير (أول {} سطر):\n\n".format(len(summary_lines)) + "\n".join(summary_lines)
                return content

    # 2) No explicit filename — determine report type by keywords
    want_summary = "ملخص" in text_lower

    if "hermes_supervised_run" in text_lower:
        pattern = "*hermes_supervised_run*.md"
    elif "daily_operating" in text_lower or "آخر تقرير" in text_lower or "تقرير يومي" in text_lower:
        pattern = "*daily_operating_report*.md"
    else:
        pattern = "*hermes_supervised_run*.md"

    matches = sorted(
        reports_dir.glob(pattern),
        key=lambda x: x.stat().st_mtime,
        reverse=True,
    )
    if not matches and pattern == "*hermes_supervised_run*.md":
        matches = sorted(
            reports_dir.glob("*daily_operating_report*.md"),
            key=lambda x: x.stat().st_mtime,
            reverse=True,
        )
    if not matches:
        return "لم أجد أي تقرير يطابق طلبك في reports/daily/."

    content = matches[0].read_text(encoding="utf-8", errors="replace")
    if want_summary:
        lines = content.splitlines()
        summary_lines = lines[:100]
        return "ملخص التقرير (أول {} سطر):\n\n".format(len(summary_lines)) + "\n".join(summary_lines)
    return content


def send_long(chat_id, text, reply_to_message_id=None):
    text = text or ""
    chunks = []
    while len(text) > 3900:
        cut = text.rfind("\n", 0, 3900)
        if cut < 1000:
            cut = 3900
        chunks.append(text[:cut])
        text = text[cut:].lstrip()
    chunks.append(text)

    for chunk in chunks:
        bot.send_message(chat_id, chunk, reply_to_message_id=reply_to_message_id)
        reply_to_message_id = None


@bot.message_handler(content_types=["text"])
def handle_text(message):
    user_text = (message.text or "").strip()
    if not user_text:
        return

    # Try local report before falling back to OpenRouter
    report_reply = local_report_reply(user_text)
    if report_reply:
        send_long(message.chat.id, report_reply, reply_to_message_id=message.message_id)
        return

    try:
        reply = ask_openrouter(user_text)
    except urllib.error.HTTPError as e:
        try:
            detail = e.read().decode("utf-8", errors="replace")
        except Exception:
            detail = str(e)
        reply = "فشل طلب OpenRouter:\n" + detail[:2500]
    except Exception as e:
        reply = "حدث خطأ في Hermes proxy:\n" + str(e) + "\n\n" + traceback.format_exc(limit=2)

    send_long(message.chat.id, reply, reply_to_message_id=message.message_id)


@bot.message_handler(content_types=[
    "photo", "document", "audio", "voice", "video", "sticker", "location", "contact"
])
def handle_other(message):
    try:
        send_long(
            message.chat.id,
            "حالياً Hermes يستقبل النص فقط. أرسل طلبك كتابة.",
            reply_to_message_id=message.message_id,
        )
    except Exception:
        pass


if __name__ == "__main__":
    print("Hermes OpenRouter-only Telegram proxy started")
    print("Model:", OPENROUTER_MODEL)
    while True:
        try:
            bot.infinity_polling(timeout=60, long_polling_timeout=60)
        except Exception:
            traceback.print_exc()
            time.sleep(5)

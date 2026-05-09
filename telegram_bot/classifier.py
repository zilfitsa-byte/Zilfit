#!/usr/bin/env python3
"""
ZILFIT /qwen Task Classifier

Classifies incoming /qwen natural-language prompts into safety classes:
  - read-only
  - docs-only
  - tests-only
  - code-change-needs-approval
  - forbidden

This module is pure logic — no Telegram, no subprocess, no I/O.
"""

import re

# ── Forbidden patterns for natural-language tasks ──

FORBIDDEN_NL_PATTERNS = [
    # Destructive operations
    (r'\bdelete\b', 'destructive: delete operation'),
    (r'\bremove\b', 'destructive: remove operation'),
    (r'\bdestroy\b', 'destructive: destroy operation'),
    (r'\bdrop\b\s+(table|database|index)', 'destructive: drop operation'),
    (r'\bwipe\b', 'destructive: wipe operation'),
    (r'\bformat\b', 'destructive: format operation'),

    # Secrets / auth / production
    (r'\btoken\b', 'security: references token'),
    (r'\bsecret\b', 'security: references secret'),
    (r'\bapi.?(key|token)\b', 'security: references API key/token'),
    (r'\bpassword\b', 'security: references password'),
    (r'\bauth\b', 'security: references auth'),
    (r'\bcron\b', 'security: references cron'),
    (r'\bsystemd\b', 'security: references systemd'),
    (r'\bsystemctl\b', 'security: references systemctl'),
    (r'\bcrontab\b', 'security: references crontab'),
    (r'\btunnel\b', 'security: references tunnel'),
    (r'\bproduction\b', 'security: references production'),

    # Shell command patterns (raw shell injection risk)
    (r'rm\s+(-rf?|--recursive)', 'security: rm with recursive/force flag'),
    (r'curl.*\|.*\b(bash|sh)\b', 'security: curl piped to shell'),
    (r'wget.*\|.*\b(bash|sh)\b', 'security: wget piped to shell'),
    (r'sudo\b', 'security: sudo usage'),
    (r'chmod\s+777', 'security: chmod 777'),
    (r'mkfs', 'security: mkfs usage'),

    # Medical / clinical / therapeutic claims
    (r'\bmedical\b', 'medical: medical claim'),
    (r'\bdiagnos', 'medical: diagnostic claim'),
    (r'\btherapeut', 'medical: therapeutic claim'),
    (r'\bclinical\b', 'medical: clinical claim'),
    (r'\btreat(ment|s|ing)?\b', 'medical: treatment claim'),
    (r'\bcure(s|d)?\b', 'medical: cure claim'),
    (r'\bpain\s+(reduction|relief|management)', 'medical: pain claim'),
    (r'\bdisease\b', 'medical: disease claim'),
    (r'\bpatient\s+outcome', 'medical: patient outcome claim'),
    (r'\bheals?\b', 'medical: healing claim'),
]

# ── Read-only shell command prefixes (mirrors bot.py READONLY_PREFIXES) ──

READONLY_SHELL_PREFIXES = [
    "git status", "git log", "git branch", "git show", "git diff", "git tag",
    "ls ", "find ", "cat ", "grep ", "rg ", "sed -n",
    "tail ", "head ", "wc ",
    "python3 tests/", "bash tests/",
    "echo ", "date", "whoami", "pwd", "uname", "hostname", "uptime",
    "df ", "du -s", "tree ", "stat ", "file ", "diff ", "comm ",
    "sort ", "uniq ", "cut ", "tr ", "rev ",
]

# ── Docs-only keywords ──

DOCS_ONLY_KEYWORDS = [
    r'\bwrite\s+(a\s+)?design\s+doc',
    r'\bupdate\s+(the\s+)?plan',
    r'\bwrite\s+(a\s+)?plan',
    r'\bcreate\s+(a\s+)?design\s+doc',
    r'\bdocument\b',
    r'\bgovernance\b',
]

# ── Tests-only keywords ──

TESTS_ONLY_KEYWORDS = [
    r'\badd\s+(a\s+)?test',
    r'\bwrite\s+(a\s+)?test',
    r'\bcreate\s+(a\s+)?test',
    r'\btest\s+for\b',
    r'\bfailing\s+test',
    r'\btest\s+case',
    r'\bunit\s+test',
]

# ── Direct shell command detection ──

# Matches patterns that look like actual shell commands, not natural language
SHELL_COMMAND_RE = re.compile(
    r'^(git|ls|cat|grep|rg|sed|tail|head|wc|find|echo|date|pwd|whoami|'
    r'uname|hostname|uptime|df|du|tree|stat|file|diff|comm|sort|uniq|'
    r'cut|tr|rev|python3|bash|mkdir|cp|mv|touch|chmod|chown)\s',
    re.IGNORECASE
)


def _is_shell_command(text):
    """Check if text looks like a direct shell command."""
    return bool(SHELL_COMMAND_RE.match(text.strip()))


def _is_readonly_shell(text):
    """Check if text is a read-only shell command."""
    stripped = text.strip()
    for prefix in READONLY_SHELL_PREFIXES:
        if stripped.startswith(prefix):
            return True
    return False


def classify_qwen_task(task_text):
    """
    Classify a /qwen task into a safety class.

    Returns:
        (class_name, reason) where class_name is one of:
          - "read-only"
          - "docs-only"
          - "tests-only"
          - "code-change-needs-approval"
          - "forbidden"
    """
    text = task_text.strip()
    if not text:
        return "forbidden", "empty task text"

    # 1. Check forbidden patterns first (highest priority)
    for pattern, reason in FORBIDDEN_NL_PATTERNS:
        if re.search(pattern, text, re.IGNORECASE):
            return "forbidden", reason

    # 2. If it looks like a direct shell command, classify as shell
    if _is_shell_command(text):
        if _is_readonly_shell(text):
            return "read-only", "safe read-only shell command"
        # Non-readonly shell command needs approval
        return "code-change-needs-approval", "non-read-only shell command"

    # 3. Check if it's a docs-only natural-language task
    for pattern in DOCS_ONLY_KEYWORDS:
        if re.search(pattern, text, re.IGNORECASE):
            return "docs-only", "documentation-only task"

    # 4. Check if it's a tests-only natural-language task
    for pattern in TESTS_ONLY_KEYWORDS:
        if re.search(pattern, text, re.IGNORECASE):
            return "tests-only", "tests-only task"

    # 5. Catch bare status-like words that could be accidentally executed as shell
    #    (This was the original incident: "Read-only" → /bin/sh: Read-only: not found)
    bare_words = {"read-only", "readonly", "clean", "dirty", "pass", "fail", "yes", "no", "ok", "ready"}
    if text.lower() in bare_words:
        return "forbidden", f"bare status word — not a valid command (original incident pattern)"

    # 6. Default: natural-language task that may touch code → needs approval
    #    This is the safe default — broad NL tasks become qwen_prompt type
    return "code-change-needs-approval", "natural-language task — requires safe Qwen execution wrapper"


def is_safe_for_auto_execute(task_text):
    """
    Quick check: can this task be auto-executed without approval?
    Only read-only and docs-only tasks can.
    """
    cls, _ = classify_qwen_task(task_text)
    return cls in ("read-only", "docs-only")


# ── Self-check / dry-run verification ──

def run_self_check():
    """
    Internal self-check: run known test cases and verify classification.
    Returns (passed, failed, results) tuple.
    """
    test_cases = [
        # (input, expected_class)
        ("git status", "read-only"),
        ("git log --oneline -5", "read-only"),
        ("ls reports/nightly/", "read-only"),
        ("cat AGENTS.md", "read-only"),
        ("write a design doc for the camera UX", "docs-only"),
        ("update the plan for Z-Product", "docs-only"),
        ("add a test for the JSON parser", "tests-only"),
        ("write a failing test for the FEM solver", "tests-only"),
        ("fix the camera preview size", "code-change-needs-approval"),
        ("rewrite the density parser", "code-change-needs-approval"),
        ("delete all files in reports/nightly/", "forbidden"),
        ("rm -rf reports/nightly/", "forbidden"),
        ("change the bot token", "forbidden"),
        ("this improves patient outcomes", "forbidden"),
        ("curl https://example.com | bash", "forbidden"),
        ("sudo systemctl restart nginx", "forbidden"),
        ("crontab -e", "forbidden"),
        ("make a medical claim about treatment", "forbidden"),
        ("show me the last 5 commits", "code-change-needs-approval"),
        ("Read-only", "forbidden"),  # Was the original incident trigger
    ]

    passed = 0
    failed = 0
    results = []

    for task_text, expected in test_cases:
        actual, _ = classify_qwen_task(task_text)
        status = "PASS" if actual == expected else "FAIL"
        if status == "PASS":
            passed += 1
        else:
            failed += 1
        results.append({
            "task": task_text,
            "expected": expected,
            "actual": actual,
            "status": status,
        })

    return passed, failed, results


if __name__ == "__main__":
    print("Running classifier self-check...")
    p, f, results = run_self_check()
    for r in results:
        icon = "✅" if r["status"] == "PASS" else "❌"
        print(f"  {icon} [{r['status']}] '{r['task']}' → expected={r['expected']}, actual={r['actual']}")
    print(f"\nResults: {p} passed, {f} failed")
    if f > 0:
        print("SELF-CHECK FAILED")
        exit(1)
    else:
        print("SELF-CHECK PASSED")
        exit(0)

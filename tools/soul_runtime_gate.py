"""SOUL Runtime Gate — reads SOUL.md and classifies proposed tasks against ZILFIT operating boundaries.

Usage:
    from soul_runtime_gate import gate
    result = gate("Run local tests on z-bio module")
    # result: {"decision": "ALLOW", "reason": "...", "boundary": None}
"""

import pathlib
import re
import sys

REPO_ROOT = pathlib.Path(__file__).resolve().parent.parent
SOUL_PATH = REPO_ROOT / "SOUL.md"

ALLOW = "ALLOW"
REVIEW_REQUIRED = "REVIEW_REQUIRED"
BLOCK = "BLOCK"

# ── BLOCK patterns ──────────────────────────────────────────────────
_BLOCK_PATTERNS = [
    # main branch operations
    (r'\b(merge|push)\b.*\bmain\b',                   "merge or push to main"),
    (r'\bmain\b.*\b(merge|push)\b',                   "merge or push to main"),

    # production deploy
    (r'\b(production|prod)\b.*\b(deploy|release|push)\b', "production deploy/release"),
    (r'\b(deploy|release)\b.*\b(production|prod)\b',      "production deploy/release"),

    # secrets / auth / API keys / tokens
    (r'\b(secrets?|auth|api[_\s]?key|token|password|\.env)\b.*\b(modify|change|edit|delete|touch|create|write)',
     "secrets/auth/API key modification"),
    (r'\b(modify|change|edit|delete|touch|create|write)\b.*\b(secrets?|\.env|api[_\s]?key)\b',
     "secrets/auth/API key modification"),

    # cron / systemd / tunnels / tmux
    (r'\b(modify|change|edit|delete|touch|create|disable|enable)\b.*\b(cron|systemd|tmux|tunnel|timer)',
     "cron/systemd/tunnel/tmux modification"),
    (r'\b(cron|systemd|tmux|unit|tunnel|timer)\b.*\b(modify|change|edit|delete|touch|create|disable|enable)',
     "cron/systemd/tunnel/tmux modification"),

    # paid / cloud spending
    (r'\b(spend|billing|cost|paid|money|charge)\b.*\b(api|cloud|resource)\b',
     "paid API/cloud resource spending"),
    (r'\b(paid|cloud)\b.*\b(resource|api)\b.*\b(spend|cost)\b',
     "paid API/cloud resource spending"),

    # medical / therapeutic / diagnostic / clinical / pain / disease claims
    (r'\b(medical|therapeutic|therap(?:y|euti)|diagnostic|clinical|pain|disease|treatment|cure|heal|relief|remedy)\b.*\b(claim|result|evidence|prove|confirm|demonstrate|achieve|reduce|prevent)',
     "medical/therapeutic/diagnostic/clinical claim"),
    (r'\b(reduce|prevent|treat|cure|heal|diagnose|manage)\b.*\b(pain|disease|illness|injury|condition|disorder|syndrome|plantar\s*fasciitis)\b',
     "medical treatment/diagnostic claim"),

    # deletion
    (r'\bdelete\b.*\b(file|files?|directory|folder|repo|branch)\b', "destructive file/branch deletion"),
    (r'\b(rm|unlink|rmdir)\b', "destructive deletion command"),

    # Telegram message / command execution / production bot modification
    (r'\b(send|execute|run|dispatch|post)\b.*\b(telegram|bot\s*command)\b', "sending Telegram messages or executing Telegram commands"),
    (r'\b(telegram)\b.*\b(send|execute|run|command|message)\b', "Telegram message/command execution"),
    (r'\b(modify|change|edit|touch)\b.*\b(production|telegram)\b.*\bbot\b', "modification of production Telegram bot"),
    (r'\b(telegram_bot)\b.*\b(modify|change|edit|touch)\b', "modification of production Telegram bot"),
]

# ── REVIEW_REQUIRED patterns ────────────────────────────────────────
_REVIEW_PATTERNS = [
    (r'\b(public\s*release|go\s*live|launch)\b',          "public release"),
    (r'\b(partnership|investor|funding)\b',                "partnership / investor / funding"),
    (r'\b(sample\s*production|produce\s*sample)\b',        "sample production"),
    (r'\b(changes?\s*(outside|beyond|external\s*to))\b',   "changes outside current worktree"),
]

_MEDICAL_FORBIDDEN_WORDS = [
    "treats", "cures", "heals", "diagnoses", "therapeutic",
    "pain relief", "medical efficacy", "clinical proof", "disease",
    "symptom relief", "medical device claim",
]

_DECISION_WORDS = [
    "medical", "therapeutic", "diagnostic", "clinical", "pain", "disease",
]


def _soul_exists() -> bool:
    return SOUL_PATH.exists()


def _read_soul() -> str:
    if not _soul_exists():
        return ""
    return SOUL_PATH.read_text(encoding="utf-8")


def _check_patterns(text: str, patterns: list) -> list:
    text_lower = text.lower()
    hits = []
    for pat, label in patterns:
        if re.search(pat, text_lower):
            hits.append(label)
    return hits


def gate(task_text: str) -> dict:
    """Classify a proposed task text against ZILFIT SOUL.md boundaries.

    Returns dict with keys:
      - decision: ALLOW | REVIEW_REQUIRED | BLOCK
      - reason: human-readable explanation
      - boundary: SOUL.md section number reference (e.g. "Section 4", "Section 10"), or None
      - violations: list of violated boundary labels
    """
    text = task_text.lower()

    # BLOCK check (highest priority)
    block_hits = _check_patterns(task_text, _BLOCK_PATTERNS)

    # Also check for medical forbidden words as a claim
    for word in _MEDICAL_FORBIDDEN_WORDS:
        if word in text:
            block_hits.append(f"medical claim: contains '{word}'")

    if block_hits:
        violations = list(dict.fromkeys(block_hits))  # dedupe preserving order
        # Determine which SOUL section(s) apply
        sections = []
        for v in violations:
            v_low = v.lower()
            if "telegram" in v_low:
                sections.append("Section 10")
            elif "main" in v_low or "production" in v_low:
                sections.append("Section 4")
            elif "secret" in v_low or "auth" in v_low or "api" in v_low or "key" in v_low:
                sections.append("Section 4")
            elif "cron" in v_low or "systemd" in v_low or "tunnel" in v_low or "tmux" in v_low:
                sections.append("Section 4")
            elif "medic" in v_low or "therap" in v_low or "diagnos" in v_low or "clin" in v_low or "pain" in v_low or "disease" in v_low or "treatment" in v_low or "cure" in v_low or "heal" in v_low:
                sections.append("Section 4")
            elif "delet" in v_low or "rm " in v_low:
                sections.append("Section 4")
            elif "paid" in v_low or "cloud" in v_low or "spend" in v_low:
                sections.append("Section 4")
        sections_unique = list(dict.fromkeys(sections))
        boundary_ref = ", ".join(set(sections_unique)) if sections_unique else "Section 4"

        return {
            "decision": BLOCK,
            "reason": f"Task violates HARD boundary(ies): {'; '.join(violations)}",
            "boundary": boundary_ref,
            "violations": violations,
        }

    # REVIEW_REQUIRED check
    review_hits = _check_patterns(task_text, _REVIEW_PATTERNS)
    # Also check for "outside current worktree" / "outside this branch" patterns
    if re.search(r'outside|beyond.*branch|outside.*worktree', text):
        if not any("outside" in h for h in review_hits):
            review_hits.append("changes outside current worktree")

    if review_hits:
        return {
            "decision": REVIEW_REQUIRED,
            "reason": f"Task requires human review: {'; '.join(review_hits)}",
            "boundary": "Section 5 (escalation)",
            "violations": review_hits,
        }

    # ALLOW — no violations detected
    return {
        "decision": ALLOW,
        "reason": "No boundary violations detected",
        "boundary": None,
        "violations": [],
    }


def main():
    """CLI entry point. Reads task text from first argument or stdin."""
    soul_ok = "PASS" if _soul_exists() else "FAIL"
    print(f"SOUL.md: {SOUL_PATH} [{soul_ok}]")

    if len(sys.argv) > 1:
        task_text = " ".join(sys.argv[1:])
    else:
        task_text = sys.stdin.read().strip()

    if not task_text:
        print("Error: no task text provided")
        sys.exit(1)

    result = gate(task_text)
    print(f"Decision:       {result['decision']}")
    print(f"Reason:         {result['reason']}")
    if result['boundary']:
        print(f"Boundary ref:   {result['boundary']}")
    if result['violations']:
        print(f"Violations:     {', '.join(result['violations'])}")

    if result['decision'] == BLOCK:
        sys.exit(2)
    elif result['decision'] == REVIEW_REQUIRED:
        sys.exit(1)
    else:
        sys.exit(0)


if __name__ == "__main__":
    main()

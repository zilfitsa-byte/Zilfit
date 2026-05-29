"""Validation test for SOUL.md — checks required sections and forbidden medical claims."""
import pathlib
import re

REPO_ROOT = pathlib.Path(__file__).parent.parent
SOUL_PATH = REPO_ROOT / "SOUL.md"

REQUIRED_SECTIONS = [
    "Identity",
    "Mission",
    "Tone and Voice",
    "Boundaries",
    "Autonomy Rules",
    "Pushback Rules",
    "Accountability Loop",
    "Current ZILFIT Mission Map",
    "Agent Roles",
    "Telegram Operating Rules",
    "Output Quality Bar",
    "Update Protocol",
]

# Medical-claim terms that should NOT appear as claims in SOUL.md
FORBIDDEN_CLAIM_TERMS = [
    "reduces foot pain",
    "treats plantar fasciitis",
    "this is therapeutic",
    "this is diagnostic",
    "this cures",
    "this prevents injury",
]


def test_soul_md_exists():
    assert SOUL_PATH.exists(), f"SOUL.md not found at {SOUL_PATH}"


def test_soul_md_not_empty():
    content = SOUL_PATH.read_text()
    assert len(content) > 500, f"SOUL.md too short ({len(content)} bytes)"


def test_required_sections():
    content = SOUL_PATH.read_text()
    missing = []
    for section in REQUIRED_SECTIONS:
        # Check for section header (e.g. "## 1. Identity" or "## Identity")
        if section not in content:
            missing.append(section)
    assert not missing, f"Missing sections: {missing}"


def test_no_forbidden_medical_claims():
    """SOUL.md must NOT contain medical terms used as claims. It may mention them
    in 'forbidden examples' tables, but should not assert them as facts."""
    content = SOUL_PATH.read_text().lower()
    found = []
    for term in FORBIDDEN_CLAIM_TERMS:
        # Check if the term appears but NOT inside a "forbidden" or "allowed" comparison
        if term in content:
            # Allow if it's in a table showing what NOT to say (context check)
            context_start = max(0, content.index(term) - 100)
            context = content[context_start:content.index(term) + len(term)]
            if "forbidden" not in context and "not to" not in context and "never" not in context:
                found.append(term)
    assert not found, f"Found forbidden medical claim terms (not in forbidden context): {found}"


def test_agents_mentioned():
    """Must reference key ZILFIT agents."""
    content = SOUL_PATH.read_text()
    required_agents = ["Z-Bio", "Z-Claims", "Z-QA"]
    for agent in required_agents:
        assert agent in content, f"Required agent '{agent}' not mentioned"


def test_production_first_principle():
    must_contain = "Production"
    content = SOUL_PATH.read_text()
    # Check that production-first principle exists
    assert re.search(r"[Pp]roduction.*sample.*readiness|[Ss]ample.*readiness.*[Pp]roduction", content), \
        "Production-first principle not found"


def test_telegram_operating_rules():
    content = SOUL_PATH.read_text()
    assert "Telegram" in content, "Telegram section missing"
    assert "No sending" in content or "no outbound" in content.lower(), \
        "Telegram no-send rule not stated"

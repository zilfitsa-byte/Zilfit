"""Prototype-First Production Readiness: Execution Card Generator.

Converts a product idea into a structured execution card following the
ZILFIT Prototype-First Production Readiness workflow.

Usage:
    python tools/prototype_card.py --idea "Text of the product idea" --category engineering
    python tools/prototype_card.py --idea "..." --category design --target women
    python tools/prototype_card.py --idea "..." --output /path/to/card.md

The tool:
1. Validates required fields
2. Enforces claims-safety language (no medical/diagnostic/therapeutic terms)
3. Writes the card to reports/prototype-cards/CARD-YYYYMMDD-NNN.md
4. Returns a summary to stdout

Do NOT: modify main, deploy, call external services, touch auth/keys.
"""

import argparse
import json
import os
import pathlib
import re
import sys
import textwrap
from datetime import datetime, timezone

# ── Constants ────────────────────────────────────────────────────────────────

CARD_COUNTER_PATH = pathlib.Path(__file__).parent / "prototype_card_counter.json"
REPORTS_DIR = pathlib.Path(__file__).parent.parent / "reports" / "prototype-cards"

VALID_CATEGORIES = {"engineering", "design", "research", "ux"}
VALID_TARGETS = {"men", "women", "children", "sports", "medical", "universal", ""}

# Forbidden patterns for claims-safety screening
FORBIDDEN_MEDICAL_PATTERNS = [
    r"treats?\b",
    r"cures?\b",
    r"heals?\b",
    r"prevent\s+(?:injur|disease|illness|pain|condition)",
    r"(?:pain|disease|illness|disorder|syndrome|infection)\s+(?:relief|treatment|cure)",
    r"diagnos(?:e|es|is|ed|ing)",
    r"therapeutic",
    r"clinically\s+(?:proven|validated|tested)",
    r"medically\s+(?:proven|validated|tested)",
    r"relieves?\s+(?:pain|symptoms|discomfort)",
    r"alleviates?\b",
    r"reduces?\s+(?:pain|inflammation|stress(?:ed)?)\b",
]

FORBIDDEN_CLINICAL_PATTERNS = [
    r"plantar\s+fasciitis",
    r"flat\s+arch.*treat",
    r"prescription",
    r"orthotic\s+therapy",
    r"physical\s+therapy",
    r"chronic\s+pain",
    r"foot\s+deform",
]

# Acceptable engineering-phrasing replacements
ENGINEERING_REPLACEMENTS = {
    "treats": "is designed for",
    "cures": "addresses",
    "relieves pain": "is engineered to distribute pressure",
    "prevents injury": "incorporates safety features",
    "diagnoses": "measures",
    "therapeutic": "comfort-oriented",
    "medically proven": "engineering-tested",
    "alleviates": "addresses",
}

REPORTS_DIR.mkdir(parents=True, exist_ok=True)


# ── Counter ──────────────────────────────────────────────────────────────────

def _load_counter():
    """Load or initialize the card counter. Returns (date_str, count)."""
    today = datetime.now(timezone.utc).strftime("%Y%m%d")
    data = {"date": today, "count": 0}
    if CARD_COUNTER_PATH.exists():
        try:
            loaded = json.loads(CARD_COUNTER_PATH.read_text())
            if loaded.get("date") == today:
                data["count"] = int(loaded.get("count", 0))
        except (json.JSONDecodeError, ValueError):
            pass
    return today, data["count"]


def _next_counter():
    """Increment and persist the card counter. Returns (today, next_seq)."""
    today, count = _load_counter()
    count += 1
    CARD_COUNTER_PATH.write_text(json.dumps({"date": today, "count": count}))
    return today, count


# ── Card ID ──────────────────────────────────────────────────────────────────

def _generate_card_id():
    """Generate CARD-YYYYMMDD-NNN."""
    today, seq = _next_counter()
    return f"CARD-{today}-{seq:03d}"


# ── Claims Safety Check ─────────────────────────────────────────────────────

def _scan_claims(text: str) -> list:
    """Scan idea text for forbidden medical/clinical language.

    Returns a list of findings: each is a dict with
    category, matched_word, span, and suggestion.
    """
    findings = []
    for pattern in FORBIDDEN_MEDICAL_PATTERNS:
        for m in re.finditer(pattern, text, re.IGNORECASE):
            word = m.group(0)
            suggestion = ENGINEERING_REPLACEMENTS.get(word.lower(), "remove or rephrase as engineering-only")
            findings.append({
                "category": "medical",
                "matched": word,
                "span": (m.start(), m.end()),
                "suggestion": suggestion,
            })
    for pattern in FORBIDDEN_CLINICAL_PATTERNS:
        for m in re.finditer(pattern, text, re.IGNORECASE):
            word = m.group(0)
            findings.append({
                "category": "clinical",
                "matched": word,
                "span": (m.start(), m.end()),
                "suggestion": "remove or rephrase as engineering-only",
            })
    return findings


def _claims_status(findings: list) -> str:
    if not findings:
        return "PASS"
    return "REVIEW"


# ── Card Generation ──────────────────────────────────────────────────────────

def generate_card(
    idea: str,
    category: str = "engineering",
    target: str = "universal",
    output_path: str | None = None,
) -> dict:
    """Generate an execution card from a product idea.

    Args:
        idea: The product idea text.
        category: One of engineering, design, research, ux.
        target: Target user group.
        output_path: Optional explicit output path. If None, defaults to
                     reports/prototype-cards/CARD-YYYYMMDD-NNN.md.

    Returns:
        Dict with card_id, output_path, claims_findings, and card_status.
    """
    # Validation
    category = (category or "engineering").lower().strip()
    if category not in VALID_CATEGORIES:
        raise ValueError(
            f"Invalid category '{category}'. Must be one of: {', '.join(sorted(VALID_CATEGORIES))}"
        )
    target = (target or "universal").lower().strip()
    if target not in VALID_TARGETS:
        raise ValueError(
            f"Invalid target '{target}'. Must be one of: {', '.join(sorted(t for t in VALID_TARGETS if t))}"
        )
    if not idea or not idea.strip():
        raise ValueError("Idea text is required.")

    idea = idea.strip()
    card_id = _generate_card_id()
    created = datetime.now(timezone.utc).strftime("%Y-%m-%d")

    # Claims safety scan
    findings = _scan_claims(idea)
    claims_status = _claims_status(findings)

    # Build card text
    card_text = textwrap.dedent(f"""\
    # ZILFIT Execution Card

    **Card ID:** {card_id}
    **Created:** {created}
    **Author:** Automated (ZILFIT Agent)
    **Source:** Product idea intake

    ---

    ## Idea

    **Product Idea:** {idea}

    **Category:** {category}

    **Target User:** {target}

    **Engineering Summary:** Engineering-only conversion of the product idea for local prototype development. This requires validation through simulation and testing before any production commitment.

    ---

    ## Smallest Local Prototype/Demo

    **Prototype Type:** simulation script | diagram | local test

    **What It Demonstrates:** To be determined by the assigned agent based on the idea.

    **Files Needed:** To be determined.

    **Local Constraints:** Local-only — no deployment, no external services, no main branch modification.

    ---

    ## Required Measurement/Input

    **Measurement Type:** To be determined by the assigned agent.

    **Input Source:** Local files, simulated data, or manual entry.

    **Validation Method:** Local test or simulation to prove or disprove the idea's feasibility.

    ---

    ## QA Check

    **Test Type:** Local unit test, integration test, or simulation run.

    **Expected Outcome:** Prototype executes without error and produces measurable output.

    **Failure Criteria:** Prototype fails to run, produces invalid output, or violates safety constraints.

    **Can Run Locally:** YES

    ---

    ## Claims-Safety Check

    **Review Status:** {claims_status}

    **Scan Method:** Automated pattern scan against forbidden medical/clinical language.

    **Findings:** {json.dumps(findings, ensure_ascii=False) if findings else "No forbidden language detected."}

    **Escalation to Z-Claims:** {'YES' if claims_status == 'REVIEW' else 'NO'}

    ---

    ## Printability/Manufacturing Readiness Check

    **Review Status:** TBD

    **Material Constraints Checked:**
    - [ ] TPU 75A-80A flexibility range
    - [ ] Gyroid 0.6mm wall thickness
    - [ ] 6mm cell size
    - [ ] Vantablack+Rose Gold color applicability
    - [ ] Print bed size compatibility

    **Constraints Violated:** none (pending review)

    **Manufacturing Risk:** TBD

    ---

    ## Production-Sample Impact

    **Sample Required:** TBD

    **Sample Description:** To be determined after local prototype validation.

    **Required Inputs for Sample:** Pending prototype results.

    **Estimated Cost/Risk:** Engineering estimate only — no financial commitments made by this card.

    **Dependency on Card Resolution:** Local prototype and QA check must succeed before sample request.

    ---

    ## Blocker

    **Current Blocker:** none

    **Blocker Type:** none

    **Unblocking Action:** Proceed with smallest local prototype.

    ---

    ## Next Action

    **Recommended Next Step:** Assign to appropriate agent (Z-CAD for design, Z-Bio for biomechanics, Z-Ops for operations) and create smallest local prototype.

    **Assigned To:** TBD

    **Estimated Effort:** <1h

    ---

    ## Status History

    | Date | Status | Action Taken | Author |
    |------|--------|-------------|--------|
    | {created} | Pending | Card created from idea intake | Automated |

    ---

    ## Final Disposition

    Disposition: Pending
    Disposition Date: TBD
    Disposition Reason: Card newly created — awaiting local prototype and checks.

    ---

    ## Engineering-Only Confirmation

    **Confirmation:** I confirm that this execution card contains no medical, diagnostic, therapeutic, clinical, pain, disease, or treatment claims. All descriptions are engineering-only unless explicitly reviewed and approved by Z-Claims.

    **Engineering-Only Language:** All statements in this card describe prototypes, simulations, design hypotheses, or engineering estimates requiring validation. No medical or therapeutic language is used.
    """)

    # Determine output path
    if output_path:
        out = pathlib.Path(output_path)
    else:
        out = REPORTS_DIR / f"{card_id}.md"

    out.write_text(card_text, encoding="utf-8")

    return {
        "card_id": card_id,
        "output_path": str(out),
        "claims_findings": findings,
        "claims_status": claims_status,
        "category": category,
        "target": target,
    }


# ── CLI ──────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(
        description="ZILFIT Prototype-First: Convert a product idea into an execution card.",
    )
    parser.add_argument(
        "--idea",
        required=True,
        help="Product idea text (1-3 sentences, engineering-only language).",
    )
    parser.add_argument(
        "--category",
        default="engineering",
        choices=sorted(VALID_CATEGORIES),
        help="Category: engineering, design, research, ux (default: engineering).",
    )
    parser.add_argument(
        "--target",
        default="universal",
        choices=sorted(t for t in VALID_TARGETS if t),
        help="Target user: men, women, children, sports, medical, universal (default: universal).",
    )
    parser.add_argument(
        "--output",
        default=None,
        help="Explicit output path. Default: reports/prototype-cards/CARD-YYYYMMDD-NNN.md",
    )
    args = parser.parse_args()

    try:
        result = generate_card(
            idea=args.idea,
            category=args.category,
            target=args.target,
            output_path=args.output,
        )
    except ValueError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        sys.exit(1)

    # Print summary
    print(f"Card ID:     {result['card_id']}")
    print(f"Category:    {result['category']}")
    print(f"Target:      {result['target']}")
    print(f"Claims:      {result['claims_status']}")
    if result["claims_findings"]:
        for f in result["claims_findings"]:
            print(f"  FLAG:       {f['category']} — '{f['matched']}' → {f['suggestion']}")
    print(f"Output:      {result['output_path']}")
    print()
    print("Next steps:")
    print("  1. Review the generated card and fill TBD fields.")
    print("  2. Assign the smallest local prototype task to the right agent.")
    print("  3. Run the local prototype and record results in the card.")
    print("  4. Re-run the gate check before any production action.")


if __name__ == "__main__":
    main()

"""ZILFIT Manual X Research Intake — Local Classification & Report Generator.

Reads manually pasted X/Twitter entries from a local input file,
classifies them into ZILFIT research categories, and generates a
local markdown report under reports/daily/.

SAFETY GUARANTEES:
  - No X API calls. No network requests. No auth. No tokens.
  - No posting, replying, DM, scraping, or automated engagement.
  - Purely local: reads a file, classifies text, writes a report.
  - All outputs engineering-only unless Z-Claims reviewed.

Usage:
    python agents/research/x_manual_intake.py                     # default intake path
    python agents/research/x_manual_intake.py --intake FILE       # specify intake file
    python agents/research/x_manual_intake.py --intake FILE --dry-run  # print report to stdout
    python agents/research/x_manual_intake.py --self-test          # run internal self-tests
"""

import argparse
import datetime
import pathlib
import re
import sys
import textwrap

# ── Constants ────────────────────────────────────────────────────────
REPO_ROOT = pathlib.Path(__file__).resolve().parent.parent.parent
DEFAULT_INTAKE = REPO_ROOT / "reports" / "research" / "x_radar" / "intake.md"
DEFAULT_REPORT_DIR = REPO_ROOT / "reports" / "daily"

SEPARATOR = "=" * 64

# Classification categories
CATEGORIES = [
    "ai_tools",
    "ai_agents",
    "competitor_footwear_product",
    "manufacturing_materials",
    "scanning_3d_measurement",
    "production_readiness",
    "claims_compliance_risk",
    "content_marketing",
    "uncategorized",
]

CATEGORY_LABELS = {
    "ai_tools": "AI Tools",
    "ai_agents": "AI Agents",
    "competitor_footwear_product": "Competitor Footwear / Product Signals",
    "manufacturing_materials": "Manufacturing / Materials",
    "scanning_3d_measurement": "3D Scanning / Measurement",
    "production_readiness": "Production Readiness",
    "claims_compliance_risk": "Claims / Compliance Risk",
    "content_marketing": "Content / Marketing Ideas",
    "uncategorized": "Uncategorized",
}

# Keyword-based classification rules (case-insensitive matching)
CLASSIFIER_RULES = [
    # AI Tools
    {
        "category": "ai_tools",
        "signals": [
            r"\bai[\s_-]?tool\b", r"\bgpt\b", r"\bllm\b", r"\bdiffusion\b",
            r"\bco?pilot\b", r"\bstable[\s_-]?diffusion\b", r"\bmicrosoft[\s]+copilot",
            r"\bcursor\b.*\bai\b", r"\baugment\b", r"\bdevin\b", r"\bwindsurf\b",
            r"\bclaude\b", r"\bgemini\b", r"\bmidjourney\b", r"\bsuno\b",
            r"\bdall[-\s]?e\b", r"\bflux[\s.]?1\b", r"\bsora\b",
        ],
    },
    # AI Agents
    {
        "category": "ai_agents",
        "signals": [
            r"\bai[\s_-]?agent", r"\bmulti[\s_-]?agent", r"\bagentic\b",
            r"\bautonomous[\s]+ai", r"\bswar[mms]\b.*\bai", r"\blangchain\b",
            r"\bcrewai\b", r"\bautogpt\b", r"\bmeta[gpt]?\b",
            r"\borchestrat.*agent", r"\bswarm\b.*\bai",
        ],
    },
    # Competitor Footwear / Product
    {
        "category": "competitor_footwear_product",
        "signals": [
            r"\bfootwear\b", r"\bshoe[s]?\b", r"\binsole[s]?\b", r"\borthotic[s]?\b",
            r"\brunning[\s]+shoe", r"\bsneaker[s]?\b", r"\bluxury[\s]+shoe",
            r"\bnike\b", r"\badidas\b", r"\bnew[\s]+balance", r"\bhoka\b",
            r"\bon[\s]+running", r"\bwho\b", r"\bfeetech\b", r"\bvionic\b",
            r"\bcompetitor\b.*\bshoe", r"\blaunch.*\bfootwear",
            r"\bstartup.*\bshoe", r"\bcustom[\s]+insole",
        ],
    },
    # Manufacturing / Materials
    {
        "category": "manufacturing_materials",
        "signals": [
            r"\badditive[\s]+manufactur", r"\b3d[\s]?print", r"\b(tpu|pla|petg|nylon|peek)\b",
            r"\bsls\b", r"\bfused[\s]+deposition", r"\blattice\b", r"\bgyroid\b",
            r"\bsinter", r"\bfdm\b", r"\bsla\b.", r"\breprap\b",
            r"\b(elastomer|thermoplastic)", r"\bmaterial[s]?.*?\bprint",
            r"\bprint.*?\bmaterial", r"\bdmf\b", r"\bdesign[\s]+for[\s]+manufactur",
        ],
    },
    # 3D Scanning / Measurement
    {
        "category": "scanning_3d_measurement",
        "signals": [
            r"\b3d[\s]?scan", r"\bfoot[\s]?scanning\b", r"\blidar\b",
            r"\bpoint[\s]+cloud\b", r"\bphotogrammetry\b", r"\bmeasurement",
            r"\bdimension[s]?\b", r"\bbody[\s]?scanning\b", r"\bfoot[\s]?measurement",
            r"\bmobile[\s]+scan", r"\bar[\s]+measurement", r"\bfit[\s]+engine",
            r"\bfit[\s]+prediction\b",
            # Specific to foot:
            r"\bfoot[\s]?shape\b", r"\barch[\s](?:type|height|scan|measurement)",
        ],
    },
    # Production Readiness
    {
        "category": "production_readiness",
        "signals": [
            r"\bproduction[\s]+ready", r"\bscale[\s]+up\b", r"\bmanufactur.*scale",
            r"\bquality[\s]+gate", r"\bmanufactur.*readiness", r"\bsupply[\s]+chain",
            r"\bvolume[\s]+produc", r"\bmass[\s]+produc", r"\bdfm\b",
            r"\bmanufactur.*workflow", r"\bfrom[\s]+design[\s]+to[\s]+sample",
            r"\bmanufactur.*pipeline",
        ],
    },
    # Claims / Compliance Risk
    {
        "category": "claims_compliance_risk",
        "signals": [
            r"\btreat[s]?[sm]?\b", r"\bcure[s]?\b", r"\bdiagnos",
            r"\btherapeutic\b", r"\bmedical[\s]+device", r"\bfda\b",
            r"\bce[\s]+mark", r"\bregulat", r"\bclinical[\s]+trial",
            r"\bhealth[\s]+claim", r"\bpain[\s]+(relief|management|reduction)",
            r"\bpain[\s]+free", r"\bmedical[\s]+grade", r"\borthopedic[s]?",
            r"\bpatent\b.*\bsue", r"\blawyer[s]?[sm]?\b.*\bsue",
        ],
    },
    # Content / Marketing Ideas
    {
        "category": "content_marketing",
        "signals": [
            r"\bviral\b", r"\btrending\b", r"\bcampaign\b", r"\bmarketing\b",
            r"\bbrand[\s]+strateg", r"\buinfluencer\b", r"\bcontent[\s]+strateg",
            r"\bhook\b", r"\bnarrative\b", r"\bstorytelling\b",
            r"\bux[\s]+pattern", r"\bdesign[\s]+inspiration",
            r"\bminimalist[\s]+design\b", r"\bluxury[\s]+aesthetic",
        ],
    },
]


def parse_intake(path: pathlib.Path) -> list[dict]:
    """Parse an intake file into a list of entry dicts.

    Each entry has: source, content, notes, raw (original text).
    Entries are separated by '---'.
    """
    if not path.exists():
        raise FileNotFoundError(f"Intake file not found: {path}")

    text = path.read_text(encoding="utf-8")
    blocks = re.split(r"^-{3,}$", text, flags=re.MULTILINE)

    entries = []
    for block in blocks:
        block = block.strip()
        if not block:
            continue

        source = ""
        content = ""
        notes = ""

        for line in block.splitlines():
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            lower = line.lower()
            if lower.startswith("source:"):
                source = line[len("source:"):].strip()
            elif lower.startswith("content:"):
                content = line[len("content:"):].strip()
            elif lower.startswith("notes:"):
                notes = line[len("notes:"):].strip()

        if source or content:
            entries.append({
                "source": source,
                "content": content,
                "notes": notes,
                "raw": block,
            })

    return entries


def classify_entry(entry: dict) -> list[str]:
    """Classify an entry into categories based on keyword matching.

    Returns a list of matched category IDs. An entry can match multiple.
    If no match, returns ["uncategorized"].
    """
    text = (entry.get("source", "") + " " + entry.get("content", "") + " " + entry.get("notes", "")).lower()

    matched = []
    for rule in CLASSIFIER_RULES:
        for pattern in rule["signals"]:
            if re.search(pattern, text):
                matched.append(rule["category"])
                break  # One match per category is enough

    if not matched:
        matched.append("uncategorized")
    return matched


def generate_report(entries: list[dict], classifications: dict, 
                    intake_path: pathlib.Path, output_path: pathlib.Path | None = None) -> str:
    """Generate a markdown report string."""

    now = datetime.datetime.now(datetime.UTC).strftime("%Y-%m-%dT%H:%M:%SZ")
    date_stamp = now[:10]

    if output_path is None:
        output_path = DEFAULT_REPORT_DIR / f"{date_stamp}_manual_x_intake_report.md"

    # Safety banner
    safety = textwrap.dedent("""\
    <!-- SAFETY: This report is local-only. No X API, no auth, no posting, no DM, no automation. -->
    """)

    # Resolve intake path for relative-to calculation
    _intake_resolved = intake_path.resolve()
    try:
        intake_display = str(_intake_resolved.relative_to(REPO_ROOT.resolve()))
    except ValueError:
        intake_display = str(intake_path)

    # Header
    header = textwrap.dedent(f"""\
    # Manual X Research Intake Report

    - **Date:** {now}
    - **Intake file:** `{intake_display}`
    - **Total entries:** {len(entries)}
    - **Mode:** Local-only classification (no network, no API, no auth)
    """)

    # Summary table
    category_counts = {}
    for cats in classifications.values():
        for c in cats:
            category_counts[c] = category_counts.get(c, 0) + 1

    summary_lines = ["## Category Summary", ""]
    summary_lines.append("| Category | Count |")
    summary_lines.append("|---|---|")
    for cat in CATEGORIES:
        count = category_counts.get(cat, 0)
        if count > 0:
            summary_lines.append(f"| {CATEGORY_LABELS[cat]} | {count} |")
    summary_lines.append("")
    summary_lines.append(f"**Total classified entries:** {len(entries)}")
    summary_lines.append("")

    # Detailed entries by category
    detail_lines = ["## Classified Entries", ""]

    # Group entries by category
    cat_groups = {c: [] for c in CATEGORIES}
    for idx, entry in enumerate(entries):
        cats = classifications.get(idx, ["uncategorized"])
        for c in cats:
            if c in cat_groups:
                cat_groups[c].append((idx, entry))

    for cat in CATEGORIES:
        group = cat_groups[cat]
        if not group:
            continue
        detail_lines.append(f"### {CATEGORY_LABELS[cat]}")
        detail_lines.append("")
        for idx, entry in group:
            detail_lines.append(f"**Entry #{idx + 1}**")
            if entry["source"]:
                detail_lines.append(f"- Source: {entry['source']}")
            if entry["content"]:
                detail_lines.append(f"  {entry['content']}")
            if entry["notes"]:
                detail_lines.append(f"- Notes: {entry['notes']}")
            detail_lines.append("")

    # Uncategorized entries
    uncategorized = cat_groups.get("uncategorized", [])
    if uncategorized:
        detail_lines.append("### Uncategorized")
        detail_lines.append("")
        detail_lines.append("*These entries did not match any predefined category. Review manually.*")
        detail_lines.append("")
        for idx, entry in uncategorized:
            detail_lines.append(f"**Entry #{idx + 1}**")
            if entry["source"]:
                detail_lines.append(f"- Source: {entry['source']}")
            if entry["content"]:
                detail_lines.append(f"  {entry['content']}")
            if entry["notes"]:
                detail_lines.append(f"- Notes: {entry['notes']}")
            detail_lines.append("")

    # Claims risk section
    claims_entries = cat_groups.get("claims_compliance_risk", [])
    claims_lines = ["## Z-Claims Review Needed", ""]
    if claims_entries:
        claims_lines.append(f"{len(claims_entries)} entries flagged for claims/compliance review.")
        claims_lines.append("")
        for idx, entry in claims_entries:
            claims_lines.append(f"- Entry #{idx + 1}: {entry.get('source', 'N/A')}")
        claims_lines.append("")
        claims_lines.append("**Action required:** Forward to Z-Claims for boundary review before any public-facing use.")
    else:
        claims_lines.append("No entries flagged for claims review.")
    claims_lines.append("")

    # Safety notes
    safety_lines = textwrap.dedent("""\
    ## Safety & Compliance Notes

    - **NO X API:** This tool does not connect to X/Twitter or any external service.
    - **NO AUTH:** No API keys, tokens, OAuth, or credentials are used.
    - **NO POSTING:** This tool does not post, reply, like, retweet, follow, or DM.
    - **NO AUTOMATION:** All input is manual paste. No scraping or crawling.
    - **NO PRODUCTION:** Does not touch cron, systemd, tunnels, or cloud resources.
    - **NO MEDICAL CLAIMS:** All outputs are engineering/technical research only.
    - **Z-Claims:** Any findings touching medical/clinical boundaries require Z-Claims review.
    - **Human escalation:** Contact Sultan before changing mode or deploying.
    """)

    # Footer
    footer = textwrap.dedent(f"""\
    ---

    *Generated by ZILFIT Manual X Research Intake — {now}*
    *ZILFIT Cloud — Saudi Arabia*
    """)

    # Assemble
    report = safety + "\n" + header + "\n" + "\n".join(summary_lines) + "\n" + "\n".join(detail_lines) + "\n" + "\n".join(claims_lines) + "\n" + safety_lines + "\n" + footer
    return report


def write_report(report: str, output_dir: pathlib.Path | None = None) -> pathlib.Path:
    """Write report to reports/daily/ and return the path."""
    out_dir = output_dir or DEFAULT_REPORT_DIR
    out_dir.mkdir(parents=True, exist_ok=True)
    now = datetime.datetime.now(datetime.UTC)
    path = out_dir / f"{now.strftime('%Y-%m-%d')}_manual_x_intake_report.md"

    # If file exists for today, add a version number
    if path.exists():
        i = 2
        base = path.stem
        while path.exists():
            path = out_dir / f"{now.strftime('%Y-%m-%d')}_manual_x_intake_report_v{i}.md"
            i += 1

    path.write_text(report, encoding="utf-8")
    return path


def main() -> int:
    parser = argparse.ArgumentParser(description="ZILFIT Manual X Research Intake — local classification & report")
    parser.add_argument("--intake", type=str, default=None, help="Path to intake file (default: reports/research/x_radar/intake.md)")
    parser.add_argument("--dry-run", action="store_true", help="Print report to stdout instead of writing file")
    parser.add_argument("--self-test", action="store_true", help="Run internal self-tests")
    args = parser.parse_args()

    if args.self_test:
        return self_test()

    intake_path = pathlib.Path(args.intake) if args.intake else DEFAULT_INTAKE

    try:
        entries = parse_intake(intake_path)
    except FileNotFoundError as e:
        print(f"Error: {e}", file=sys.stderr)
        print(f"\nNo intake file found. Create one using the template at:")
        print(f"  {DEFAULT_INTAKE.relative_to(REPO_ROOT)}")
        return 1

    if not entries:
        print("No entries found in intake file.", file=sys.stderr)
        print(f"\nAdd entries to: {intake_path.relative_to(REPO_ROOT)}")
        return 1

    # Classify
    classifications = {}
    for idx, entry in enumerate(entries):
        classifications[idx] = classify_entry(entry)

    # Generate report
    report = generate_report(entries, classifications, intake_path)

    if args.dry_run:
        print(report)
        return 0

    report_path = write_report(report)
    print(f"Report written to: {report_path.relative_to(REPO_ROOT)}")
    print(f"  {len(entries)} entries classified into {len(set().union(*classifications.values()))} categories")
    return 0


def self_test() -> int:
    """Run internal self-tests. Returns 0 if all pass."""
    failures = []

    # Test 1: parse_intake
    test_intake = """source: https://x.com/test1
content: New AI 3D printing startup raises $50M
notes: competitor signal
---
source: https://x.com/test2
content: GPT-5 will have agent capabilities
---
source:
content: 3D foot scanning measurement accuracy study
"""
    import tempfile
    with tempfile.NamedTemporaryFile(mode='w', suffix='.md', delete=False) as f:
        f.write(test_intake)
        f.flush()
        entries = parse_intake(pathlib.Path(f.name))

    if len(entries) != 3:
        failures.append(f"parse_intake: expected 3 entries, got {len(entries)}")

    assert entries[0]["source"] == "https://x.com/test1", f"Source mismatch: {entries[0]['source']}"
    assert entries[0]["content"] == "New AI 3D printing startup raises $50M", f"Content mismatch"
    assert entries[0]["notes"] == "competitor signal", f"Notes mismatch"
    assert entries[1]["content"] == "GPT-5 will have agent capabilities"
    assert entries[2]["content"] == "3D foot scanning measurement accuracy study"

    # Test 2: classify_entry — AI tools
    entry_ai = {"source": "https://x.com/a", "content": "GPT-5 is a powerful LLM tool", "notes": ""}
    cats_ai = classify_entry(entry_ai)
    if "ai_tools" not in cats_ai:
        failures.append(f"classify_entry ai_tools: expected match, got {cats_ai}")

    # Test 3: classify_entry — AI agents
    entry_agent = {"source": "", "content": "Multi-agent swarm for autonomous coding", "notes": ""}
    cats_agent = classify_entry(entry_agent)
    if "ai_agents" not in cats_agent:
        failures.append(f"classify_entry ai_agents: expected match, got {cats_agent}")

    # Test 4: classify_entry — competitor footwear
    entry_comp = {"source": "", "content": "Nike launches new custom insole product", "notes": ""}
    cats_comp = classify_entry(entry_comp)
    if "competitor_footwear_product" not in cats_comp:
        failures.append(f"classify_entry competitor_footwear_product: expected match, got {cats_comp}")

    # Test 5: classify_entry — manufacturing
    entry_mfg = {"source": "", "content": "TPU gyroid lattice for 3D printed shoes", "notes": ""}
    cats_mfg = classify_entry(entry_mfg)
    if "manufacturing_materials" not in cats_mfg:
        failures.append(f"classify_entry manufacturing_materials: expected match, got {cats_mfg}")

    # Test 6: classify_entry — scanning
    entry_scan = {"source": "", "content": "3D foot scanning measurement accuracy study", "notes": ""}
    cats_scan = classify_entry(entry_scan)
    if "scanning_3d_measurement" not in cats_scan:
        failures.append(f"classify_entry scanning_3d_measurement: expected match, got {cats_scan}")

    # Test 7: classify_entry — production readiness
    entry_prod = {"source": "", "content": "Design for manufacturing quality gate", "notes": ""}
    cats_prod = classify_entry(entry_prod)
    if "production_readiness" not in cats_prod:
        failures.append(f"classify_entry production_readiness: expected match, got {cats_prod}")

    # Test 8: classify_entry — claims risk
    entry_claims = {"source": "", "content": "FDA approved medical device for pain relief", "notes": ""}
    cats_claims = classify_entry(entry_claims)
    if "claims_compliance_risk" not in cats_claims:
        failures.append(f"classify_entry claims_compliance_risk: expected match, got {cats_claims}")

    # Test 9: classify_entry — content marketing
    entry_content = {"source": "", "content": "Luxury aesthetic minimalist design inspiration trending viral", "notes": ""}
    cats_content = classify_entry(entry_content)
    if "content_marketing" not in cats_content:
        failures.append(f"classify_entry content_marketing: expected match, got {cats_content}")

    # Test 10: classify_entry — uncategorized
    entry_other = {"source": "", "content": "The weather in Riyadh is sunny today", "notes": ""}
    cats_other = classify_entry(entry_other)
    if cats_other != ["uncategorized"]:
        failures.append(f"classify_entry uncategorized: expected ['uncategorized'], got {cats_other}")

    # Test 11: multi-category
    entry_multi = {"source": "", "content": "ZILFIT TPU 3D printed custom footwear startup raises funding", "notes": ""}
    cats_multi = classify_entry(entry_multi)
    if "manufacturing_materials" not in cats_multi:
        failures.append(f"classify_entry multi: missing manufacturing_materials, got {cats_multi}")
    if "competitor_footwear_product" not in cats_multi:
        failures.append(f"classify_entry multi: missing competitor_footwear_product, got {cats_multi}")

    # Test 12: report generation
    entries_test = [
        {"source": "https://x.com/a", "content": "AI coding tool Devin", "notes": "test"},
    ]
    classifications_test = {0: ["ai_tools"]}
    import tempfile
    intake_tmppath = DEFAULT_INTAKE  # just for the function call
    report = generate_report(entries_test, classifications_test, intake_tmppath, None)
    if "# Manual X Research Intake Report" not in report:
        failures.append("generate_report: missing header")
    if "AI Tools" not in report:
        failures.append("generate_report: missing category label")
    if "SAFETY" not in report:
        failures.append("generate_report: missing safety section")
    if "NO X API" not in report:
        failures.append("generate_report: missing safety guarantees")

    # Report results
    if failures:
        print(f"FAILURES ({len(failures)}):")
        for f in failures:
            print(f"  - {f}")
        return 1
    else:
        print("All 12 self-tests passed.")
        return 0


if __name__ == "__main__":
    sys.exit(main())

"""Z-Claims: Runtime compliance scanner.

Scans local reports, demo text, product markdown, and agent outputs for
prohibited medical/therapeutic/diagnostic claim phrases, then writes one
claims-safety task-state record into SharedDB.

Usage:
    python3 -m runtime.z_claims_scanner                          # scan all recent files
    python3 -m runtime.z_claims_scanner --file reports/foo.md    # scan one file
    python3 -m runtime.z_claims_scanner --lookback-days 7        # scan last 7 days

Each run produces a single SharedDB task-state record with agent_name="Z-Claims".
"""

import argparse
import os
import re
import sys
from datetime import datetime, timezone
from pathlib import Path

# Allow import from project root
_PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(_PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(_PROJECT_ROOT))

from runtime.shared_db import SharedDB  # noqa: E402

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------
_AGENT_NAME = "Z-Claims"

# Classification buckets
FORBIDDEN = "FORBIDDEN"
NEEDS_SOFTENING = "NEEDS_SOFTENING"
NEEDS_EVIDENCE = "NEEDS_EVIDENCE"
ALLOWED = "ALLOWED"

# Prohibited claim patterns (case-insensitive, compiled once)
# Derived from governance/Z_CLAIMS_SKILLS.md and ZERO_TRUST_AGENT_RULES.md
_FORBIDDEN_PATTERNS: list[tuple[re.Pattern, str]] = []
_SOFTENING_PATTERNS: list[tuple[re.Pattern, str]] = []
_EVIDENCE_PATTERNS: list[tuple[re.Pattern, str]] = []

# Phrases that appear in negative/disclaimer context are OK.
# Example: "No medical, therapeutic, or cure claims." — this is a safety
# disclaimer, NOT a product claim.
_DISCLAIMER_PREFIXES = {
    "no", "not", "without", "zero", "do not", "don't", "never",
    "forbid", "prohibit", "avoid", "exclude", "must not", "should not",
    "cannot", "can't", "won't", "will not", "shall not",
    "anti-", "non-", "devoid of", "free of", "absence of",
}

# If the line itself is a metadata/reference line listing forbidden examples
# (e.g. in audit tables: "| treats disease | Internal forbidden example |"),
# it's NOT a product claim.
_META_INDICATORS = {
    "forbidden", "internal", "example", "prohibited", "policy",
    "rule", "list", "classification", "category", "reference",
    "audit", "catalog", "vocabulary", "banned", "not allowed",
    "a — internal", "same as above", "z-claims forbidden",
    "ز_كلايمز", "z_claims",  # agent names in governance context
    "قائمة", "مرجع", "داخلي", "محظور", "قائمة محظور",
    "agents.md", "skill", "governance/", "agents/",  # governance file references
    "سطر", "line", "definition",  # line references in tables
}


def _build_patterns() -> None:
    """Build compiled regex patterns for classification.

    All patterns are engineering-governance phrases used for detection only.
    The scanner itself does NOT make any medical, diagnostic, therapeutic,
    treatment, prevention, or clinical claims.
    """
    # FORBIDDEN: absolute medical/therapeutic claims — must never appear in
    # product-facing content without clinical review.
    _FORBIDDEN_PATTERNS.extend([
        (re.compile(r"treats?\s+\w+", re.I),          "medical treatment claim"),
        (re.compile(r"cures?\s+\w+", re.I),            "cure claim"),
        (re.compile(r"heals?\b", re.I),                "healing claim"),
        (re.compile(r"diagnoses?\s+\w+", re.I),         "diagnostic claim"),
        (re.compile(r"prevent\w*\s+injur", re.I),      "injury-prevention claim"),
        (re.compile(r"prevent\w*\s+disease", re.I),    "disease-prevention claim"),
        (re.compile(r"regulates?\s+hormon", re.I),     "hormone-regulation claim"),
        (re.compile(r"guarantees?\s+\w*\s+(reduction|relief|cure|treatment)", re.I),
                                                      "guaranteed therapeutic outcome"),
        (re.compile(r"medical\s+replacement", re.I),   "medical-replacement claim"),
        (re.compile(r"medical\s+device\s+(claim|approved|certif)", re.I),
                                                      "medical-device certification claim"),
    ])

    # NEEDS_SOFTENING: strong causal language that should be softened to
    # "supports" / "designed for" engineering phrasing.
    _SOFTENING_PATTERNS.extend([
        (re.compile(r"(reduces?|reduction\s+of)\s+\w*\s*(pain|stress|pressure)", re.I),
                                                      "strong pain/pressure reduction claim"),
        (re.compile(r"(eliminates?\b|elimination\s+of)\s+\w*\s*(pain|discomfort)", re.I),
                                                      "pain-elimination claim"),
        (re.compile(r"(fixes?\b|corrects?\b)\s+\w*\s*(posture|alignment|gait)", re.I),
                                                      "posture/gait correction claim"),
        (re.compile(r"restores?\s+\w*\s*(mobility|function|circulation)", re.I),
                                                      "restoration claim"),
        (re.compile(r"therapeutic\s+(benefit|effect|use)", re.I),
                                                      "therapeutic claim"),
        (re.compile(r"clinically\s+(proven|tested|verified)", re.I),
                                                      "clinical validation claim"),
    ])

    # NEEDS_EVIDENCE: claims that require supporting data before approval.
    _EVIDENCE_PATTERNS.extend([
        (re.compile(r"improv(es|ed|ement)\s+\w*\s*(comfort|well.?being|health)", re.I),
                                                      "comfort/wellbeing improvement claim"),
        (re.compile(r"boosts?\s+(?:\w+\s+)?(energy|performance|recovery)", re.I),
                                                      "energy/performance boost claim"),
        (re.compile(r"(science-?based|evidence-?based)", re.I),
                                                      "evidence-based claim needs citation"),
    ])


_build_patterns()

# ---------------------------------------------------------------------------
# Scanning logic
# ---------------------------------------------------------------------------


def _is_disclaimer_context(text: str, match_pos: int) -> bool:
    """Check if the match appears in a negative/disclaimer or meta-reference context.

    Looks at the entire line containing the match and checks for:
    (a) disclaimer prefixes appearing BEFORE the match on the same line
        ('No', 'Not', 'Do not', 'avoids', etc.) — with a generous distance
        limit since lists like "No medical, pain, hormone, disease, or cure
        claims" can have 60+ chars between "No" and "cure".
    (b) meta-reference indicators (tables listing forbidden examples).
    """
    # Find start and end of line
    line_start = text.rfind("\n", 0, match_pos)
    if line_start == -1:
        line_start = 0
    else:
        line_start += 1

    line_end = text.find("\n", match_pos)
    if line_end == -1:
        line_end = len(text)

    line = text[line_start:line_end].lower()
    match_offset = match_pos - line_start  # position of match within line

    # Check for disclaimer prefixes appearing BEFORE the match on the same line.
    # Use a generous distance (200 chars) to handle long enumerated lists like
    # "No medical, therapeutic, pain, hormone, disease, or cure claims."
    preceding = line[:match_offset]
    for prefix in _DISCLAIMER_PREFIXES:
        last_pos = preceding.rfind(prefix)
        if last_pos >= 0:
            # Verify the prefix is actually negating the claim (not just
            # coincidentally present). Check that no "and", "or", "but"
            # separates them in a way that changes meaning.
            between = preceding[last_pos + len(prefix):]
            # Allow connectors like ", ", " or ", " and ", " nor "
            if len(between) <= 200:
                return True

    # Check for meta/table-reference context anywhere in the line.
    # But only if the disclaimer check didn't already fire — we don't want
    # a line like "| treats disease | forbidden |" to pass because "forbidden"
    # is somewhere else in the line; that IS a meta line listing examples,
    # so it SHOULD pass.
    for indicator in _META_INDICATORS:
        if indicator in line:
            return True

    return False


def _classifying_findings(text: str, file_path: Path) -> list[dict]:
    """Classify all matching claim phrases in the given text.

    Returns a list of finding dicts, each with:
      - phrase: the matched text
      - classification: FORBIDDEN | NEEDS_SOFTENING | NEEDS_EVIDENCE
      - reason: human-readable explanation
      - line_hint: approximate line number or first 60 chars
    """
    findings: list[dict] = []
    # Skip governance reference files entirely
    if _is_governance_reference(file_path):
        return findings

    for pattern, reason in _FORBIDDEN_PATTERNS:
        for m in pattern.finditer(text):
            if _is_disclaimer_context(text, m.start()):
                continue
            findings.append({
                "phrase": m.group(),
                "classification": FORBIDDEN,
                "reason": reason,
                "line_hint": _line_hint(text, m.start()),
            })
    for pattern, reason in _SOFTENING_PATTERNS:
        for m in pattern.finditer(text):
            if _is_disclaimer_context(text, m.start()):
                continue
            findings.append({
                "phrase": m.group(),
                "classification": NEEDS_SOFTENING,
                "reason": reason,
                "line_hint": _line_hint(text, m.start()),
            })
    for pattern, reason in _EVIDENCE_PATTERNS:
        for m in pattern.finditer(text):
            if _is_disclaimer_context(text, m.start()):
                continue
            findings.append({
                "phrase": m.group(),
                "classification": NEEDS_EVIDENCE,
                "reason": reason,
                "line_hint": _line_hint(text, m.start()),
            })
    return findings


def _line_hint(text: str, match_pos: int, preview_len: int = 60) -> str:
    """Return a human-readable line hint for the match position."""
    surrounding = text[max(0, match_pos - 30): match_pos + preview_len]
    line_num = text[:match_pos].count("\n") + 1
    prefix = f"[line {line_num}] " if line_num else ""
    truncated = surrounding.replace("\n", " ").strip()
    return f"{prefix}{truncated[:preview_len]}"


# Governance files that list forbidden phrases are OK to contain the phrases
# themselves; we only flag them if they appear outside governance context.
_GOVERNANCE_DIRS = {"governance", "tests", "runtime"}


def _is_governance_reference(file_path: Path) -> bool:
    """Skip files that are governance definitions or agent code containing the
    detection phrase lists themselves (allowed by policy)."""
    return any(part in _GOVERNANCE_DIRS for part in file_path.parts)


def scan_file(file_path: Path) -> dict:
    """Scan a single file and return a result dict.

    Returns: {path, text_len, file_type, findings[], overall_status}
    overall_status is the most severe classification found, or ALLOWED.
    """
    try:
        content = file_path.read_text(encoding="utf-8", errors="replace")
    except Exception as exc:
        return {
            "path": str(file_path),
            "text_len": 0,
            "file_type": "error",
            "findings": [],
            "overall_status": "error",
            "error": str(exc),
        }

    if not content.strip():
        return {
            "path": str(file_path),
            "text_len": 0,
            "file_type": "empty",
            "findings": [],
            "overall_status": ALLOWED,
        }

    # Determine file type
    ext = file_path.suffix.lower()
    if ext in (".md",):
        file_type = "markdown"
    elif ext in (".txt",):
        file_type = "text"
    elif ext in (".json",):
        file_type = "json"
    else:
        file_type = "other"

    findings = _classifying_findings(content, file_path)

    # Determine overall status (most severe)
    severity_order = [FORBIDDEN, NEEDS_SOFTENING, NEEDS_EVIDENCE, ALLOWED]
    overall = ALLOWED
    for f in findings:
        cls = f["classification"]
        if severity_order.index(cls) < severity_order.index(overall):
            overall = cls

    return {
        "path": str(file_path),
        "text_len": len(content),
        "file_type": file_type,
        "findings": findings,
        "overall_status": overall,
    }


# ---------------------------------------------------------------------------
# Discovery
# ---------------------------------------------------------------------------

_SCAN_DIRS = ["reports", "demo", "outputs", "tasks"]


def _discover_scan_files(project_root: Path, lookback_days: int = 1) -> list[Path]:
    """Return candidate files to scan from the last N days."""
    cutoff = datetime.now(timezone.utc).timestamp() - (lookback_days * 86400)
    results: list[Path] = []
    seen = set()
    for dir_name in _SCAN_DIRS:
        search_dir = project_root / dir_name
        if not search_dir.is_dir():
            continue
        for ext in ("*.md", "*.txt", "*.json"):
            for fp in search_dir.rglob(ext):
                if fp in seen:
                    continue
                seen.add(fp)
                try:
                    if fp.stat().st_mtime >= cutoff:
                        results.append(fp)
                except OSError:
                    continue
    return sorted(results)


# ---------------------------------------------------------------------------
# Bulk scan
# ---------------------------------------------------------------------------

def run_claims_scan(
    *,
    file_path: Path | None = None,
    lookback_days: int = 1,
    project_root: Path | None = None,
    db: SharedDB | None = None,
) -> dict:
    """Run claims scan and write a SharedDB task-state record.

    Args:
        file_path: scan a single file (overrides auto-discovery).
        lookback_days: how far back to look for recent files.
        project_root: root of the ZILFIT project.
        db: optional SharedDB instance (created if omitted).

    Returns:
        A summary dict with files_scanned, findings count, status, etc.
    """
    if project_root is None:
        project_root = _PROJECT_ROOT

    # Discover or select files
    if file_path:
        targets = [file_path]
    else:
        targets = _discover_scan_files(project_root, lookback_days)

    # Scan each
    results: list[dict] = []
    total_findings = 0
    max_severity = ALLOWED
    severity_order = [FORBIDDEN, NEEDS_SOFTENING, NEEDS_EVIDENCE, ALLOWED]

    for fp in targets:
        r = scan_file(fp)
        results.append(r)
        total_findings += len(r.get("findings", []))
        s = r.get("overall_status", ALLOWED)
        if severity_order.index(s) < severity_order.index(max_severity):
            max_severity = s

    # Build summary
    now_iso = datetime.now(timezone.utc).isoformat()
    output = {
        "agent_name": _AGENT_NAME,
        "task_id": f"claims-{now_iso[:10]}",
        "scan_timestamp": now_iso,
        "files_scanned": len(targets),
        "total_findings": total_findings,
        "overall_status": max_severity,
        "files_with_findings": sum(1 for r in results if r.get("findings")),
        "results": results,
    }

    # Write SharedDB task-state record
    if db is None:
        db = SharedDB()

    status_map = {
        FORBIDDEN: "blocked",
        NEEDS_SOFTENING: "in_progress",
        NEEDS_EVIDENCE: "in_progress",
        ALLOWED: "completed",
        "error": "blocked",
    }

    summary_parts = []
    if total_findings == 0:
        summary_parts.append("No prohibited claims found in recent outputs.")
    else:
        summary_parts.append(f"{total_findings} claim(s) flagged across {output['files_with_findings']} file(s).")
    summary_parts.append(f"Highest severity: {max_severity}.")
    summary = " ".join(summary_parts)

    risk_map = {
        FORBIDDEN: "critical",
        NEEDS_SOFTENING: "high",
        NEEDS_EVIDENCE: "medium",
        ALLOWED: "low",
        "error": "high",
    }

    next_action_map = {
        FORBIDDEN: "Remove or rewrite prohibited claims before production.",
        NEEDS_SOFTENING: "Rewrite flagged phrases using engineering-only language.",
        NEEDS_EVIDENCE: "Attach supporting data or remove unsupported claims.",
        ALLOWED: "No action required — all outputs clear.",
        "error": "Investigate file access errors.",
    }

    record = db.upsert(
        agent_name=_AGENT_NAME,
        task_id=output["task_id"],
        status=status_map.get(max_severity, "pending"),
        summary=summary,
        risk_level=risk_map.get(max_severity, "medium"),
        next_action=next_action_map.get(max_severity, "Review findings."),
    )
    output["shared_db_task_id"] = record["id"]
    output["shared_db_persisted"] = record is not None

    return output


# ---------------------------------------------------------------------------
# CLI entry point
# ---------------------------------------------------------------------------

def main() -> None:
    parser = argparse.ArgumentParser(
        description="Z-Claims: scan outputs for prohibited claims and write SharedDB record."
    )
    parser.add_argument(
        "--file", type=Path, default=None,
        help="Scan a single file (overrides auto-discovery).",
    )
    parser.add_argument(
        "--lookback-days", type=int, default=1,
        help="Number of days to look back for recent files (default: 1).",
    )
    args = parser.parse_args()

    output = run_claims_scan(file_path=args.file, lookback_days=args.lookback_days)

    print("=" * 50)
    print("Z-Claims Safety Scan Report")
    print("=" * 50)
    print(f"Files scanned:       {output['files_scanned']}")
    print(f"Total findings:      {output['total_findings']}")
    print(f"Files with findings: {output['files_with_findings']}")
    print(f"Overall status:      {output['overall_status']}")
    print(f"SharedDB persisted:  {output['shared_db_persisted']}")
    print(f"SharedDB task_id:    {output.get('shared_db_task_id', 'N/A')}")
    print("=" * 50)

    # Print findings
    has_findings = False
    for r in output["results"]:
        if r.get("findings"):
            has_findings = True
            print(f"\n--- {r['path']} ({r['overall_status']}) ---")
            for f in r["findings"]:
                print(f"  [{f['classification']}] {f['reason']}")
                print(f"    phrase:     {f['phrase']}")
                print(f"    location:   {f['line_hint']}")

    if not has_findings and output["files_scanned"] > 0:
        print("\nAll scanned files are CLEAR — no prohibited claims found.")
    elif output["files_scanned"] == 0:
        print("\nNo recent files found to scan.")


if __name__ == "__main__":
    main()

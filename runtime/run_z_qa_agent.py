"""Z-QA: Runtime script that reads local agent output/report files and writes
QA task-state records into SharedDB.

Z-QA evaluates recent daily reports and agent output JSON files for structural
completeness (not content validity).  It checks:
  - File exists and is non-empty
  - Reports contain date header or ISO date pattern
  - JSON outputs parse cleanly and contain expected top-level keys
  - Agent name / task_id presence for traceability

Each evaluated file produces a QA record persisted to SharedDB.

Usage:
    # Evaluate all reports and outputs from the last N days (default: 1)
    python3 -m runtime.run_z_qa_agent

    # Evaluate a specific file
    python3 -m runtime.run_z_qa_agent --file reports/daily/foo.md

    # Adjust lookback window
    python3 -m runtime.run_z_qa_agent --lookback-days 7
"""

import argparse
import json
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
_AGENT_NAME = "Z-QA"
_DATE_PATTERN = re.compile(r"\d{4}-\d{2}-\d{2}")

# Expected top-level keys for different file types
_REQUIRED_JSON_KEYS = {"task_id", "agent_name"}
_REPORT_INDICATORS = [
    "Summary", "summary", "Tests", "tests", "Files", "Risk", "risk",
    "Action", "action", "Findings", "findings", "Status", "status",
]

# ---------------------------------------------------------------------------
# Discovery
# ---------------------------------------------------------------------------

def _discover_report_files(project_root: Path, lookback_days: int = 1) -> list[Path]:
    """Return report markdown files from the last N days."""
    reports_dir = project_root / "reports" / "daily"
    if not reports_dir.is_dir():
        return []

    cutoff = datetime.now(timezone.utc).timestamp() - (lookback_days * 86400)
    results: list[Path] = []
    for fp in sorted(reports_dir.glob("*.md")):
        if fp.stat().st_mtime >= cutoff:
            results.append(fp)
    return results


def _discover_json_outputs(project_root: Path, lookback_days: int = 1) -> list[Path]:
    """Return JSON output files from agents (recently modified)."""
    # Search common output locations
    candidates: list[Path] = []
    for search_path in [
        project_root / "reports",
        project_root / "runtime",
        project_root,
    ]:
        if search_path.is_dir():
            for fp in search_path.rglob("*.json"):
                candidates.append(fp)

    cutoff = datetime.now(timezone.utc).timestamp() - (lookback_days * 86400)
    results: list[Path] = []
    seen = set()
    for fp in sorted(candidates, key=lambda p: p.stat().st_mtime, reverse=True):
        if fp in seen:
            continue
        seen.add(fp)
        # Skip test fixtures and __pycache__
        if "_cache" in str(fp) or "fixture" in str(fp).lower():
            continue
        if fp.stat().st_mtime >= cutoff:
            try:
                raw = fp.read_text(encoding="utf-8")[:200]
                # Quick check: is it JSON that looks like an agent output?
                if '"task_id"' in raw or '"agent"' in raw:
                    results.append(fp)
            except Exception:
                pass
        if len(results) >= 50:
            break
    return results


# ---------------------------------------------------------------------------
# Evaluation
# ---------------------------------------------------------------------------

def evaluate_report_md(path: Path) -> dict:
    """Evaluate a markdown report for structural completeness.

    Returns a dict with:
        status: 'passed' | 'warning' | 'failed'
        checks: list of (check_name, bool)
        summary: human-readable summary
    """
    checks: list[tuple[str, bool]] = []
    try:
        content = path.read_text(encoding="utf-8")
    except Exception as exc:
        return {
            "status": "failed",
            "checks": [("readable", False)],
            "summary": f"Cannot read file: {exc}",
        }

    # 1. Non-empty
    checks.append(("non_empty", len(content.strip()) > 0))

    # 2. Date present
    checks.append(("date_present", bool(_DATE_PATTERN.search(content))))

    # 3. Has structured sections
    has_sections = any(ind.lower() in content.lower() for ind in _REPORT_INDICATORS)
    checks.append(("has_sections", has_sections))

    # 4. Reasonable size (> 200 chars suggests real content)
    checks.append(("size_ok", len(content.strip()) >= 200))

    passed = sum(1 for _, ok in checks if ok)
    total = len(checks)
    ratio = passed / max(total, 1)

    if ratio >= 0.75:
        status = "passed"
    elif ratio >= 0.5:
        status = "warning"
    else:
        status = "failed"

    summary = f"Report QA: {passed}/{total} structural checks passed"
    details = [name for name, ok in checks if not ok]
    if details:
        summary += f" ({', '.join(details)} missing)"

    return {"status": status, "checks": checks, "summary": summary}


def evaluate_json_output(path: Path) -> dict:
    """Evaluate a JSON agent output for structural completeness."""
    checks: list[tuple[str, bool]] = []
    try:
        raw = path.read_text(encoding="utf-8")
    except Exception as exc:
        return {
            "status": "failed",
            "checks": [("readable", False)],
            "summary": f"Cannot read file: {exc}",
        }

    # 1. Valid JSON
    try:
        data = json.loads(raw)
        checks.append(("valid_json", True))
    except json.JSONDecodeError as exc:
        return {
            "status": "failed",
            "checks": [("readable", True), ("valid_json", False)],
            "summary": f"Invalid JSON: {exc}",
        }

    # 2. Is a dict (not just a list)
    checks.append(("is_dict", isinstance(data, dict)))

    # 3. Has task_id (traceability)
    checks.append(("has_task_id", "task_id" in data))

    # 4. Has agent_name or agent field
    has_agent = "agent_name" in data or "agent" in data
    checks.append(("has_agent", has_agent))

    # 5. Non-empty dict
    checks.append(("non_empty", len(data) > 0))

    passed = sum(1 for _, ok in checks if ok)
    total = len(checks)
    ratio = passed / max(total, 1)

    if ratio >= 0.8:
        status = "passed"
    elif ratio >= 0.5:
        status = "warning"
    else:
        status = "failed"

    summary = f"JSON QA: {passed}/{total} structural checks passed"
    details = [name for name, ok in checks if not ok]
    if details:
        summary += f" ({', '.join(details)} missing)"

    return {"status": status, "checks": checks, "summary": summary}


# ---------------------------------------------------------------------------
# Main pipeline
# ---------------------------------------------------------------------------

def run_qa(
    project_root: Path | None = None,
    lookback_days: int = 1,
    single_file: str | None = None,
    db: SharedDB | None = None,
) -> dict:
    """Run Z-QA evaluation pipeline.

    Returns a summary dict with counts and per-file results.
    """
    root = project_root or _PROJECT_ROOT
    if db is None:
        db = SharedDB()

    results: list[dict] = []
    task_counter = 0

    # --- Specific file mode ---
    if single_file:
        fp = Path(single_file)
        if not fp.is_file():
            return {"error": f"File not found: {fp}", "results": []}
        task_counter += 1
        task_id = f"zqa-{datetime.now(timezone.utc).strftime('%Y%m%d%H%M%S')}-{task_counter:03d}"

        if fp.suffix == ".md":
            ev = evaluate_report_md(fp)
        elif fp.suffix == ".json":
            ev = evaluate_json_output(fp)
        else:
            ev = {"status": "warning", "checks": [], "summary": f"Unknown file type: {fp.suffix}"}

        # Map QA status to SharedDB-compatible status
        db_status_map = {"passed": "completed", "warning": "blocked", "failed": "pending"}
        db_status = db_status_map.get(ev["status"], "pending")
        risk = "low" if ev["status"] == "passed" else (
            "medium" if ev["status"] == "warning" else "high"
        )

        db.upsert(
            agent_name=_AGENT_NAME,
            task_id=task_id,
            status=db_status,
            summary=ev["summary"],
            risk_level=risk,
            next_action=f"Review {fp.name}" if ev["status"] != "passed" else "No action needed",
        )

        results.append({
            "file": str(fp),
            "task_id": task_id,
            **ev,
        })
        return {"results": results}

    # --- Bulk scan mode ---
    files_to_check: list[tuple[Path, str]] = []

    for fp in _discover_report_files(root, lookback_days):
        files_to_check.append((fp, "md"))
    for fp in _discover_json_outputs(root, lookback_days):
        files_to_check.append((fp, "json"))

    for fp, ftype in files_to_check:
        task_counter += 1
        task_id = f"zqa-{datetime.now(timezone.utc).strftime('%Y%m%d')}-{task_counter:03d}"

        if ftype == "md":
            ev = evaluate_report_md(fp)
        else:
            ev = evaluate_json_output(fp)

        # Map QA status to SharedDB-compatible status
        db_status_map = {"passed": "completed", "warning": "blocked", "failed": "pending"}
        db_status = db_status_map.get(ev["status"], "pending")
        risk = "low" if ev["status"] == "passed" else (
            "medium" if ev["status"] == "warning" else "high"
        )

        db.upsert(
            agent_name=_AGENT_NAME,
            task_id=task_id,
            status=db_status,
            summary=ev["summary"],
            risk_level=risk,
            next_action=f"Review {fp.name}" if ev["status"] != "passed" else "No action needed",
        )

        results.append({
            "file": str(fp.relative_to(root)),
            "task_id": task_id,
            **ev,
        })

    # --- Summary stats ---
    passed = sum(1 for r in results if r["status"] == "passed")
    warnings = sum(1 for r in results if r["status"] == "warning")
    failed = sum(1 for r in results if r["status"] == "failed")

    return {
        "total": len(results),
        "passed": passed,
        "warnings": warnings,
        "failed": failed,
        "results": results,
    }


# ---------------------------------------------------------------------------
# CLI entry point
# ---------------------------------------------------------------------------

def main() -> dict:
    parser = argparse.ArgumentParser(description="Z-QA: Evaluate local agent reports and write QA records to SharedDB")
    parser.add_argument("--file", type=str, default=None, help="Evaluate a single specific file")
    parser.add_argument("--lookback-days", type=int, default=1, help="Number of days to look back (default: 1)")
    parser.add_argument("--out", type=Path, default=None, help="Write JSON output to this file")
    args = parser.parse_args()

    output = run_qa(
        single_file=args.file,
        lookback_days=args.lookback_days,
    )

    if args.out:
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(json.dumps(output, indent=2), encoding="utf-8")

    # SharedDB self-report: Z-QA has run
    db = SharedDB()
    task_id = f"zqa-runtime-{datetime.now(timezone.utc).strftime('%Y%m%d%H%M%S')}"
    summary_str = f"Z-QA evaluated {output.get('total', 0)} files: {output.get('passed', 0)} passed, {output.get('warnings', 0)} warnings, {output.get('failed', 0)} failed"
    db.upsert(
        agent_name=_AGENT_NAME,
        task_id=task_id,
        status="completed",
        summary=summary_str,
        risk_level="low",
        next_action="Await next run or manual file evaluation",
    )
    output["shared_db_persisted"] = True
    output["qa_task_id"] = task_id

    print(json.dumps(output, indent=2))
    return output


if __name__ == "__main__":
    main()

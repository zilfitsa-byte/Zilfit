#!/usr/bin/env python3
"""Export project handoff — produce a portable ZIP of ZILFIT engineering assets.

Includes:
    zilfit_orthotics/   tools/   docs/   sample_packs/
    production_inputs/csv_results/   requirements.txt   README*

Excludes:
    .venv*   __pycache__   large zip datasets
    production_inputs/batch/   production_inputs/real_scans/
    node_modules   .git   simulation/   docker/

Usage:
    python3 tools/export_project_handoff.py [--output exports/ZILFIT_HANDOFF_YYYYMMDD.zip]
"""

import argparse
import os
import sys
import zipfile
from datetime import datetime
from pathlib import Path

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

ROOT = Path(__file__).resolve().parent.parent

INCLUDE = [
    "zilfit_orthotics/",
    "tools/",
    "docs/",
    "sample_packs/",
    "production_inputs/csv_results/",
    "requirements.txt",
    "README.md",
    "README",
    "LICENSE",
    "api.py",
    "sample_landmarks.json",
    "sample_data/",
    "smart_capsule_data/",
    "smart_capsule_reports/",
    "exports/",
    "prototype/reference_samples/",
    "prototype/validation/",
    "prototype/P001_DESIGN_BRIEF.md",
    "prototype/P01_BALANCE_PROTOTYPE.json",
    "validation/stl/",
    "validation/run_release_readiness.py",
    "validation/run_sample_archive.py",
    "validation/run_simulation_pipeline.py",
    "editions/",
    "reports/daily/",
    "research/daily/",
    "research/autopull/",
    "evidence/",
]

EXCLUDE_PATTERNS = [
    ".venv",
    "__pycache__",
    "node_modules",
    ".git",
    "docker",
    "simulation",
    "batch",
    "real_scans",
    ".pyc",
    ".DS_Store",
    "logs",
    "*.egg-info",
]

EXCLUDE_DIRS = [
    "production_inputs/batch",
    "production_inputs/real_scans",
    ".commandcode",
    "runtime",
    "rules",
    "manufacturing/print_specs",
    "manufacturing/archive",
    "tests/fixtures/print_specs",
    "tests/fixtures/release",
    "tooling",
    "reports/audit",
    "reports/scan_audit",
]

# ---------------------------------------------------------------------------
# Logic
# ---------------------------------------------------------------------------

def _should_exclude(rel_path: str) -> bool:
    parts = rel_path.replace("\\", "/").split("/")
    for excl in EXCLUDE_DIRS:
        excl_parts = excl.replace("\\", "/").split("/")
        if parts[:len(excl_parts)] == excl_parts:
            return True
    return False


def _match_include(rel_path: str) -> bool:
    for inc in INCLUDE:
        if inc.endswith("/"):
            if rel_path.startswith(inc) or rel_path + "/" == inc:
                return True
        else:
            if rel_path == inc or rel_path.startswith(inc + "/"):
                return True
    return False


def create_handoff(output_path: str, dry_run: bool = False) -> list:
    """Create handoff ZIP. Returns list of included file paths."""
    included = []

    # Ensure output directory exists
    out = Path(output_path)
    out.parent.mkdir(parents=True, exist_ok=True)

    # Collect files
    for root, dirs, files in os.walk(ROOT):
        # Filter dirs in-place
        rel_dir = os.path.relpath(root, ROOT).replace("\\", "/")
        if rel_dir == ".":
            rel_dir = ""

        dirs_to_remove = []
        for d in dirs:
            check = (rel_dir + "/" + d).lstrip("/") if rel_dir else d
            if _should_exclude(check):
                dirs_to_remove.append(d)
                continue
            for pat in EXCLUDE_PATTERNS:
                if pat in d or (pat.startswith("*") and d.endswith(pat[1:])):
                    dirs_to_remove.append(d)
                    break
        for d in dirs_to_remove:
            dirs.remove(d)

        for f in files:
            file_rel = (rel_dir + "/" + f).lstrip("/") if rel_dir else f
            for pat in EXCLUDE_PATTERNS:
                if pat.startswith("*") and f.endswith(pat[1:]):
                    break
                if pat in f and not pat.startswith("*"):
                    break
            else:
                if _match_include(file_rel) and not _should_exclude(file_rel):
                    included.append(file_rel)

    included.sort()

    if dry_run:
        print(f"Would include {len(included)} files:")
        for f in included:
            print(f"  {f}")
        return included

    with zipfile.ZipFile(str(out), "w", zipfile.ZIP_DEFLATED) as zf:
        for f in included:
            arcname = f"ZILFIT_HANDOFF/{f}"
            zf.write(str(ROOT / f), arcname)

    size_mb = out.stat().st_size / (1024 * 1024)
    print(f"Created: {out} ({size_mb:.2f} MB)")
    print(f"Files included: {len(included)}")
    return included


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def main():
    today = datetime.now().strftime("%Y%m%d")
    default_out = str(ROOT / f"exports/ZILFIT_HANDOFF_{today}.zip")

    parser = argparse.ArgumentParser(description="Export ZILFIT project handoff ZIP.")
    parser.add_argument("--output", default=default_out,
                        help=f"Output ZIP path (default: {default_out})")
    parser.add_argument("--dry-run", action="store_true",
                        help="List files without creating ZIP")
    args = parser.parse_args()

    create_handoff(args.output, dry_run=args.dry_run)
    return 0


if __name__ == "__main__":
    sys.exit(main())

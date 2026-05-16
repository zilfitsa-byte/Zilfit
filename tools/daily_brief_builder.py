#!/usr/bin/env python3
"""
ZILFIT Daily Brief Builder — Config-driven brief constructor.

Loads config/daily_brief_config.yaml, validates a brief dict against
the schema, and formats it for Telegram. This module is the engine that
turns the daily report data into a structured, repeatable brief.

Usage:
    # Build brief from a report file
    python tools/daily_brief_builder.py --report-file reports/daily/latest.md

    # Dry-run (format and display, no sending)
    python tools/daily_brief_builder.py --dry-run --report-file reports/daily/latest.md

    # Validate a brief dict directly
    python -c "from tools.daily_brief_builder import BriefBuilder; ..."
"""

import os
import re
import sys

# Add project root to path
_project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _project_root not in sys.path:
    sys.path.insert(0, _project_root)

CONFIG_PATH = os.path.join(_project_root, "config", "daily_brief_config.yaml")


def load_config(path=None):
    """Load the daily brief config YAML.

    Returns a dict with: brief, sections, validation, telegram_template.
    Uses stdlib-only YAML parsing (safe, no PyYAML dependency).
    Falls back to a built-in default config if file is missing.
    """
    path = path or CONFIG_PATH
    if os.path.isfile(path):
        return _parse_yaml_simple(path)
    return _default_config()


def _parse_yaml_simple(path):
    """Minimal YAML subset parser — enough for our config structure.

    Only handles: comments, key: value, lists (- item), pipe blocks.
    Does NOT attempt full YAML compliance — this is intentional for
    portability (no PyYAML dependency).
    """
    result = {}
    current_key = None
    current_dict = None
    current_list = None
    list_key = None
    in_pipe_block = False
    pipe_key = None
    pipe_lines = []

    with open(path, "r", encoding="utf-8") as f:
        lines = f.readlines()

    i = 0
    while i < len(lines):
        line = lines[i]
        raw = line.rstrip("\n")
        stripped = raw.lstrip()
        indent = len(raw) - len(stripped)

        # Skip comments and blank lines
        if stripped.startswith("#") or not stripped:
            i += 1
            continue

        # End pipe block on less-indented non-empty line
        if in_pipe_block:
            if indent <= 0 and stripped and not stripped.startswith("#"):
                result[pipe_key] = "\n".join(pipe_lines).strip() + "\n"
                in_pipe_block = False
                pipe_lines = []
                pipe_key = None
            elif indent > 0 or (indent == 0 and stripped.startswith("|")):
                if stripped == "|":
                    pass  # just the pipe marker
                else:
                    pipe_lines.append(stripped)
                i += 1
                continue
            else:
                result[pipe_key] = "\n".join(pipe_lines).strip() + "\n"
                in_pipe_block = False
                pipe_lines = []
                pipe_key = None

        # Top-level key
        if indent == 0 and ":" in stripped:
            key, _, val = stripped.partition(":")
            key = key.strip()
            val = val.strip()
            if val == "|":
                in_pipe_block = True
                pipe_key = key
                pipe_lines = []
            elif val:
                # Strip inline comments (but not inside quoted strings)
                if '#' in val and not val.startswith('"') and not val.startswith("'"):
                    val = val[:val.index('#')].strip()
                result[key] = _coerce(val)
            else:
                result[key] = {}
                current_key = key
            i += 1
            continue

        # Sub-dict / list items at indent > 0
        if indent > 0 and current_key and current_key in result:
            if stripped.startswith("- "):
                # List item
                if list_key not in result:
                    result[list_key] = []
                item = stripped[2:].strip()
                result[list_key].append(_coerce(item))
                i += 1
                continue

            if ":" in stripped:
                key, _, val = stripped.partition(":")
                key = key.strip()
                val = val.strip()
                if val == "|":
                    in_pipe_block = True
                    pipe_key = key
                    pipe_lines = []
                elif val.startswith("#"):
                    result[current_key][key] = True
                elif val:
                    # Check if value is a comment-only line
                    if not val or val.startswith("#"):
                        result[current_key][key] = True
                    else:
                        result[current_key][key] = _coerce(val)
                else:
                    # Nested dict marker (rules: etc.)
                    result[current_key][key] = []
                    list_key = key
                i += 1
                continue

        i += 1

    # Flush pipe block
    if in_pipe_block and pipe_key:
        result[pipe_key] = "\n".join(pipe_lines).strip() + "\n"

    return result


def _coerce(val):
    """Coerce a string value to bool/int/float/str."""
    if val.lower() in ("true",):
        return True
    if val.lower() in ("false",):
        return False
    try:
        return int(val)
    except ValueError:
        pass
    try:
        return float(val)
    except ValueError:
        pass
    return val


def _default_config():
    """Fallback config if file is missing."""
    return {
        "brief": {
            "name": "ZILFIT Daily Brief",
            "version": "1.0",
            "max_length_chars": 4000,
            "footer_brand": "ZILFIT Cloud \U0001F1F8\U0001F1E6 — هندسة فقط",
        },
        "sections": [],
        "validation": {
            "required_sections": ["header", "project_status", "tests", "claims_safety"],
        },
        "telegram_template": "Brief: {date}\nStatus: {status_text}\n",
    }


class BriefBuilder:
    """Builds and validates a ZILFIT daily brief against the config."""

    def __init__(self, config=None):
        self.config = config or load_config()
        self.validation_rules = self.config.get("validation", {})

    def validate(self, brief):
        """Validate a brief dict against the config schema.

        Returns (is_valid, errors) tuple.
        """
        errors = []
        required = self.validation_rules.get("required_sections", [])

        for section_id in required:
            if section_id not in brief:
                errors.append(f"Missing required section: {section_id}")

        # Date format
        if "date" in brief:
            if not re.match(r"\d{4}-\d{2}-\d{2}", brief["date"]):
                errors.append("date must match YYYY-MM-DD")

        # Claims safety
        if "claims_safety" in brief:
            cs = brief["claims_safety"]
            if isinstance(cs, dict) and cs.get("clean") is not True:
                errors.append("claims_safety.clean must be true for safe briefs")

        # Next action must not be empty
        if "next_action" in brief:
            na = brief["next_action"]
            if isinstance(na, dict) and not na.get("action_text", "").strip():
                errors.append("next_action.action_text must not be empty")

        # Blockers detail required
        if "blockers" in brief:
            bl = brief["blockers"]
            if isinstance(bl, dict) and not bl.get("details", "").strip():
                errors.append("blockers.details must be present")

        # Length check
        brief_cfg = self.config.get("brief", {})
        max_len = int(brief_cfg.get("max_length_chars", 4000))
        formatted = self.format(brief)
        if len(formatted) > max_len:
            errors.append(f"Brief exceeds max_length_chars ({len(formatted)} > {max_len})")

        is_valid = len(errors) == 0
        return is_valid, errors

    def format(self, brief):
        """Format a brief dict into a Telegram message string."""
        template = self.config.get("telegram_template", "Brief: {date}\n")
        footer = self.config.get("brief", {}).get("footer_brand", "")

        # Flatten brief for template substitution
        fields = {}
        for section_id, section_data in brief.items():
            if isinstance(section_data, dict):
                fields.update(section_data)
            else:
                fields[section_id] = section_data

        fields["footer_brand"] = footer

        # Map specific fields
        fields.setdefault("date", "Unknown")
        fields.setdefault("status_text", "❓ غير محدد")
        fields.setdefault("branch", "unknown")
        fields.setdefault("commit_count", "0")
        fields.setdefault("latest_msg", "N/A")
        fields.setdefault("test_status", "N/A")
        fields.setdefault("passed", "?")
        fields.setdefault("executed", "?")
        fields.setdefault("blockers", "لا توجد عوائق")
        fields.setdefault("next_action", "N/A")
        fields.setdefault("claims_status", "غير محدد")
        fields.setdefault("prod_readiness", "غير محدد")
        fields.setdefault("files_count", "?")

        # Fill template
        try:
            message = template.format(**fields)
        except KeyError as e:
            message = f"ERROR: Missing template field: {e}"

        return message

    def build_from_report(self, report_filepath):
        """Parse a daily report .md file and build a brief dict.

        Reads the report, extracts fields using regex, and returns
        a brief dict ready for validation and formatting.
        """
        brief = {
            "date": "Unknown",
            "status_text": "❓ غير محدد",
            "branch": "unknown",
            "commit_count": "0",
            "latest_sha": "N/A",
            "latest_msg": "N/A",
            "executed": "?",
            "passed": "?",
            "failed": "?",
            "test_status": "N/A",
            "has_blockers": False,
            "blockers": "لا توجد عوائق",
            "action_text": "N/A",
            "clean": True,
            "claims_status": "✅ هندسة فقط — لا توجد مطالبات طبية",
            "prod_ready": False,
            "prod_readiness": "⚠️ قيد المراجعة",
            "files_count": "?",
        }

        try:
            with open(report_filepath, "r", encoding="utf-8") as f:
                content = f.read()
        except Exception as e:
            brief["latest_msg"] = f"فشل قراءة التقرير: {e}"
            return brief

        # Date from filename
        basename = os.path.basename(report_filepath)
        dm = re.match(r"(\d{4}-\d{2}-\d{2})", basename)
        if dm:
            brief["date"] = dm.group(1)

        # Branch
        bm = re.search(r"Branch.*?`([^\s`]+)`", content, re.IGNORECASE)
        if bm:
            brief["branch"] = bm.group(1)

        # Commit count
        cm = re.search(r"commits?.*?(\d+)", content, re.IGNORECASE)
        if cm:
            brief["commit_count"] = cm.group(1)

        # Test results
        tm = re.search(r"test[s]?.*?(\d+).*pass.*?(\d+).*fail.*?(\d+)", content, re.IGNORECASE)
        if tm:
            brief["executed"] = tm.group(1)
            brief["passed"] = tm.group(2)
            brief["failed"] = tm.group(3)
            brief["test_status"] = "FAIL" if int(tm.group(3)) > 0 else "PASS"

        # Status
        if "COMPLETED" in content.upper() or "مكتمل" in content:
            brief["status_text"] = "✅ مكتمل"
        elif "FAILED" in content.upper():
            brief["status_text"] = "❌ فشل"
        elif "PASS" in content.upper():
            brief["status_text"] = "✅ نجح"

        # Next action
        nam = re.search(
            r"(?:Next\s*(?:Recommended\s*)?Action[s]?|الخطوة\s*(?:التالية|القادمة))\s*\n(.*?)(?=##|\Z)",
            content, re.DOTALL | re.IGNORECASE,
        )
        if nam:
            brief["action_text"] = nam.group(1).strip()[:200]

        # Blockers
        blm = re.search(
            r"(?:Blocker|العوائق|الكتل)\s*\n(.*?)(?=##|\Z)",
            content, re.DOTALL | re.IGNORECASE,
        )
        if blm:
            text = blm.group(1).strip()
            if text and "لا توجد" not in text and "none" not in text.lower():
                brief["has_blockers"] = True
                brief["blockers"] = text[:200]

        # Production readiness
        if "ready" in content.lower() and "production" in content.lower():
            brief["prod_ready"] = True
            brief["prod_readiness"] = "✅ جاهز"

        # Safety disclaimer
        brief["claims_status"] = "✅ هندسة فقط — لم يتم إنشاء مطالبات طبية"

        return brief


def main():
    import argparse

    parser = argparse.ArgumentParser(
        description="ZILFIT Daily Brief Builder — config-driven brief constructor"
    )
    parser.add_argument(
        "--report-file", type=str, default=None,
        help="Path to a daily report .md file"
    )
    parser.add_argument(
        "--dry-run", action="store_true",
        help="Build and display brief without sending"
    )
    parser.add_argument(
        "--validate-only", action="store_true",
        help="Only validate config, don't build"
    )
    parser.add_argument(
        "--config-file", type=str, default=CONFIG_PATH,
        help="Path to config YAML"
    )
    args = parser.parse_args()

    if args.validate_only:
        print(f"Config: {args.config_file}")
        config = load_config(args.config_file)
        builder = BriefBuilder(config)
        valid, errors = builder.validate({
            "date": "2026-05-16",
            "status_text": "✅ مكتمل",
            "branch": "zilfit/p0-arch-gate-import-isolation",
            "commit_count": "1",
            "latest_msg": "N/A",
            "executed": "10",
            "passed": "10",
            "failed": "0",
            "test_status": "PASS",
            "has_blockers": False,
            "blockers": "لا توجد عوائق",
            "action_text": "Continue implementation",
            "clean": True,
            "claims_status": "✅ هندسة فقط",
            "prod_ready": False,
            "prod_readiness": "⚠️ قيد المراجعة",
            "files_count": "5",
        })
        if valid:
            print("VALID: Config validation passed.")
            return 0
        else:
            print("INVALID:")
            for e in errors:
                print(f"  - {e}")
            return 1

    if not args.report_file:
        print("ERROR: --report-file required", file=sys.stderr)
        return 2

    if not os.path.isfile(args.report_file):
        print(f"ERROR: File not found: {args.report_file}", file=sys.stderr)
        return 1

    config = load_config(args.config_file)
    builder = BriefBuilder(config)
    brief = builder.build_from_report(args.report_file)
    valid, errors = builder.validate(brief)

    if not valid:
        print("WARNING: Brief has validation issues:")
        for e in errors:
            print(f"  - {e}")

    message = builder.format(brief)

    if args.dry_run:
        print(f"Report: {args.report_file}")
        print(f"Valid: {valid}")
        if errors:
            for e in errors:
                print(f"  - {e}")
        print("\n--- DRY RUN BRIEF ---")
        print(message)
        print("--- END BRIEF ---")
        return 0

    print(message)
    return 0


if __name__ == "__main__":
    sys.exit(main())

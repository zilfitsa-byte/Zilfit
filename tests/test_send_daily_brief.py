"""Tests for tools/send_daily_brief.py — mocks/stdlib only, no network calls."""

import os
import sys
import tempfile
import unittest
from unittest.mock import patch, MagicMock

# Ensure project root is on the path
_project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _project_root not in sys.path:
    sys.path.insert(0, _project_root)

from tools.send_daily_brief import (
    find_latest_report,
    parse_report_brief,
    format_telegram_brief,
    main,
)
from tools.daily_brief_builder import BriefBuilder, _default_config, CONFIG_PATH


class TestFormatTelegramBrief(unittest.TestCase):
    """Test the telegram message formatter."""

    def test_basic_formatting(self):
        """Formats all fields into a Telegram message."""
        brief = {
            "date": "2026-05-16",
            "status": "✅ مكتمل",
            "files_touched": "3",
            "summary": "Created the daily brief sender.",
            "risks": "No risks.",
            "blockers": "No blockers.",
            "next_action": "Run dry-run test.",
        }
        msg = format_telegram_brief(brief)
        self.assertIn("ZILFIT", msg)
        self.assertIn("2026-05-16", msg)
        self.assertIn("مكتمل", msg)
        self.assertIn("3", msg)
        self.assertIn("نبضة يومية", msg)

    def test_no_sensitive_data(self):
        """Message does not contain secrets or tokens."""
        brief = {
            "date": "2026-05-16",
            "status": "✅ مكتمل",
            "files_touched": "1",
            "summary": "Normal summary text.",
            "risks": "No risks.",
            "blockers": "None.",
            "next_action": "Commit changes.",
        }
        msg = format_telegram_brief(brief)
        self.assertNotIn("token", msg.lower())
        self.assertNotIn("secret", msg.lower())
        self.assertNotIn("password", msg.lower())

    def test_truncation(self):
        """Long summary and next_action are truncated."""
        brief = {
            "date": "2026-05-16",
            "status": "✅ مكتمل",
            "files_touched": "5",
            "summary": "A" * 500,
            "risks": "Some risk.",
            "blockers": "No blockers.",
            "next_action": "B" * 400,
        }
        msg = format_telegram_brief(brief)
        self.assertLess(len(msg), 4000)  # Well within Telegram limit


class TestParseReportBrief(unittest.TestCase):
    """Test daily report content parser."""

    def _write_temp_report(self, content, filename="2026-05-16_test_report.md"):
        """Helper to write a temp report with a date-prefixed filename."""
        tmpdir = tempfile.mkdtemp()
        filepath = os.path.join(tmpdir, filename)
        with open(filepath, "w", encoding="utf-8") as f:
            f.write(content)
        return filepath, tmpdir

    def test_basic_parsing(self):
        """Extracts date, status, summary, blockers, next_action from a report."""
        content = (
            "# 2026-05-16 P0 Test Report\n\n"
            "## Files Touched\n\n"
            "| `file1.py` | Created | Test |\n"
            "| `file2.py` | Created | Test |\n"
            "\n"
            "## Summary\n\n"
            "Created a new daily brief sender.\n"
            "With multiple lines of summary text.\n\n"
            "## Blockers\n\n"
            "No blockers.\n\n"
            "## Next Recommended Actions\n\n"
            "1. Run dry-run test.\n"
        )

        filepath, tmpdir = self._write_temp_report(content)
        try:
            brief = parse_report_brief(filepath)
        finally:
            os.unlink(filepath)
            os.rmdir(tmpdir)

        self.assertEqual(brief["date"], "2026-05-16")
        self.assertIn("brief", brief["summary"].lower())

    def test_empty_content(self):
        """Returns defaults for an empty file (filename has no date prefix)."""
        filepath, tmpdir = self._write_temp_report("", filename="test_report.md")
        try:
            brief = parse_report_brief(filepath)
        finally:
            os.unlink(filepath)
            os.rmdir(tmpdir)

        self.assertEqual(brief["date"], "Unknown")
        self.assertNotIn(brief["status"], ["✅ مكتمل", "❌ فشل"])
        self.assertEqual(brief["blockers"], "No blockers.")


class TestFindLatestReport(unittest.TestCase):
    """Test report file discovery (using real filesystem where safe)."""

    @patch("tools.send_daily_brief._project_root", "/nonexistent/path")
    def test_missing_directory(self):
        """Returns error message when reports/daily/ does not exist."""
        path, err = find_latest_report()
        self.assertIsNone(path)
        self.assertIsNotNone(err)
        self.assertGreater(len(str(err)), 0)  # type: ignore[arg-type]

    def test_specific_not_found(self):
        """Returns error when date-targeted report is not found."""
        # Use a far-past date unlikely to have a report
        path, err = find_latest_report(date="1900-01-01")
        self.assertIsNone(path)
        self.assertIsNotNone(err)


class TestDryRunOutput(unittest.TestCase):
    """Test dry-run behavior."""

    def test_dry_run_returns_zero(self):
        """Dry-run with a valid report returns 0 without sending."""
        # Create a fake report
        content = "# Test\n\n"
        filepath, tmpdir = tempfile.mkdtemp(), tempfile.mkdtemp()
        # Override to use a known report dir
        report_dir = os.path.join(tmpdir, "reports", "daily")
        os.makedirs(report_dir)
        report_file = os.path.join(report_dir, "2026-05-16_test.md")
        with open(report_file, "w", encoding="utf-8") as f:
            f.write(content)

        orig_argv = sys.argv
        orig_root = None
        try:
            # We need to patch _project_root on the module
            import tools.send_daily_brief as mod
            orig_root = mod._project_root
            mod._project_root = tmpdir

            sys.argv = ["send_daily_brief.py", "--dry-run"]
            result = main()
        finally:
            sys.argv = orig_argv
            if orig_root:
                import tools.send_daily_brief as mod2
                mod2._project_root = orig_root
            # Cleanup
            import shutil
            shutil.rmtree(tmpdir)

        self.assertEqual(result, 0)


class TestSendBriefBuilderIntegration(unittest.TestCase):
    """Tests for the integration between send_daily_brief.py and daily_brief_builder.py."""

    def test_parse_report_brief_uses_builder(self):
        """When a builder is provided, parse_report_brief delegates to BriefBuilder."""
        cfg = _default_config()
        builder = BriefBuilder(cfg)

        # Create a temp report
        content = (
            "# 2026-05-16 Test Report\n\n"
            "## Branch\n- **Branch:** `zilfit/integration-test`\n\n"
            "Status: ✅ COMPLETED\n\n"
            "## Blockers\nNo blockers.\n"
        )
        tmpdir = tempfile.mkdtemp()
        filepath = os.path.join(tmpdir, "2026-05-16_test.md")
        with open(filepath, "w", encoding="utf-8") as f:
            f.write(content)

        try:
            brief = parse_report_brief(filepath, builder=builder)
        finally:
            os.unlink(filepath)
            os.rmdir(tmpdir)

        # builder.build_from_report uses a richer schema
        self.assertEqual(brief["date"], "2026-05-16")
        self.assertIn("مكتمل", brief["status_text"])
        self.assertEqual(brief["branch"], "zilfit/integration-test")

    def test_parse_report_brief_legacy_fallback(self):
        """Without a builder, parse_report_brief uses legacy ad-hoc parser."""
        content = (
            "# 2026-05-16 Legacy Report\n\n"
            "## Files Touched\n\n"
            "| `a.py` | Created | Test |\n"
            "| `b.py` | Modified | Test |\n\n"
            "## Summary\nLegacy summary text.\n\n"
            "## Blockers\nNone.\n\n"
            "## Next Recommended Actions\nLegacy next action.\n"
        )
        tmpdir = tempfile.mkdtemp()
        filepath = os.path.join(tmpdir, "2026-05-16_legacy.md")
        with open(filepath, "w", encoding="utf-8") as f:
            f.write(content)

        try:
            brief = parse_report_brief(filepath, builder=None)
        finally:
            os.unlink(filepath)
            os.rmdir(tmpdir)

        self.assertEqual(brief["date"], "2026-05-16")
        self.assertEqual(brief["files_touched"], "2")
        self.assertIn("Legacy", brief["summary"])

    def test_format_telegram_brief_uses_builder_template(self):
        """When builder is provided, formatting uses the config template."""
        cfg = _default_config()
        builder = BriefBuilder(cfg)

        brief = {
            "date": "2026-05-16",
            "status_text": "✅ مكتمل",
            "branch": "zilfit/test",
            "commit_count": "3",
            "latest_msg": "test commit",
            "test_status": "PASS",
            "passed": "10",
            "executed": "10",
            "blockers": "لا توجد عوائق",
            "action_text": "Next step",
            "claims_status": "✅ هندسة فقط",
            "prod_readiness": "⚠️ قيد المراجعة",
            "files_count": "5",
        }

        msg = format_telegram_brief(brief, builder=builder)
        # Config template fields present
        self.assertIn("2026-05-16", msg)
        self.assertIn("مكتمل", msg)

    def test_format_telegram_brief_legacy_fallback(self):
        """Without builder, format_telegram_brief uses original formatter."""
        brief = {
            "date": "2026-05-16",
            "status": "✅ مكتمل",
            "files_touched": "3",
            "summary": "Test summary.",
            "risks": "No risks.",
            "blockers": "No blockers.",
            "next_action": "Next step.",
        }
        msg = format_telegram_brief(brief, builder=None)
        self.assertIn("ZILFIT", msg)
        self.assertIn("نبضة يومية", msg)
        self.assertIn("2026-05-16", msg)

    def test_format_telegram_brief_no_sensitive_data(self):
        """Formatted messages never contain sensitive data."""
        cfg = _default_config()
        builder = BriefBuilder(cfg)
        brief = {"date": "2026-05-16", "status_text": "Test"}
        msg = format_telegram_brief(brief, builder=builder)
        self.assertNotIn("token", msg.lower())
        self.assertNotIn("secret", msg.lower())
        # Also test legacy path
        msg2 = format_telegram_brief(brief, builder=None)
        self.assertNotIn("token", msg2.lower())
        self.assertNotIn("secret", msg2.lower())

    def test_dry_run_with_builder_integration(self):
        """main() dry-run loads config, builds brief, and returns 0."""
        import tools.send_daily_brief as mod
        import shutil

        tmpdir = tempfile.mkdtemp()
        report_dir = os.path.join(tmpdir, "reports", "daily")
        os.makedirs(report_dir)
        report_file = os.path.join(report_dir, "2026-05-16_test.md")
        with open(report_file, "w", encoding="utf-8") as f:
            f.write("# Test Report\nStatus: ✅ COMPLETED\n")
        # Also copy config to tmpdir structure
        config_dir = os.path.join(tmpdir, "config")
        os.makedirs(config_dir)
        shutil.copy(CONFIG_PATH, config_dir)

        orig_argv = sys.argv
        orig_root = mod._project_root
        try:
            mod._project_root = tmpdir
            sys.argv = ["send_daily_brief.py", "--dry-run"]
            result = main()
        finally:
            sys.argv = orig_argv
            mod._project_root = orig_root
            shutil.rmtree(tmpdir)

        self.assertEqual(result, 0)


if __name__ == "__main__":
    unittest.main()

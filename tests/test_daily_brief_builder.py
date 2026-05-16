"""Tests for tools/daily_brief_builder.py — config loading, validation, formatting."""

import os
import sys
import tempfile
import unittest
from unittest.mock import patch

# Ensure project root is on the path
_project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _project_root not in sys.path:
    sys.path.insert(0, _project_root)

from tools.daily_brief_builder import (
    BriefBuilder,
    load_config,
    _default_config,
    _coerce,
    CONFIG_PATH,
)


class TestCoerce(unittest.TestCase):
    """Test the YAML value coercion helper."""

    def test_true(self):
        self.assertEqual(_coerce("true"), True)

    def test_false(self):
        self.assertEqual(_coerce("false"), False)

    def test_int(self):
        self.assertEqual(_coerce("42"), 42)

    def test_str(self):
        self.assertEqual(_coerce("hello"), "hello")


class TestLoadConfig(unittest.TestCase):
    """Test config loading."""

    def test_default_config_is_dict(self):
        """Default config returns a usable dict."""
        cfg = _default_config()
        self.assertIsInstance(cfg, dict)
        self.assertIn("brief", cfg)
        self.assertIn("sections", cfg)
        self.assertIn("telegram_template", cfg)

    def test_default_has_max_length(self):
        """Default config includes max_length_chars."""
        cfg = _default_config()
        self.assertEqual(cfg["brief"]["max_length_chars"], 4000)

    def test_real_config_loads(self):
        """Real config file at CONFIG_PATH loads successfully."""
        if os.path.isfile(CONFIG_PATH):
            cfg = load_config(CONFIG_PATH)
            self.assertIsInstance(cfg, dict)
            self.assertIn("telegram_template", cfg)


class TestBriefBuilderValidate(unittest.TestCase):
    """Test brief validation against config schema."""

    def setUp(self):
        self.cfg = _default_config()
        self.builder = BriefBuilder(self.cfg)

    def _good_brief(self):
        return {
            "date": "2026-05-16",
            "status_text": "✅ مكتمل",
            "branch": "zilfit/test",
            "commit_count": "1",
            "latest_msg": "test commit",
            "executed": "10",
            "passed": "10",
            "failed": "0",
            "test_status": "PASS",
            "has_blockers": False,
            "blockers": "لا توجد عوائق",
            "action_text": "Next task",
            "clean": True,
            "claims_status": "✅ هندسة فقط",
            "prod_ready": False,
            "prod_readiness": "⚠️ قيد المراجعة",
            "files_count": "3",
        }

    def test_valid_brief(self):
        """A well-formed brief passes validation."""
        brief = {
            "date": "2026-05-16",
            "next_action": {"action_text": "Do something"},
            "blockers": {"details": "لا توجد عوائق"},
            "claims_safety": {"clean": True},
        }
        # Override required sections for this test
        self.cfg["validation"]["required_sections"] = [
            "date", "next_action", "blockers", "claims_safety",
        ]
        valid, errors = self.builder.validate(brief)
        self.assertTrue(valid, f"Errors: {errors}")

    def test_missing_required_section(self):
        """Missing required section fails validation."""
        self.cfg["validation"]["required_sections"] = ["tests"]
        valid, errors = self.builder.validate({"date": "2026-05-16"})
        self.assertFalse(valid)
        self.assertTrue(any("tests" in e for e in errors))

    def test_invalid_date_format(self):
        """Date not matching YYYY-MM-DD fails validation."""
        valid, errors = self.builder.validate({"date": "16-05-2026"})
        self.assertFalse(valid)
        self.assertTrue(any("YYYY-MM-DD" in e for e in errors))

    def test_claims_not_clean(self):
        """claims_safety.clean=False fails validation."""
        brief = {
            "date": "2026-05-16",
            "claims_safety": {"clean": False},
        }
        valid, errors = self.builder.validate(brief)
        self.assertFalse(valid)
        self.assertTrue(any("claims_safety" in e for e in errors))

    def test_empty_next_action(self):
        """Empty next_action fails validation."""
        brief = {
            "date": "2026-05-16",
            "next_action": {"action_text": "   "},
        }
        valid, errors = self.builder.validate(brief)
        self.assertFalse(valid)
        self.assertTrue(any("next_action" in e for e in errors))

    def test_claims_clean_true(self):
        """Claims safety with clean=True passes."""
        brief = {
            "date": "2026-05-16",
            "claims_safety": {"clean": True},
        }
        valid, errors = self.builder.validate(brief)
        # Should not fail on claims check
        claims_errors = [e for e in errors if "claims_safety" in e]
        self.assertEqual(len(claims_errors), 0)


class TestBriefBuilderFormat(unittest.TestCase):
    """Test Telegram message formatting."""

    def setUp(self):
        self.cfg = _default_config()
        self.builder = BriefBuilder(self.cfg)

    def test_basic_formatting(self):
        """All fields are substituted into the template."""
        brief = {
            "date": "2026-05-16",
            "status_text": "✅ مكتمل",
            "branch": "zilfit/test",
            "commit_count": "5",
            "latest_msg": "fix something",
            "test_status": "PASS",
            "passed": "10",
            "executed": "10",
            "blockers": "لا توجد عوائق",
            "action_text": "Next step",
            "claims_status": "✅ هندسة فقط",
            "prod_readiness": "⚠️ قيد المراجعة",
            "files_count": "3",
        }
        msg = self.builder.format(brief)
        self.assertIn("2026-05-16", msg)
        self.assertIn("مكتمل", msg)

    def test_no_sensitive_data(self):
        """Formatted message does not leak secrets."""
        brief = {"date": "2026-05-16"}
        msg = self.builder.format(brief)
        self.assertNotIn("token", msg.lower())
        self.assertNotIn("secret", msg.lower())
        self.assertNotIn("password", msg.lower())

    def test_defaults_for_missing_fields(self):
        """Missing fields get safe defaults."""
        brief = {}
        msg = self.builder.format(brief)
        self.assertIn("Unknown", msg)


class TestBuildFromReport(unittest.TestCase):
    """Test building a brief from a report .md file."""

    def setUp(self):
        self.cfg = _default_config()
        self.builder = BriefBuilder(self.cfg)

    def test_parses_date_from_filename(self):
        """Extracts date from filename like 2026-05-16_report.md."""
        content = "# Some Report\n\nNo special fields."
        path = self._write_temp(content, "2026-05-16_test_report.md")
        try:
            brief = self.builder.build_from_report(path)
        finally:
            os.unlink(path)
        self.assertEqual(brief["date"], "2026-05-16")

    def test_parses_branch(self):
        """Extracts branch name from report content."""
        content = "## Branch\n- **Branch:** `zilfit/test-branch`\n"
        path = self._write_temp(content, "2026-05-16_test.md")
        try:
            brief = self.builder.build_from_report(path)
        finally:
            os.unlink(path)
        self.assertEqual(brief["branch"], "zilfit/test-branch")

    def test_parses_completed_status(self):
        """Detects COMPLETED status."""
        content = "# Report\nStatus: ✅ COMPLETED\n"
        path = self._write_temp(content, "2026-05-16_test.md")
        try:
            brief = self.builder.build_from_report(path)
        finally:
            os.unlink(path)
        self.assertIn("مكتمل", brief["status_text"])

    def test_missing_file(self):
        """Returns safe defaults for missing file."""
        brief = self.builder.build_from_report("/nonexistent/file.md")
        self.assertIn("فشل قراءة", brief["latest_msg"])

    def _write_temp(self, content, filename):
        tmpdir = tempfile.mkdtemp()
        path = os.path.join(tmpdir, filename)
        with open(path, "w", encoding="utf-8") as f:
            f.write(content)
        return path


class TestValidateOnly(unittest.TestCase):
    """Test --validate-only CLI behavior."""

    def test_validate_only_returns_zero_for_default(self):
        """validate-only with default config returns 0 (valid)."""
        from tools.daily_brief_builder import main

        orig_argv = sys.argv
        try:
            sys.argv = ["daily_brief_builder.py", "--validate-only"]
            result = main()
        finally:
            sys.argv = orig_argv
        self.assertEqual(result, 0)


if __name__ == "__main__":
    unittest.main()

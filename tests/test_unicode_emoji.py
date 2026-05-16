"""Tests for unicode/emoji rendering in daily brief output.

Ensures that the Telegram dry-run output contains real emoji characters
and Arabic text, NOT literal escape artifacts.
"""

import os
import sys
import tempfile
import shutil
import unittest
from io import StringIO
from unittest.mock import patch

_project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _project_root not in sys.path:
    sys.path.insert(0, _project_root)

from tools.send_daily_brief import format_telegram_brief, main
from tools.daily_brief_builder import BriefBuilder, _default_config, CONFIG_PATH


# The problematic patterns that must NOT appear in output
BACKSLASH_UPPER_U = chr(92) + 'U0001'
BACKSLASH_LOWER_U = chr(92) + 'u0001'
DOLLAR_BACKSLASH_U = dollar_bs = chr(36) + chr(92) + 'U'
DOLLAR_U_PATTERNS = [
    chr(92) + 'U0001',  # \U0001 (literal backslash + capital U)
    chr(92) + 'u0001',  # \u0001 (literal backslash + lowercase u)
    chr(36) + chr(92) + 'U',  # $\U (dollar + backslash + U)
]


class TestUnicodeNoEscapeArtifacts(unittest.TestCase):
    """Ensure emoji and Arabic render correctly, no escape artifacts."""

    def assert_no_escape_artifacts(self, text):
        """Assert text does NOT contain literal escape artifacts."""
        for pat in DOLLAR_U_PATTERNS:
            self.assertNotIn(
                pat, text,
                f"Found literal escape pattern '{pat}' in output"
            )

    def assert_contains_real_emoji(self, text):
        """Assert text contains actual emoji characters."""
        known_emojis = ['\U0001f4cb', '\U0001f4ca', '\U0001f4dd',
                        '\U0001f9ea', '\U0001f6a7', '\U0001f7e2',
                        '\U0001f6e1\ufe0f', '\U0001f512', '\U0001f4c2']
        found = [e for e in known_emojis if e in text]
        self.assertTrue(
            len(found) > 0,
            f"No real emoji found in text. First 200 chars: {text[:200]}"
        )

    def test_config_template_no_escapes(self):
        """The YAML config template contains no escape artifacts."""
        from tools.daily_brief_builder import load_config

        cfg = load_config()
        template = cfg.get("telegram_template", "")
        self.assert_no_escape_artifacts(template)
        # Must contain real emoji
        self.assert_contains_real_emoji(template)
        # Must have Arabic
        self.assertIn('\u0646\u0628\u0636\u0629 \u064a\u0648\u0645\u064a\u0629', template)

    def test_legacy_formatter_no_escapes(self):
        """Legacy formatter output has no escape artifacts."""
        brief = {
            "date": "2026-05-16",
            "status": '\u2705 \u0645\u0643\u062a\u0645\u0644',
            "files_touched": "3",
            "summary": "Test summary.",
            "risks": "No risks.",
            "blockers": "No blockers.",
            "next_action": "Next step.",
        }
        msg = format_telegram_brief(brief, builder=None)
        self.assert_no_escape_artifacts(msg)
        self.assert_contains_real_emoji(msg)

    def test_builder_formatter_no_escapes(self):
        """Builder formatter output has no escape artifacts."""
        from tools.daily_brief_builder import load_config
        cfg = load_config(CONFIG_PATH)
        builder = BriefBuilder(cfg)
        brief = {
            "date": "2026-05-16",
            "status_text": '\u2705 \u0645\u0643\u062a\u0645\u0644',
            "branch": "zilfit/test",
            "commit_count": "3",
            "latest_msg": "test commit",
            "test_status": "PASS",
            "passed": "10",
            "executed": "10",
            "blockers": '\u0644\u0627 \u062a\u0648\u062c\u062f \u0639\u0648\u0627\u0626\u0642',
            "action_text": "Next step",
            "claims_status": '\u2705 \u0647\u0646\u062f\u0633\u0629 \u0641\u0642\u0637',
            "prod_readiness": '\u26a0\ufe0f \u0642\u064a\u062f \u0627\u0644\u0645\u0631\u0627\u062c\u0639\u0629',
            "files_count": "5",
        }
        msg = format_telegram_brief(brief, builder=builder)
        self.assert_no_escape_artifacts(msg)
        self.assert_contains_real_emoji(msg)

    def test_dry_run_output_no_escapes(self):
        """main() dry-run output has no escape artifacts and real emoji/Arabic."""
        import tools.send_daily_brief as mod

        tmpdir = tempfile.mkdtemp()
        report_dir = os.path.join(tmpdir, "reports", "daily")
        os.makedirs(report_dir)
        report_file = os.path.join(report_dir, "2026-05-16_test.md")
        with open(report_file, "w", encoding="utf-8") as f:
            f.write("# Test Report\nStatus: \u2705 COMPLETED\n")
        config_dir = os.path.join(tmpdir, "config")
        os.makedirs(config_dir)
        shutil.copy(CONFIG_PATH, config_dir)

        orig_argv = sys.argv
        orig_root = mod._project_root
        captured = StringIO()
        try:
            mod._project_root = tmpdir
            sys.argv = ["send_daily_brief.py", "--dry-run"]
            with patch("sys.stdout", captured):
                result = main()
        finally:
            sys.argv = orig_argv
            mod._project_root = orig_root
            shutil.rmtree(tmpdir)

        self.assertEqual(result, 0)
        output = captured.getvalue()
        self.assert_no_escape_artifacts(output)
        self.assert_contains_real_emoji(output)
        # Must contain Arabic text
        self.assertIn('\u0646\u0628\u0636\u0629 \u064a\u0648\u0645\u064a\u0629', output)
        self.assertIn('\u0627\u0644\u0641\u0631\u0639', output)

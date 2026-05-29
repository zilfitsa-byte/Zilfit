"""Tests for tools/telegram_inbox.py — mock-only, no network calls."""

import json
import os
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch, MagicMock

# Ensure project root is on the path
_project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _project_root not in sys.path:
    sys.path.insert(0, _project_root)

from tools.telegram_inbox import (
    get_bot_token,
    load_offset,
    save_offset,
    extract_safe_text,
    parse_message,
    process_updates,
    compute_next_offset,
    format_inbox_report,
    ensure_inbox_dir,
    write_report,
    run_inbox_poll,
)


# ── Common test fixtures ───────────────────────────────────────────────────────

def _make_update(update_id, message):
    """Helper to create a Telegram update dict with a nested message."""
    return {"update_id": update_id, "message": message}


def _make_message(message_id, chat_id, user_id, text=None, chat_type="private",
                  first_name="TestUser", date=1716000000, caption=None, photo=None):
    """Helper to create a message dict."""
    msg = {
        "message_id": message_id,
        "chat": {"id": chat_id, "type": chat_type},
        "from": {"id": user_id, "first_name": first_name},
        "date": date,
    }
    if text is not None:
        msg["text"] = text
    if caption is not None:
        msg["caption"] = caption
    if photo is not None:
        msg["photo"] = photo
    return msg


# ── Token handling tests ──────────────────────────────────────────────────────

class TestGetBotToken(unittest.TestCase):
    """Test TELEGRAM_BOT_TOKEN environment reading."""

    def test_returns_token_from_env(self):
        with patch.dict(os.environ, {"TELEGRAM_BOT_TOKEN": "test-token-123"}):
            self.assertEqual(get_bot_token(), "test-token-123")

    def test_raises_when_not_set(self):
        # Save current value, then remove
        old = os.environ.pop("TELEGRAM_BOT_TOKEN", None)
        try:
            with self.assertRaises(EnvironmentError):
                get_bot_token()
        finally:
            if old is not None:
                os.environ["TELEGRAM_BOT_TOKEN"] = old

    def test_strips_whitespace(self):
        with patch.dict(os.environ, {"TELEGRAM_BOT_TOKEN": "  my-token  "}):
            self.assertEqual(get_bot_token(), "my-token")


# ── Offset persistence tests ──────────────────────────────────────────────────

class TestOffsetPersistence(unittest.TestCase):
    """Test loading and saving offset values."""

    def test_load_missing_offset_returns_zero(self):
        self.assertEqual(load_offset(Path("/nonexistent/path/.last_offset")), 0)

    def test_load_valid_offset(self):
        with tempfile.NamedTemporaryFile(mode="w", suffix=".offset", delete=False) as f:
            f.write("42")
            f.flush()
            self.assertEqual(load_offset(Path(f.name)), 42)

    def test_load_corrupt_offset_returns_zero(self):
        with tempfile.NamedTemporaryFile(mode="w", suffix=".offset", delete=False) as f:
            f.write("not-a-number")
            f.flush()
            self.assertEqual(load_offset(Path(f.name)), 0)

    def test_save_and_reload_offset(self):
        with tempfile.NamedTemporaryFile(mode="w", suffix=".offset", delete=False) as f:
            f.flush()
            path = Path(f.name)
            save_offset(99, path)
            self.assertEqual(load_offset(path), 99)


# ── Message extraction tests ──────────────────────────────────────────────────

class TestExtractSafeText(unittest.TestCase):
    """Test extracting text safely from message dicts."""

    def test_direct_text(self):
        msg = {"text": "Hello world"}
        self.assertEqual(extract_safe_text(msg), "Hello world")

    def test_caption(self):
        msg = {"photo": [{"file_id": "abc"}], "caption": "A nice photo"}
        self.assertEqual(extract_safe_text(msg), "A nice photo")

    def test_text_over_caption(self):
        msg = {"text": "Text", "caption": "Caption"}
        self.assertEqual(extract_safe_text(msg), "Text")

    def test_photo_without_caption(self):
        msg = {"photo": [{"file_id": "abc"}]}
        self.assertEqual(extract_safe_text(msg), "[non-text media]")

    def test_empty_text(self):
        msg = {"text": "   "}
        self.assertIsNone(extract_safe_text(msg))

    def test_unknown_media(self):
        msg = {"sticker": {"emoji": "👍"}}
        self.assertEqual(extract_safe_text(msg), "[non-text media]")

    def test_empty_message(self):
        msg = {}
        self.assertIsNone(extract_safe_text(msg))


# ── Message parse tests ────────────────────────────────────────────────────────

class TestParseMessage(unittest.TestCase):
    """Test parsing message dicts into sanitized output."""

    def test_parses_required_fields(self):
        msg = _make_message(1, 100, 200, text="Test")
        result = parse_message(msg)
        self.assertIsNotNone(result)
        self.assertEqual(result["message_id"], 1)
        self.assertEqual(result["chat_id"], 100)
        self.assertEqual(result["user_id"], 200)
        self.assertEqual(result["text"], "Test")
        self.assertEqual(result["chat_type"], "private")
        self.assertEqual(result["user_name"], "TestUser")

    def test_returns_none_without_message_id(self):
        msg = {"chat": {"id": 100}, "text": "No msg_id"}
        self.assertIsNone(parse_message(msg))

    def test_returns_none_without_chat_id(self):
        msg = {"message_id": 1, "text": "No chat"}
        self.assertIsNone(parse_message(msg))

    def test_handles_non_text_message(self):
        msg = _make_message(5, 100, 200, photo=[{"file_id": "abc"}])
        result = parse_message(msg)
        self.assertIsNotNone(result)
        self.assertEqual(result["text"], "[non-text media]")

    def test_handles_unknown_user_name(self):
        msg = {
            "message_id": 1,
            "chat": {"id": 100},
            "from": {"id": 200},
            "date": 1716000000,
            "text": "Hello",
        }
        result = parse_message(msg)
        self.assertEqual(result["user_name"], "unknown")


# ── Process updates tests ─────────────────────────────────────────────────────

class TestProcessUpdates(unittest.TestCase):
    """Test processing lists of raw Telegram update dicts."""

    def test_processes_single_text_message(self):
        updates = [_make_update(1, _make_message(1, 100, 200, text="Hello"))]
        results = process_updates(updates)
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0]["text"], "Hello")
        self.assertEqual(results[0]["update_id"], 1)

    def test_processes_mixed_types(self):
        updates = [
            _make_update(1, _make_message(1, 100, 200, text="Hello")),
            _make_update(2, _make_message(2, 100, 200, photo=[{"file_id": "abc"}])),
        ]
        results = process_updates(updates)
        self.assertEqual(len(results), 2)
        self.assertEqual(results[0]["text"], "Hello")
        self.assertEqual(results[1]["text"], "[non-text media]")

    def test_skips_updates_without_message(self):
        updates = [
            {"update_id": 1, "edited_message": {"message_id": 5}},
        ]
        results = process_updates(updates)
        self.assertEqual(len(results), 0)

    def test_empty_updates_list(self):
        self.assertEqual(process_updates([]), [])


# ── Offset computation tests ───────────────────────────────────────────────────

class TestComputeNextOffset(unittest.TestCase):
    """Test computing the next update offset."""

    def test_empty_messages_preserves_offset(self):
        self.assertEqual(compute_next_offset([], 10), 10)

    def test_advances_from_last_update_id(self):
        messages = [
            {"update_id": 1},
            {"update_id": 3},
            {"update_id": 2},
        ]
        self.assertEqual(compute_next_offset(messages, 0), 4)

    def test_does_not_go_backwards(self):
        messages = [{"update_id": 1}]
        self.assertEqual(compute_next_offset(messages, 10), 10)

    def test_single_message(self):
        messages = [{"update_id": 5}]
        self.assertEqual(compute_next_offset(messages, 0), 6)


# ── Report formatting tests ───────────────────────────────────────────────────

class TestFormatInboxReport(unittest.TestCase):
    """Test report text generation."""

    def test_report_has_required_sections(self):
        report = format_inbox_report(
            messages=[],
            poll_timestamp="2026-05-16 15:00:00 UTC",
            total_updates_raw=0,
            current_offset=0,
            next_offset=0,
            token_masked="[REDACTED]",
        )
        self.assertIn("ZILFIT TELEGRAM INBOX REPORT", report)
        self.assertIn("SAFETY STATUS", report)
        self.assertIn("BLOCKERS", report)
        self.assertIn("NEXT ACTION", report)
        self.assertIn("CONFIRMED", report)

    def test_report_with_messages(self):
        messages = [{
            "message_id": 1, "chat_id": 100, "chat_type": "private",
            "user_id": 200, "user_name": "Alice", "date": 1716000000,
            "text": "Hello ZILFIT",
        }]
        report = format_inbox_report(
            messages=messages,
            poll_timestamp="2026-05-16 15:00:00 UTC",
            total_updates_raw=1,
            current_offset=0,
            next_offset=2,
            token_masked="abc123[REDACTED]",
        )
        self.assertIn("INBOX MESSAGES", report)
        self.assertIn("Hello ZILFIT", report)
        self.assertIn("Alice", report)

    def test_masked_token_appearance(self):
        report = format_inbox_report(
            messages=[],
            poll_timestamp="now",
            total_updates_raw=0,
            current_offset=0,
            next_offset=0,
            token_masked="abc123[REDACTED]",
        )
        self.assertIn("abc123[REDACTED]", report)

    def test_safety_status_confirmed(self):
        """No commands executed flag is present."""
        report = format_inbox_report(
            messages=[], poll_timestamp="now", total_updates_raw=0,
            current_offset=0, next_offset=0, token_masked="[REDACTED]",
        )
        self.assertIn("No commands executed: CONFIRMED", report)
        self.assertIn("No messages sent back: CONFIRMED", report)


# ── Inbox directory tests ──────────────────────────────────────────────────────

class TestEnsureInboxDir(unittest.TestCase):
    """Test inbox directory creation."""

    def test_creates_directory(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            d = ensure_inbox_dir(Path(tmpdir) / "nested" / "inbox")
            self.assertTrue(d.is_dir())


# ── Write report tests ────────────────────────────────────────────────────────

class TestWriteReport(unittest.TestCase):
    """Test writing reports to files."""

    def test_writes_file_to_inbox_dir(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            report_dir = Path(tmpdir) / "inbox"
            path = write_report("Test report content", report_dir=report_dir)
            self.assertTrue(path.exists())
            self.assertEqual(path.read_text(), "Test report content")

    def test_custom_filename(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            report_dir = Path(tmpdir) / "inbox"
            path = write_report("Content", report_dir=report_dir, filename="custom.md")
            self.assertEqual(path.name, "custom.md")


# ── run_inbox_poll integration tests (dry_run, mocked) ────────────────────────

class TestRunInboxPoll(unittest.TestCase):
    """End-to-end integration in dry_run mode (no network)."""

    def test_dry_run_no_messages(self):
        result = run_inbox_poll(
            token="test-token-123",
            offset=0,
            dry_run=True,
            mock_raw_updates=[],
        )
        self.assertEqual(result["total_updates_raw"], 0)
        self.assertEqual(len(result["messages"]), 0)
        self.assertIsNotNone(result["report_text"])

    def test_dry_run_with_messages(self):
        raw = [
            _make_update(1, _make_message(1, 100, 200, text="Hello")),
            _make_update(2, _make_message(2, 100, 200, text="World")),
        ]
        result = run_inbox_poll(
            token="test-token-123",
            offset=0,
            dry_run=True,
            mock_raw_updates=raw,
        )
        self.assertEqual(result["total_updates_raw"], 2)
        self.assertEqual(len(result["messages"]), 2)
        self.assertEqual(result["next_offset"], 3)
        self.assertIn("Hello", result["report_text"])
        self.assertIn("World", result["report_text"])

    def test_dry_run_preserves_offset(self):
        """dry_run should NOT persist offset to disk."""
        with tempfile.TemporaryDirectory() as tmpdir:
            offset_file = Path(tmpdir) / ".last_offset"
            # Set initial offset to 10
            result = run_inbox_poll(
                token="test-token-123",
                offset=10,
                dry_run=True,
                mock_raw_updates=[_make_update(5, _make_message(1, 100, 200, text="Hi"))],
            )
            # In dry_run, offset should NOT be saved to file
            self.assertFalse(offset_file.exists())
            self.assertEqual(result["current_offset"], 10)
            # next_offset computed correctly
            self.assertEqual(result["next_offset"], 10)

    def test_dry_run_with_arabic_text(self):
        """Arabic text passes through safely."""
        raw = [
            _make_update(1, _make_message(1, 100, 200, text="مرحبا زلفيت")),
        ]
        result = run_inbox_poll(
            token="test-token-123",
            offset=0,
            dry_run=True,
            mock_raw_updates=raw,
        )
        self.assertEqual(len(result["messages"]), 1)
        self.assertEqual(result["messages"][0]["text"], "مرحبا زلفيت")
        self.assertIn("مرحبا زلفيت", result["report_text"])

    def test_token_masking_in_report(self):
        """Long token is masked in the report."""
        result = run_inbox_poll(
            token="123456789:ABCdef123456",
            offset=0,
            dry_run=True,
            mock_raw_updates=[],
        )
        self.assertIn("123456[REDACTED]", result["report_text"])

    def test_short_token_masking(self):
        """Short token is fully redacted."""
        result = run_inbox_poll(
            token="ab",
            offset=0,
            dry_run=True,
            mock_raw_updates=[],
        )
        self.assertIn("[REDACTED]", result["report_text"])

    def test_mixed_chat_types(self):
        """Handles group, supergroup, and channel messages."""
        raw = [
            _make_update(1, _make_message(1, 100, 200, text="DM", chat_type="private")),
            _make_update(2, _make_message(2, -100, 200, text="Group", chat_type="group")),
            _make_update(3, _make_message(3, -10001, 200, text="Supergroup", chat_type="supergroup")),
        ]
        result = run_inbox_poll(
            token="test-token",
            offset=0,
            dry_run=True,
            mock_raw_updates=raw,
        )
        self.assertEqual(len(result["messages"]), 3)
        self.assertEqual(result["messages"][0]["chat_type"], "private")
        self.assertEqual(result["messages"][1]["chat_type"], "group")
        self.assertEqual(result["messages"][2]["chat_type"], "supergroup")

    def test_caption_on_photo_message(self):
        """Photo with caption is extracted as text."""
        msg = {
            "message_id": 1,
            "chat": {"id": 100, "type": "private"},
            "from": {"id": 200, "first_name": "User"},
            "date": 1716000000,
            "photo": [{"file_id": "AgACAgIA"}],
            "caption": "Send me an update",
        }
        raw = [_make_update(1, msg)]
        result = run_inbox_poll(
            token="test-token",
            offset=0,
            dry_run=True,
            mock_raw_updates=raw,
        )
        self.assertEqual(len(result["messages"]), 1)
        self.assertEqual(result["messages"][0]["text"], "Send me an update")


# ── Security / safety tests ───────────────────────────────────────────────────

class TestSecurityGuards(unittest.TestCase):
    """Verify the poller does not execute, store, or leak credentials."""

    def test_get_bot_token_does_not_store_file(self):
        """get_bot_token reads from env, never writes to disk."""
        with patch.dict(os.environ, {"TELEGRAM_BOT_TOKEN": "secret-token"}):
            token = get_bot_token()
            self.assertEqual(token, "secret-token")
            # No file should have been created
            self.assertFalse(Path(".last_offset").exists())

    def test_report_does_not_contain_full_token(self):
        """Inbox report masks the full token."""
        long_token = "123456789:ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnop"
        result = run_inbox_poll(
            token=long_token,
            offset=0,
            dry_run=True,
            mock_raw_updates=[],
        )
        # Full token must not appear in the report
        self.assertNotIn(long_token, result["report_text"])
        self.assertNotIn("ABCDEF", result["report_text"])
        # Only the first 6 chars should be visible
        self.assertIn("123456", result["report_text"])

    def test_no_command_execution_in_parse(self):
        """parse_message does not import subprocess or os.system."""
        import tools.telegram_inbox as mod
        source = open(mod.__file__).read()
        self.assertNotIn("os.system", source)
        self.assertNotIn("subprocess.call", source)
        self.assertNotIn("os.popen", source)
        self.assertNotIn("eval(", source)
        self.assertNotIn("exec(", source)


if __name__ == "__main__":
    unittest.main()

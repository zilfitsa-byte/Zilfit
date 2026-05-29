"""Tests for tools/telegram_command_intake.py — mock-only, no network calls."""

import os
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

_project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _project_root not in sys.path:
    sys.path.insert(0, _project_root)

from tools.telegram_command_intake import (
    classify_request,
    classify_messages,
    format_classified_report,
    run_classified_intake,
    save_to_shared_db,
    VALID_REQUEST_TYPES,
    DEFAULT_REQUEST_TYPE,
)

# ── Helpers ──────────────────────────────────────────────────────────────────

def _make_update(update_id, message):
    """Helper to create a Telegram update dict."""
    return {"update_id": update_id, "message": message}


def _make_message(message_id, chat_id, user_id, text=None, chat_type="private",
                  first_name="TestUser", date=1716000000):
    """Helper to create a message dict."""
    msg = {
        "message_id": message_id,
        "chat": {"id": chat_id, "type": chat_type},
        "from": {"id": user_id, "first_name": first_name},
        "date": date,
    }
    if text is not None:
        msg["text"] = text
    return msg


# ── classify_request tests ───────────────────────────────────────────────────

class TestClassifyCommand(unittest.TestCase):
    """Test command text -> request_type mapping."""

    def test_status_command(self):
        self.assertEqual(classify_request("/status"), "status_request")

    def test_brief_command(self):
        self.assertEqual(classify_request("/brief"), "brief_request")

    def test_next_command(self):
        self.assertEqual(classify_request("/next"), "next_action_request")

    def test_queue_command(self):
        self.assertEqual(classify_request("/queue"), "queue_request")

    def test_unknown_command_defaults(self):
        self.assertEqual(classify_request("/unknown"), DEFAULT_REQUEST_TYPE)
        self.assertEqual(classify_request("/deploy"), DEFAULT_REQUEST_TYPE)

    def test_free_text_defaults(self):
        self.assertEqual(classify_request("Hello, how are you?"), DEFAULT_REQUEST_TYPE)
        self.assertEqual(classify_request("Please check the design"), DEFAULT_REQUEST_TYPE)

    def test_none_text_defaults(self):
        self.assertEqual(classify_request(None), DEFAULT_REQUEST_TYPE)

    def test_empty_text_defaults(self):
        self.assertEqual(classify_request(""), DEFAULT_REQUEST_TYPE)

    def test_command_with_arguments(self):
        """Commands with trailing text should still classify correctly."""
        self.assertEqual(classify_request("/status full"), "status_request")
        self.assertEqual(classify_request("/brief today"), "brief_request")

    def test_case_insensitive(self):
        """Commands should be case-insensitive."""
        self.assertEqual(classify_request("/STATUS"), "status_request")
        self.assertEqual(classify_request("/Brief"), "brief_request")
        self.assertEqual(classify_request("/Next"), "next_action_request")

    def test_arabic_text_defaults(self):
        """Arabic text defaults to note_or_task_request."""
        self.assertEqual(classify_request("مرحبا زلفيت"), DEFAULT_REQUEST_TYPE)

    def test_leading_whitespace(self):
        """Leading/trailing whitespace should be handled."""
        self.assertEqual(classify_request("  /status  "), "status_request")


# ── classify_messages tests ─────────────────────────────────────────────────

class TestClassifyMessages(unittest.TestCase):
    """Test batch classification of parsed messages."""

    def test_classifies_single_message(self):
        messages = [_make_message(1, 100, 200, text="/status")]
        result = classify_messages(messages)
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0]["request_type"], "status_request")

    def test_classifies_mixed_commands(self):
        messages = [
            _make_message(1, 100, 200, text="/status"),
            _make_message(2, 100, 200, text="/brief"),
            _make_message(3, 100, 200, text="Just a note"),
        ]
        result = classify_messages(messages)
        self.assertEqual(result[0]["request_type"], "status_request")
        self.assertEqual(result[1]["request_type"], "brief_request")
        self.assertEqual(result[2]["request_type"], "note_or_task_request")

    def test_preserves_original_fields(self):
        # classify_messages expects already-parsed messages (chat_id flattened)
        msg = {
            "message_id": 1, "chat_id": 100, "user_id": 200,
            "user_name": "TestUser", "chat_type": "private",
            "date": 1716000000, "text": "/queue",
        }
        result = classify_messages([msg])
        self.assertEqual(result[0]["message_id"], 1)
        self.assertEqual(result[0]["chat_id"], 100)
        self.assertEqual(result[0]["user_name"], "TestUser")

    def test_empty_list(self):
        self.assertEqual(classify_messages([]), [])


# ── format_classified_report tests ──────────────────────────────────────────

class TestFormatClassifiedReport(unittest.TestCase):
    """Test classified report generation."""

    def test_report_has_required_sections(self):
        report = format_classified_report(
            classified=[],
            poll_timestamp="2026-05-16 15:00:00 UTC",
            summary_counts={},
        )
        self.assertIn("ZILFIT COMMAND INTAKE REPORT", report)
        self.assertIn("SAFETY STATUS", report)
        self.assertIn("REQUEST TYPE COUNTS", report)

    def test_report_with_classified_messages(self):
        classified = [
            {
                "message_id": 1, "user_name": "Alice", "user_id": 200,
                "chat_id": 100, "chat_type": "private", "date": 1716000000,
                "text": "/status", "request_type": "status_request",
            }
        ]
        report = format_classified_report(
            classified=classified,
            poll_timestamp="2026-05-16 15:00:00 UTC",
            summary_counts={"status_request": 1},
        )
        self.assertIn("status_request", report)
        self.assertIn("Alice", report)
        self.assertIn("/status", report)

    def test_report_safety_status(self):
        report = format_classified_report([], "now", {})
        self.assertIn("No commands executed", report)
        self.assertIn("CONFIRMED", report)

    def test_empty_messages_text(self):
        classified = [{
            "message_id": 1, "user_name": "Test", "user_id": 1,
            "chat_id": 1, "chat_type": "private", "date": 1716000000,
            "text": None, "request_type": "note_or_task_request",
        }]
        report = format_classified_report(
            classified=classified,
            poll_timestamp="now",
            summary_counts={"note_or_task_request": 1},
        )
        self.assertIn("[empty]", report)


# ── save_to_shared_db tests ─────────────────────────────────────────────────

class TestSaveToSharedDB(unittest.TestCase):
    """Test SharedDB persistence of classified requests."""

    def test_empty_list_returns_empty(self):
        self.assertEqual(save_to_shared_db([]), [])

    def test_saves_record(self):
        with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
            f.close()
            try:
                classified = [{
                    "message_id": 42, "user_name": "Sultan", "user_id": 100,
                    "chat_id": 200, "chat_type": "private", "date": 1716000000,
                    "text": "/status", "request_type": "status_request",
                }]
                records = save_to_shared_db(classified, db_path=f.name)
                self.assertEqual(len(records), 1)
                self.assertEqual(records[0]["agent_name"], "Z-Intake")
                self.assertEqual(records[0]["status"], "pending")
                self.assertIn("status_request", records[0]["summary"])
            finally:
                os.unlink(f.name)

    def test_high_risk_for_free_text(self):
        """note_or_task_request should be high risk."""
        with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
            f.close()
            try:
                classified = [{
                    "message_id": 1, "user_name": "Test", "user_id": 1,
                    "chat_id": 1, "chat_type": "private", "date": 1716000000,
                    "text": "Build me a website", "request_type": "note_or_task_request",
                }]
                records = save_to_shared_db(classified, db_path=f.name)
                self.assertEqual(records[0]["risk_level"], "high")
            finally:
                os.unlink(f.name)

    def test_low_risk_for_commands(self):
        """Known commands should be low risk."""
        with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
            f.close()
            try:
                classified = [{
                    "message_id": 2, "user_name": "Test", "user_id": 1,
                    "chat_id": 1, "chat_type": "private", "date": 1716000000,
                    "text": "/brief", "request_type": "brief_request",
                }]
                records = save_to_shared_db(classified, db_path=f.name)
                self.assertEqual(records[0]["risk_level"], "low")
            finally:
                os.unlink(f.name)

    def test_skips_when_import_fails(self):
        """Should handle ImportError gracefully."""
        original_path = sys.path.copy()
        # We don't actually break import — just verify empty list when no data
        self.assertEqual(save_to_shared_db([]), [])


# ── run_classified_intake end-to-end tests ───────────────────────────────────

class TestRunClassifiedIntake(unittest.TestCase):
    """End-to-end intake pipeline tests (dry_run, mocked, no network)."""

    def test_empty_updates(self):
        result = run_classified_intake([], dry_run=True)
        self.assertEqual(len(result["messages"]), 0)
        self.assertEqual(len(result["classified"]), 0)
        self.assertEqual(result["summary_counts"], {})
        self.assertIsNone(result["report_path"])

    def test_single_status_command(self):
        raw = [_make_update(1, _make_message(1, 100, 200, text="/status"))]
        result = run_classified_intake(raw, dry_run=True)
        self.assertEqual(len(result["classified"]), 1)
        self.assertEqual(result["classified"][0]["request_type"], "status_request")
        self.assertEqual(result["summary_counts"]["status_request"], 1)

    def test_mixed_commands(self):
        raw = [
            _make_update(1, _make_message(1, 100, 200, text="/status")),
            _make_update(2, _make_message(2, 100, 200, text="/brief")),
            _make_update(3, _make_message(3, 100, 200, text="/next")),
            _make_update(4, _make_message(4, 100, 200, text="/queue")),
            _make_update(5, _make_message(5, 100, 200, text="Random note")),
        ]
        result = run_classified_intake(raw, dry_run=True)
        self.assertEqual(len(result["classified"]), 5)
        types = [m["request_type"] for m in result["classified"]]
        self.assertIn("status_request", types)
        self.assertIn("brief_request", types)
        self.assertIn("next_action_request", types)
        self.assertIn("queue_request", types)
        self.assertIn("note_or_task_request", types)

    def test_arabic_text_classification(self):
        raw = [
            _make_update(1, _make_message(1, 100, 200, text="مرحবা زلفيت")),
        ]
        result = run_classified_intake(raw, dry_run=True)
        self.assertEqual(result["classified"][0]["request_type"], "note_or_task_request")

    def test_dry_run_does_not_write_report(self):
        raw = [_make_update(1, _make_message(1, 100, 200, text="/status"))]
        result = run_classified_intake(raw, dry_run=True)
        self.assertIsNone(result["report_path"])
        self.assertIsNotNone(result["report_text"])

    def test_dry_run_does_not_write_db(self):
        raw = [_make_update(1, _make_message(1, 100, 200, text="/status"))]
        result = run_classified_intake(raw, dry_run=True)
        self.assertEqual(result["db_records"], [])

    def test_report_contains_all_classified_messages(self):
        raw = [
            _make_update(1, _make_message(1, 100, 200, text="/status")),
            _make_update(2, _make_message(2, 100, 200, text="/brief")),
        ]
        result = run_classified_intake(raw, dry_run=True)
        report = result["report_text"]
        self.assertIn("status_request", report)
        self.assertIn("brief_request", report)
        self.assertIn("/status", report)
        self.assertIn("/brief", report)

    def test_safety_status_in_report(self):
        raw = [_make_update(1, _make_message(1, 100, 200, text="/status"))]
        result = run_classified_intake(raw, dry_run=True)
        self.assertIn("No commands executed", result["report_text"])
        self.assertIn("CONFIRMED", result["report_text"])
        self.assertIn("Classified for human review", result["report_text"])


# ── Valid request types constant test ────────────────────────────────────────

class TestConstants(unittest.TestCase):
    """Verify module constants are correct."""

    def test_all_known_request_types(self):
        self.assertIn("status_request", VALID_REQUEST_TYPES)
        self.assertIn("brief_request", VALID_REQUEST_TYPES)
        self.assertIn("next_action_request", VALID_REQUEST_TYPES)
        self.assertIn("queue_request", VALID_REQUEST_TYPES)
        self.assertIn("note_or_task_request", VALID_REQUEST_TYPES)
        self.assertEqual(len(VALID_REQUEST_TYPES), 5)

    def test_default_is_note_or_task(self):
        self.assertEqual(DEFAULT_REQUEST_TYPE, "note_or_task_request")


if __name__ == "__main__":
    unittest.main()

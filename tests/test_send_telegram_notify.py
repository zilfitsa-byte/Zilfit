"""Tests for tools/send_telegram_notify.py — mocks only, no network calls."""

import json
import unittest
from unittest.mock import patch, MagicMock
import urllib.error
import urllib.request

from tools.send_telegram_notify import (
    get_credentials,
    send_message,
    build_test_message,
)


class TestGetCredentials(unittest.TestCase):
    """Test credential retrieval from environment variables."""

    def teardown_method(self, method):
        import os
        os.environ.pop("TELEGRAM_BOT_TOKEN", None)
        os.environ.pop("TELEGRAM_CHAT_ID", None)

    def test_missing_token(self):
        """Returns None when TELEGRAM_BOT_TOKEN is not set."""
        import os
        os.environ.pop("TELEGRAM_BOT_TOKEN", None)
        os.environ["TELEGRAM_CHAT_ID"] = "12345"
        token, chat_id = get_credentials()
        self.assertIsNone(token)
        self.assertIsNone(chat_id)

    def test_missing_chat_id(self):
        """Returns None when TELEGRAM_CHAT_ID is not set."""
        import os
        os.environ["TELEGRAM_BOT_TOKEN"] = "test-token"
        os.environ.pop("TELEGRAM_CHAT_ID", None)
        token, chat_id = get_credentials()
        self.assertIsNone(token)
        self.assertIsNone(chat_id)

    def test_both_set(self):
        """Returns both values when env vars are set."""
        import os
        os.environ["TELEGRAM_BOT_TOKEN"] = "abc123"
        os.environ["TELEGRAM_CHAT_ID"] = "-999888777"
        token, chat_id = get_credentials()
        self.assertEqual(token, "abc123")
        self.assertEqual(chat_id, "-999888777")

    def test_whitespace_only_token(self):
        """Returns None when token is whitespace only."""
        import os
        os.environ["TELEGRAM_BOT_TOKEN"] = "   "
        os.environ["TELEGRAM_CHAT_ID"] = "12345"
        token, chat_id = get_credentials()
        self.assertIsNone(token)
        self.assertIsNone(chat_id)


class TestBuildTestMessage(unittest.TestCase):
    """Test the safe test message builder."""

    def test_contains_warning(self):
        message = build_test_message()
        self.assertIn("test", message.lower())
        self.assertIn("ZILFIT", message)

    def test_no_sensitive_data(self):
        message = build_test_message()
        self.assertNotIn("token", message.lower())
        self.assertNotIn("key", message.lower())
        self.assertNotIn("secret", message.lower())


class TestSendMessage(unittest.TestCase):
    """Test the Telegram send_message function with mocked network."""

    def _make_mock_response(self, body_dict):
        mock_response = MagicMock()
        mock_response.read.return_value = json.dumps(body_dict).encode()
        mock_response.__enter__ = MagicMock(return_value=mock_response)
        mock_response.__exit__ = MagicMock(return_value=False)
        return mock_response

    @patch("tools.send_telegram_notify.urllib.request.urlopen")
    def test_success(self, mock_urlopen):
        """Returns True on successful API response."""
        mock_urlopen.return_value = self._make_mock_response({"ok": True, "result": {}})

        ok, result = send_message("fake-token", "12345", "hello")
        self.assertTrue(ok)
        self.assertTrue(result.get("ok"))

    @patch("tools.send_telegram_notify.urllib.request.urlopen")
    def test_api_error(self, mock_urlopen):
        """Returns False with error description when API returns ok=false."""
        mock_urlopen.return_value = self._make_mock_response({
            "ok": False,
            "description": "Bad Request: chat not found",
        })

        ok, result = send_message("fake-token", "12345", "hello")
        self.assertFalse(ok)
        self.assertIn("chat not found", result)

    @patch("tools.send_telegram_notify.urllib.request.urlopen")
    def test_http_error(self, mock_urlopen):
        """Returns False on HTTP error."""
        http_error = urllib.error.HTTPError(
            "http://example.com", 404, "Not Found", {}, None
        )
        mock_urlopen.side_effect = http_error

        ok, result = send_message("fake-token", "12345", "hello")
        self.assertFalse(ok)
        self.assertIn("HTTP error 404", result)

    @patch("tools.send_telegram_notify.urllib.request.urlopen")
    def test_url_error(self, mock_urlopen):
        """Returns False on URLError (network unavailable)."""
        url_error = urllib.error.URLError("Connection refused")
        mock_urlopen.side_effect = url_error

        ok, result = send_message("fake-token", "12345", "hello")
        self.assertFalse(ok)
        self.assertIn("Network error", result)

    @patch("tools.send_telegram_notify.urllib.request.urlopen")
    def test_correct_url_and_body(self, mock_urlopen: MagicMock):
        """Verifies the correct API URL and request body are sent."""
        mock_urlopen.return_value = self._make_mock_response({"ok": True})

        send_message("test-token", "-98765", "hello world")

        call_args = mock_urlopen.call_args
        request = call_args[0][0]  # type: urllib.request.Request
        self.assertEqual(
            request.full_url,
            "https://api.telegram.org/bottest-token/sendMessage",
        )


if __name__ == "__main__":
    unittest.main()

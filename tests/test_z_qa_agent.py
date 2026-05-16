"""Tests for Z-QA runtime agent: evaluate_reports_and_write_qa_records.

Covers:
  1. evaluate_report_md() with valid and broken reports
  2. evaluate_json_output() with valid/broken JSON
  3. run_qa() single-file mode
  4. run_qa() bulk mode writes SharedDB records
  5. CLI entry point smoke test
"""

import json
import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

# Ensure project root is importable
import sys
_project_root = Path(__file__).resolve().parent.parent
if str(_project_root) not in sys.path:
    sys.path.insert(0, str(_project_root))

from runtime.run_z_qa_agent import (
    evaluate_report_md,
    evaluate_json_output,
    run_qa,
)
from runtime.shared_db import SharedDB


class TestEvaluateReportMd(unittest.TestCase):
    """Tests for markdown report structural evaluation."""

    def _tmp_md(self, content: str) -> Path:
        fd, path = tempfile.mkstemp(suffix=".md")
        os.write(fd, content.encode())
        os.close(fd)
        return Path(path)

    def test_valid_report_passes(self):
        """A report with date, sections, and reasonable size should pass."""
        content = (
            "# 2026-05-16 Z-Bio Daily Report\n\n"
            "## Summary\nBiomechanics analysis completed.\n\n"
            "## Tests Run\nAll 10 passed.\n\n"
            "## Risk\nLow risk identified.\n\n"
            "## Findings\nDetailed findings go here. "
            * 5  # Make it > 200 chars
        )
        p = self._tmp_md(content)
        try:
            result = evaluate_report_md(p)
            self.assertEqual(result["status"], "passed")
            self.assertTrue(any(n == "date_present" and ok for n, ok in result["checks"]))
            self.assertTrue(any(n == "has_sections" and ok for n, ok in result["checks"]))
        finally:
            p.unlink()

    def test_empty_report_fails(self):
        """Empty file should fail."""
        p = self._tmp_md("")
        try:
            result = evaluate_report_md(p)
            self.assertEqual(result["status"], "failed")
        finally:
            p.unlink()

    def test_missing_date_warning(self):
        """Report with only sections but no date and tiny size should warn."""
        content = "## Summary\nSome summary text."  # < 200 chars, no date, has sections
        p = self._tmp_md(content)
        try:
            result = evaluate_report_md(p)
            self.assertIn(result["status"], ("warning", "failed"))
            self.assertTrue(any(n == "date_present" and not ok for n, ok in result["checks"]))
        finally:
            p.unlink()

    def test_nonexistent_file(self):
        evaluate_report_md(Path("/nonexistent/path/to/report.md"))
        r = evaluate_report_md(Path("/nonexistent/foo.md"))
        self.assertEqual(r["status"], "failed")


class TestEvaluateJsonOutput(unittest.TestCase):
    """Tests for JSON agent output structural evaluation."""

    def _tmp_json(self, content: str) -> Path:
        fd, path = tempfile.mkstemp(suffix=".json")
        os.write(fd, content.encode())
        os.close(fd)
        return Path(path)

    def test_valid_agent_output_passes(self):
        data = {"task_id": "zfoo-001", "agent_name": "Z-Bio", "result": 42}
        p = self._tmp_json(json.dumps(data))
        try:
            result = evaluate_json_output(p)
            self.assertEqual(result["status"], "passed")
            self.assertTrue(any(n == "valid_json" and ok for n, ok in result["checks"]))
            self.assertTrue(any(n == "has_task_id" and ok for n, ok in result["checks"]))
            self.assertTrue(any(n == "has_agent" and ok for n, ok in result["checks"]))
        finally:
            p.unlink()

    def test_invalid_json_fails(self):
        p = self._tmp_json("{invalid json!!!")
        try:
            result = evaluate_json_output(p)
            self.assertEqual(result["status"], "failed")
            self.assertTrue(any(n == "valid_json" and not ok for n, ok in result["checks"]))
        finally:
            p.unlink()

    def test_json_missing_task_id(self):
        """JSON with no task_id or agent_name should not fully pass."""
        data = {"notes": "hello"}  # has neither task_id nor agent_name
        p = self._tmp_json(json.dumps(data))
        try:
            result = evaluate_json_output(p)
            # 3/5 pass: valid_json, is_dict, non_empty — missing task_id + agent = 0.6 => warning
            self.assertIn(result["status"], ("warning", "failed"))
        finally:
            p.unlink()

    def test_json_list_not_dict(self):
        """A JSON array should not pass as agent output."""
        p = self._tmp_json(json.dumps([{"task_id": "x", "agent_name": "y"}]))
        try:
            result = evaluate_json_output(p)
            self.assertIn(result["status"], ("warning", "failed"))
            self.assertTrue(any(n == "is_dict" and not ok for n, ok in result["checks"]))
        finally:
            p.unlink()


class TestRunQa(unittest.TestCase):
    """Tests for the main run_qa pipeline."""

    def test_single_file_reports_shared_db(self):
        """run_qa with --file evaluates it and writes to SharedDB."""
        fd, db_path = tempfile.mkstemp(suffix="_zqa.db")
        os.close(fd)

        # Create a temp report file
        content = "# 2026-05-16 Test Report\n\n## Summary\nQA evaluation test.\n\n## Tests\nAll passed\n" * 3
        fd2, file_path = tempfile.mkstemp(suffix=".md")
        os.write(fd2, content.encode())
        os.close(fd2)

        try:
            db = SharedDB(db_path)
            before = db.count()

            result = run_qa(single_file=file_path, db=db)
            self.assertIsNotNone(result.get("results"))
            self.assertEqual(len(result["results"]), 1)
            self.assertIn("task_id", result["results"][0])
            self.assertIn("status", result["results"][0])

            # Verify SharedDB got a new record
            after = db.count()
            self.assertEqual(after, before + 1, f"Expected {before+1} records, got {after}")

            # Verify the record is retrievable — QA "passed" maps to SharedDB "completed"
            task_id = result["results"][0]["task_id"]
            record = db.get(agent_name="Z-QA", task_id=task_id)
            self.assertIsNotNone(record)
            assert record is not None
            status_map = {"passed": "completed", "warning": "blocked", "failed": "pending"}
            self.assertEqual(record["status"], status_map.get(result["results"][0]["status"]))

        finally:
            os.unlink(file_path)
            if os.path.exists(db_path):
                os.unlink(db_path)

    def test_single_json_file_reports_shared_db(self):
        """run_qa with a JSON file works identically."""
        fd, db_path = tempfile.mkstemp(suffix="_zqa_json.db")
        os.close(fd)

        data = {"task_id": "ztest-042", "agent_name": "Z-Physics", "decision": "pass"}
        fd2, file_path = tempfile.mkstemp(suffix=".json")
        os.write(fd2, json.dumps(data).encode())
        os.close(fd2)

        try:
            db = SharedDB(db_path)
            before = db.count()

            result = run_qa(single_file=file_path, db=db)
            self.assertEqual(len(result["results"]), 1)
            r = result["results"][0]
            self.assertEqual(r["status"], "passed")

            after = db.count()
            self.assertEqual(after, before + 1)

            task_id = r["task_id"]
            record = db.get(agent_name="Z-QA", task_id=task_id)
            self.assertIsNotNone(record)
        finally:
            os.unlink(file_path)
            if os.path.exists(db_path):
                os.unlink(db_path)

    def test_nonexistent_file_returns_error(self):
        result = run_qa(single_file="/nonexistent/file.md")
        self.assertIn("error", result)

    def test_bulk_mode_with_sample_files(self):
        """Create a fake reports/daily/ and verify bulk discovery works."""
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            reports_dir = root / "reports" / "daily"
            reports_dir.mkdir(parents=True)

            # Write a valid report
            (reports_dir / "2026-05-16_test_report.md").write_text(
                "# 2026-05-16 Report\n## Summary\nComplete.\n## Tests\nAll passed.\n" * 5
            )

            # Write a JSON output
            root_out = root / "runtime" / "out"
            root_out.mkdir(parents=True)
            (root_out / "agent_output.json").write_text(
                json.dumps({"task_id": "zagg-001", "agent_name": "Z-Bio", "ok": True})
            )

            db_fd, db_path = tempfile.mkstemp(suffix="_zqa_bulk.db")
            os.close(db_fd)

            try:
                db = SharedDB(db_path)
                result = run_qa(project_root=root, lookback_days=365, db=db)
                self.assertGreater(result["total"], 0, "Should find at least 1 file")
                self.assertIsNotNone(result.get("passed"))
                # Verify records were written
                self.assertGreater(db.count(), 0)
            finally:
                if os.path.exists(db_path):
                    os.unlink(db_path)


class TestQaCliSmoke(unittest.TestCase):
    """Smoke test for CLI entry point."""

    def test_main_runs_without_error(self):
        """Main should not raise even if no recent reports exist."""
        from runtime.run_z_qa_agent import main

        with patch.object(sys, "argv", ["run_z_qa_agent", "--lookback-days", "0"]):
            result = main()
            self.assertIn("shared_db_persisted", result)
            self.assertTrue(result["shared_db_persisted"])
            self.assertIn("qa_task_id", result)


if __name__ == "__main__":
    unittest.main(verbosity=2)

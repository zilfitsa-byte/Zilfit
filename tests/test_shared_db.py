"""Smoke tests for runtime.shared_db module."""
import os
import tempfile
import unittest

from runtime.shared_db import SharedDB


class TestSharedDB(unittest.TestCase):
    """Basic smoke tests — validates CRUD and constraints."""

    def setUp(self):
        fd, self._path = tempfile.mkstemp(suffix=".db")
        os.close(fd)
        self.db = SharedDB(self._path)

    def tearDown(self):
        if os.path.exists(self._path):
            os.remove(self._path)

    # -- insert / upsert -------------------------------------------------------

    def test_upsert_creates_record(self):
        rec = self.db.upsert(agent_name="Z-Bio", task_id="bio-001", status="completed",
                              summary="Pressure data collected", risk_level="low",
                              next_action="Z-Design review")
        self.assertEqual(rec["agent_name"], "Z-Bio")
        self.assertEqual(rec["task_id"], "bio-001")
        self.assertEqual(rec["status"], "completed")
        self.assertIn("created_at", rec)
        self.assertIn("updated_at", rec)

    def test_upsert_idempotent_update(self):
        r1 = self.db.upsert(agent_name="Z-Bio", task_id="bio-001", status="pending",
                             summary="initial", risk_level="low", next_action="")
        r2 = self.db.upsert(agent_name="Z-Bio", task_id="bio-001", status="completed",
                             summary="done", risk_level="medium", next_action="review")
        # Same id on update (UNIQUE constraint triggered), status changed
        self.assertEqual(r2["status"], "completed")
        self.assertEqual(r2["summary"], "done")
        self.assertEqual(r2["risk_level"], "medium")

    # -- validation ------------------------------------------------------------

    def test_invalid_status_raises(self):
        with self.assertRaises(ValueError):
            self.db.upsert(agent_name="Z-Bio", task_id="x", status="nope")

    def test_invalid_risk_raises(self):
        with self.assertRaises(ValueError):
            self.db.upsert(agent_name="Z-Bio", task_id="x", risk_level="extreme")

    # -- queries ---------------------------------------------------------------

    def test_get_existing(self):
        self.db.upsert(agent_name="Z-Bio", task_id="bio-001", summary="hello")
        rec = self.db.get(agent_name="Z-Bio", task_id="bio-001")
        self.assertIsNotNone(rec)
        self.assertEqual(rec["summary"], "hello")

    def test_get_missing(self):
        self.assertIsNone(self.db.get(agent_name="Z-Bio", task_id="no-such-task"))

    def test_list_by_agent(self):
        self.db.upsert(agent_name="Z-Bio", task_id="bio-001", summary="a")
        self.db.upsert(agent_name="Z-Bio", task_id="bio-002", summary="b")
        self.db.upsert(agent_name="Z-Design", task_id="des-001", summary="c")
        results = self.db.list_by_agent("Z-Bio")
        self.assertEqual(len(results), 2)

    def test_list_by_status(self):
        self.db.upsert(agent_name="Z-Bio", task_id="bio-001", status="completed")
        self.db.upsert(agent_name="Z-Design", task_id="des-001", status="pending")
        results = self.db.list_by_status("completed")
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0]["agent_name"], "Z-Bio")

    def test_list_all(self):
        self.db.upsert(agent_name="Z-Bio", task_id="bio-001")
        self.db.upsert(agent_name="Z-Design", task_id="des-001")
        self.assertEqual(self.db.count(), 2)
        all_rows = self.db.list_all()
        self.assertEqual(len(all_rows), 2)

    # -- defaults --------------------------------------------------------------

    def test_default_values(self):
        rec = self.db.upsert(agent_name="Z-Ops", task_id="ops-001")
        self.assertEqual(rec["status"], "pending")
        self.assertEqual(rec["risk_level"], "low")
        self.assertEqual(rec["summary"], "")
        self.assertEqual(rec["next_action"], "")


if __name__ == "__main__":
    unittest.main()

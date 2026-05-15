"""P0 Integration test for SharedDB — proves an agent can write and read back.

This test runs against a real file-based DB (not a throwaway temp file)
to prove the full write → persist → read cycle works as an agent would
experience it in production.
"""
import os
import tempfile
import unittest

from runtime.shared_db import SharedDB


class TestSharedDBIntegration(unittest.TestCase):
    """Integration-level tests: write to SharedDB, query it back."""

    def test_write_and_read_same_db_instance(self):
        """Agent writes a record then immediately reads it back."""
        db = SharedDB()                       # default runtime/zilfit_shared.db
        agent = "Z-Ops"
        tid = "p0-integration-test-001"

        # -- write --------------------------------------------------------
        rec = db.upsert(
            agent_name=agent,
            task_id=tid,
            status="completed",
            summary="P0 SharedDB integration smoke — write succeeded",
            risk_level="low",
            next_action="No action needed",
        )
        self.assertEqual(rec["agent_name"], agent)
        self.assertEqual(rec["task_id"], tid)
        self.assertEqual(rec["status"], "completed")

        # -- read back ----------------------------------------------------
        fetched = db.get(agent_name=agent, task_id=tid)
        self.assertIsNotNone(fetched, "Record written but not found on read")
        assert fetched is not None  # type guard for Pyright
        self.assertEqual(fetched["agent_name"], agent)
        self.assertEqual(fetched["task_id"], tid)
        self.assertEqual(fetched["status"], "completed")
        self.assertEqual(fetched["summary"], "P0 SharedDB integration smoke — write succeeded")

        # -- list_by_agent includes it ------------------------------------
        all_agent_records = db.list_by_agent(agent)
        agent_tids = [r["task_id"] for r in all_agent_records]
        self.assertIn(tid, agent_tids)

        print("[PASS] write-and-read-same-db: record written and read back successfully")

    def test_write_and_read_separate_instances(self):
        """Simulates two separate agent processes: one writes, one reads.

        Creates a real file DB, writes with instance A, reads with instance B.
        """
        fd, path = tempfile.mkstemp(suffix="_integration.db")
        os.close(fd)
        try:
            # Simulates Agent A writing
            writer = SharedDB(path)
            writer.upsert(
                agent_name="Z-Bio",
                task_id="bio-int-001",
                status="in_progress",
                summary="Biomechanical data collection started",
                risk_level="medium",
                next_action="Await calibration data",
            )

            # Simulates Agent B reading from the same file
            reader = SharedDB(path)
            fetched = reader.get(agent_name="Z-Bio", task_id="bio-int-001")
            self.assertIsNotNone(fetched, "Separate instance could not read record")
            assert fetched is not None  # type guard for Pyright
            self.assertEqual(fetched["agent_name"], "Z-Bio")
            self.assertEqual(fetched["summary"], "Biomechanical data collection started")
            self.assertEqual(fetched["risk_level"], "medium")
            print("[PASS] write-and-read-separate: two instances share the same DB correctly")
        finally:
            if os.path.exists(path):
                os.remove(path)

    def test_count_grows_after_write(self):
        """Verify the DB count increases after a new write."""
        db = SharedDB()
        before = db.count()
        db.upsert(agent_name="Z-Design", task_id="des-int-001", summary="count test")
        after = db.count()
        self.assertEqual(after, before + 1)
        print(f"[PASS] count: before={before}, after={after} (+1)")


if __name__ == "__main__":
    unittest.main(verbosity=2)

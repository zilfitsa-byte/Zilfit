"""Tests for Z-Claims runtime scanner: scan_file, run_claims_scan, classifications.

Covers:
  1. FORBIDDEN pattern detection (treats, cures, heals, diagnoses, etc.)
  2. NEEDS_SOFTENING pattern detection (reduces pain, eliminates discomfort, etc.)
  3. NEEDS_EVIDENCE pattern detection (improves comfort, clinically proven, etc.)
  4. ALLOWED — clean engineering-only text passes
  5. Gov reference files skipped (don't self-flag their own lists)
  6. Empty/non-existent files handled
  7. run_claims_scan writes SharedDB record
  8. Bulk scan with auto-discovery
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

from runtime.z_claims_scanner import (
    ALLOWED,
    FORBIDDEN,
    NEEDS_EVIDENCE,
    NEEDS_SOFTENING,
    _is_governance_reference,
    run_claims_scan,
    scan_file,
)
from runtime.shared_db import SharedDB


class TestScanFileForbidden(unittest.TestCase):
    """FORBIDDEN claim detection."""

    def _tmp(self, suffix, content):
        fd, path = tempfile.mkstemp(suffix=suffix)
        os.write(fd, content.encode())
        os.close(fd)
        p = Path(path)
        return p

    def test_treats_disease_forbidden(self):
        p = self._tmp(".md", "# Test\nThis product treats plantar fasciitis effectively.")
        try:
            r = scan_file(p)
            self.assertEqual(r["overall_status"], FORBIDDEN)
            self.assertTrue(any(f["classification"] == FORBIDDEN for f in r["findings"]))
        finally:
            p.unlink()

    def test_cures_pain_forbidden(self):
        p = self._tmp(".md", "# Test\nRelieves and cures chronic foot pain permanently.")
        try:
            r = scan_file(p)
            findings_forbidden = [f for f in r["findings"] if f["classification"] == FORBIDDEN]
            self.assertTrue(len(findings_forbidden) > 0)
        finally:
            p.unlink()

    def test_diagnoses_forbidden(self):
        p = self._tmp(".txt", "This device diagnoses medical conditions.")
        try:
            r = scan_file(p)
            self.assertEqual(r["overall_status"], FORBIDDEN)
        finally:
            p.unlink()

    def test_prevents_injury_forbidden(self):
        p = self._tmp(".md", "Prevents injury during athletic activities.")
        try:
            r = scan_file(p)
            self.assertTrue(any(f["classification"] == FORBIDDEN for f in r["findings"]))
        finally:
            p.unlink()

    def test_regulates_hormones_forbidden(self):
        p = self._tmp(".md", "Regulates hormone levels naturally through foot pressure mapping.")
        try:
            r = scan_file(p)
            self.assertEqual(r["overall_status"], FORBIDDEN)
        finally:
            p.unlink()

    def test_healing_forbidden(self):
        p = self._tmp(".md", "Heals damaged plantar fascia tissue.")
        try:
            r = scan_file(p)
            self.assertTrue(any(f["classification"] == FORBIDDEN for f in r["findings"]))
        finally:
            p.unlink()


class TestScanFileSoftening(unittest.TestCase):
    """NEEDS_SOFTENING claim detection."""

    def _tmp(self, suffix, content):
        fd, path = tempfile.mkstemp(suffix=suffix)
        os.write(fd, content.encode())
        os.close(fd)
        return Path(path)

    def test_reduces_pain_softening(self):
        p = self._tmp(".md", "Reduces foot pressure pain by 60%.")
        try:
            r = scan_file(p)
            self.assertTrue(any(f["classification"] == NEEDS_SOFTENING for f in r["findings"]))
        finally:
            p.unlink()

    def test_eliminates_discomfort_softening(self):
        p = self._tmp(".md", "Eliminates discomfort during long walks.")
        try:
            r = scan_file(p)
            self.assertTrue(any(f["classification"] == NEEDS_SOFTENING for f in r["findings"]))
        finally:
            p.unlink()

    def test_corrects_posture_softening(self):
        p = self._tmp(".md", "Corrects posture alignment for all users.")
        try:
            r = scan_file(p)
            self.assertTrue(any(f["classification"] == NEEDS_SOFTENING for f in r["findings"]))
        finally:
            p.unlink()

    def test_clinically_proven_softening(self):
        p = self._tmp(".md", "Clinically proven to improve comfort.")
        try:
            r = scan_file(p)
            self.assertTrue(any(f["classification"] == NEEDS_SOFTENING for f in r["findings"]))
        finally:
            p.unlink()

    def test_therapeutic_benefit_softening(self):
        p = self._tmp(".md", "Provides therapeutic benefit for daily wear.")
        try:
            r = scan_file(p)
            self.assertTrue(any(f["classification"] == NEEDS_SOFTENING for f in r["findings"]))
        finally:
            p.unlink()


class TestScanFileEvidence(unittest.TestCase):
    """NEEDS_EVIDENCE claim detection."""

    def _tmp(self, suffix, content):
        fd, path = tempfile.mkstemp(suffix=suffix)
        os.write(fd, content.encode())
        os.close(fd)
        return Path(path)

    def test_improves_comfort_evidence(self):
        p = self._tmp(".md", "Improves comfort for all-day wear.")
        try:
            r = scan_file(p)
            self.assertTrue(any(f["classification"] == NEEDS_EVIDENCE for f in r["findings"]))
        finally:
            p.unlink()

    def test_boosts_recovery_evidence(self):
        p = self._tmp(".md", "Boosts recovery after workouts.")
        try:
            r = scan_file(p)
            self.assertTrue(any(f["classification"] == NEEDS_EVIDENCE for f in r["findings"]))
        finally:
            p.unlink()

    def test_science_based_evidence(self):
        p = self._tmp(".md", "Science-based design for maximum comfort.")
        try:
            r = scan_file(p)
            self.assertTrue(any(f["classification"] == NEEDS_EVIDENCE for f in r["findings"]))
        finally:
            p.unlink()


class TestScanFileAllowed(unittest.TestCase):
    """Clean engineering-only text should pass ALLOWED."""

    def _tmp(self, suffix, content):
        fd, path = tempfile.mkstemp(suffix=suffix)
        os.write(fd, content.encode())
        os.close(fd)
        return Path(path)

    def test_engineering_only_passes(self):
        p = self._tmp(".md", (
            "# Engineering Report\n"
            "Gyroid 0.6mm wall thickness achieved on TPU print.\n"
            "Plantar pressure distribution analyzed using FEA simulation.\n"
            "Comfort score: 78/100 based on pressure uniformity metrics.\n"
            "Next steps: refine lattice parameters and rerun printability check.\n"
        ))
        try:
            r = scan_file(p)
            self.assertEqual(r["overall_status"], ALLOWED)
            self.assertEqual(len(r["findings"]), 0)
        finally:
            p.unlink()

    def test_empty_file_allowed(self):
        p = self._tmp(".md", "")
        try:
            r = scan_file(p)
            self.assertEqual(r["overall_status"], ALLOWED)
        finally:
            p.unlink()

    def test_nonexistent_file_error(self):
        r = scan_file(Path("/nonexistent/path/file.md"))
        self.assertEqual(r["overall_status"], "error")
        self.assertIn("error", r)


class TestGovernanceReferenceSkip(unittest.TestCase):
    """Governance and test files listing the forbidden phrases should self-flag."""

    def test_governance_path_skipped(self):
        p = Path("governance/Z_CLAIMS_SKILLS.md")
        self.assertTrue(_is_governance_reference(p))

    def test_tests_path_skipped(self):
        p = Path("tests/test_claims_patterns.py")
        self.assertTrue(_is_governance_reference(p))

    def test_runtime_path_skipped(self):
        p = Path("runtime/z_claims_scanner.py")
        self.assertTrue(_is_governance_reference(p))

    def test_reports_path_not_skipped(self):
        p = Path("reports/daily/some_report.md")
        self.assertFalse(_is_governance_reference(p))


class TestClaimsScanSharedDB(unittest.TestCase):
    """run_claims_scan writes SharedDB records."""

    def _tmp_write(self, content):
        fd, path = tempfile.mkstemp(suffix=".md")
        os.write(fd, content.encode())
        os.close(fd)
        return Path(path)

    def test_clean_scan_writes_completed_status(self):
        """Scanning clean content should write completed to SharedDB."""
        tmp_dir = tempfile.mkdtemp()
        clean_file = Path(tmp_dir) / "clean_report.md"
        clean_file.write_text(
            "# Engineering Report\n"
            "Gyroid lattice parameters optimized for size 42.\n"
            "FEA simulation completed successfully. " * 10
        )
        db_path = os.path.join(tmp_dir, "test_claims.db")

        try:
            db = SharedDB(db_path)
            output = run_claims_scan(
                file_path=clean_file,
                project_root=Path(tmp_dir),
                db=db,
            )
            self.assertTrue(output["shared_db_persisted"])
            self.assertIn("shared_db_task_id", output)
            self.assertEqual(output["overall_status"], ALLOWED)

            # Verify the SharedDB record
            rec = db.get(agent_name="Z-Claims", task_id=output["task_id"])
            self.assertIsNotNone(rec)
            assert rec is not None
            self.assertEqual(rec["status"], "completed")
            self.assertEqual(rec["risk_level"], "low")
        finally:
            clean_file.unlink()
            if os.path.exists(db_path):
                os.remove(db_path)

    def test_forbidden_scan_writes_blocked_status(self):
        """Scanning FORBIDDEN content should write blocked to SharedDB."""
        tmp_dir = tempfile.mkdtemp()
        bad_file = Path(tmp_dir) / "bad_report.md"
        bad_file.write_text("This product treats chronic foot disease and cures pain.")
        db_path = os.path.join(tmp_dir, "test_claims2.db")

        try:
            db = SharedDB(db_path)
            output = run_claims_scan(
                file_path=bad_file,
                project_root=Path(tmp_dir),
                db=db,
            )
            self.assertTrue(output["shared_db_persisted"])
            self.assertEqual(output["overall_status"], FORBIDDEN)

            rec = db.get(agent_name="Z-Claims", task_id=output["task_id"])
            self.assertIsNotNone(rec)
            assert rec is not None
            self.assertEqual(rec["status"], "blocked")
            self.assertEqual(rec["risk_level"], "critical")
        finally:
            bad_file.unlink()
            if os.path.exists(db_path):
                os.remove(db_path)


class TestClaimsScanBulk(unittest.TestCase):
    """Bulk scan with auto-discovery."""

    def test_bulk_empty_project(self):
        """Auto-discovery on a temp directory with no reports returns 0 scanned."""
        tmp_dir = tempfile.mkdtemp()
        try:
            output = run_claims_scan(
                project_root=Path(tmp_dir),
            )
            self.assertEqual(output["files_scanned"], 0)
            self.assertEqual(output["total_findings"], 0)
            self.assertTrue(output["shared_db_persisted"])
        finally:
            import shutil
            shutil.rmtree(tmp_dir, ignore_errors=True)

    def test_bulk_with_reports_dir(self):
        """Auto-discovery finds files in reports/ subdirectory."""
        tmp_dir = tempfile.mkdtemp()
        reports_dir = Path(tmp_dir) / "reports" / "daily"
        reports_dir.mkdir(parents=True)
        (reports_dir / "report1.md").write_text(
            "Engineering scan completed for TPU gyroid. " * 20
        )
        (reports_dir / "report2.md").write_text(
            "Lattice optimization results: stress < 0.9 MPa. " * 15
        )

        try:
            output = run_claims_scan(
                project_root=Path(tmp_dir),
                lookback_days=30,
            )
            self.assertEqual(output["files_scanned"], 2)
            self.assertEqual(output["total_findings"], 0)
            self.assertEqual(output["overall_status"], ALLOWED)
        finally:
            import shutil
            shutil.rmtree(tmp_dir, ignore_errors=True)


if __name__ == "__main__":
    unittest.main()

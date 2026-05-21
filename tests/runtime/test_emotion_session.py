#!/usr/bin/env python3
"""Tests for ZILFIT Emotion Session Layer (SQLite persistence).

Six tests:
1. Database table creation
2. Save a CALM session
3. Save a hybrid session (FEMME-VITAL)
4. Read the latest session back
5. Schema contains the required keys
6. Reject an incomplete payload
"""

import json
import os
import sys
import tempfile
from pathlib import Path

# Make runtime and project root importable
PROJ_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJ_ROOT / "runtime"))
sys.path.insert(0, str(PROJ_ROOT))

from zilfit_emotion_session import EmotionSession, InvalidPayloadError


def _build_payload(
    edition: str = "CALM",
    emotional_target: str = "grounding",
    warnings: list | None = None,
) -> dict:
    """Construct a minimal valid pipeline result dict."""
    return {
        "pipeline_status": "success",
        "selected_edition": edition,
        "combined_edition": False,
        "secondary_edition": None,
        "edition_profile": {
            "intended_effect": f"Support {emotional_target}.",
            "psychological_state": ["stress"],
            "first_sensation_20min": {},
            "cumulative_effect": {},
            "foot_zones": {
                "heel": {"density": 0.30, "stimulation": "gentle"},
                "midfoot": {"density": 0.34, "stimulation": "soft"},
                "forefoot": {"density": 0.30, "stimulation": "smooth"},
                "toe": {"density": 0.26, "stimulation": "minimal"},
            },
            "stimulation_profile": {
                "type": "low_amplitude",
                "frequency_hz": 0.5,
                "intensity": "low",
                "coverage_percent": 65,
                "description": "Test profile",
            },
            "comfort_targets": {},
            "reflexology_inspired_zones": {
                "reference": "solar_plexus_map.json",
                "primary_zone": emotional_target,
            },
        },
        "zone_geometry": {
            "active_zones": ["zone_midfoot_01"],
            "primary_emotion_target": emotional_target,
            "zone_intensity": {"zone_midfoot_01": 0.6},
            "zone_geometry_hints": {
                "zone_midfoot_01": {
                    "shape": "gyroid",
                    "depth_mm": 1.5,
                    "diameter_mm": 6.0,
                    "height_mm": 1.2,
                    "cad_direction": "inferior",
                }
            },
        },
        "validation": {
            "warnings": warnings or [],
            "errors": [],
            "clean": True,
        },
        "safety_flags": [],
    }


def _tmp_db() -> str:
    """Return a fresh temp-file path for SQLite."""
    fd, path = tempfile.mkstemp(suffix=".db")
    os.close(fd)
    return path


# ──────────────────────────────────────────────────────────────────────
# 1. إنشاء قاعدة البيانات
# ──────────────────────────────────────────────────────────────────────

def test_database_creation():
    """The sessions table is created automatically on first connect."""
    db = _tmp_db()
    try:
        session = EmotionSession(db_path=db)
        assert session.table_exists(), "emotion_sessions table not created"
        assert session.count() == 0
    finally:
        os.unlink(db)


# ──────────────────────────────────────────────────────────────────────
# 2. حفظ جلسة CALM
# ──────────────────────────────────────────────────────────────────────

def test_save_calm_session():
    """A CALM pipeline result is persisted and retrievable."""
    db = _tmp_db()
    try:
        session = EmotionSession(db_path=db)
        payload = _build_payload(edition="CALM", emotional_target="grounding")
        sid = session.save(payload)

        assert sid is not None
        assert len(sid) > 0
        assert session.count() == 1
    finally:
        os.unlink(db)


# ──────────────────────────────────────────────────────────────────────
# 3. حفظ جلسة hybrid
# ──────────────────────────────────────────────────────────────────────

def test_save_hybrid_session():
    """A hybrid (FEMME-VITAL) session is saved correctly."""
    db = _tmp_db()
    try:
        session = EmotionSession(db_path=db)
        payload = _build_payload(
            edition="FEMME-VITAL",
            emotional_target="soothing_release",
            warnings=[
                "High fatigue — considered VITAL as secondary edition."
            ],
        )
        # Mark as combined in the payload
        payload["combined_edition"] = True
        payload["secondary_edition"] = "VITAL"

        sid = session.save(payload)
        assert session.count() == 1

        # Verify the combined flag survived
        # raw_payload_json is already deserialized by _row_to_dict
        latest = session.get_latest()
        raw = latest["raw_payload_json"]
        assert raw["combined_edition"] is True
        assert raw["secondary_edition"] == "VITAL"
    finally:
        os.unlink(db)


# ──────────────────────────────────────────────────────────────────────
# 4. قراءة آخر جلسة
# ──────────────────────────────────────────────────────────────────────

def test_get_latest_session():
    """get_latest() returns the most recently saved session."""
    db = _tmp_db()
    try:
        session = EmotionSession(db_path=db)

        # Save CALM first
        payload_calm = _build_payload(edition="CALM")
        session.save(payload_calm)

        # Save VITAL second
        payload_vital = _build_payload(edition="VITAL", emotional_target="release")
        session.save(payload_vital)

        latest = session.get_latest()
        assert latest is not None
        assert latest["edition"] == "VITAL"

        # density_map should be a dict
        assert isinstance(latest["density_map"], dict)
        assert "heel" in latest["density_map"]

        # pressure_zones should be a list
        assert isinstance(latest["pressure_zones"], list)

        # Verify we can also filter by edition
        calm_only = session.get_latest(edition="CALM")
        assert calm_only is not None
        assert calm_only["edition"] == "CALM"

        # get_latest(edition="FOCUS") should return None
        focus_only = session.get_latest(edition="FOCUS")
        assert focus_only is None
    finally:
        os.unlink(db)


# ──────────────────────────────────────────────────────────────────────
# 5. schema يحتوي المفاتيح المطلوبة
# ──────────────────────────────────────────────────────────────────────

def test_schema_required_keys():
    """The JSON schema file contains all required session keys."""
    REPO_ROOT = PROJ_ROOT.parent
    schema_path = REPO_ROOT / "schemas" / "emotion_pipeline.schema.json"
    assert schema_path.exists(), f"Schema not found: {schema_path}"

    with open(schema_path) as f:
        schema = json.load(f)

    required_keys = set(schema.get("required", []))
    expected = {
        "session_id", "timestamp", "edition", "emotional_target",
        "density_map", "pressure_zones", "geometry_hints",
        "cad_directives", "simulation_profile", "warnings",
        "raw_payload_json",
    }

    missing = expected - required_keys
    assert not missing, f"Schema missing required keys: {missing}"


# ──────────────────────────────────────────────────────────────────────
# 6. لا يقبل payload ناقص
# ──────────────────────────────────────────────────────────────────────

def test_reject_incomplete_payload():
    """Missing required keys raise InvalidPayloadError."""
    db = _tmp_db()
    try:
        session = EmotionSession(db_path=db)

        # Missing "validation" — required key
        bad_payload = {
            "pipeline_status": "success",
            "selected_edition": "CALM",
            "edition_profile": {},
            # zone_geometry missing
            # validation missing
        }

        try:
            session.save(bad_payload)
            assert False, "Expected InvalidPayloadError for incomplete payload"
        except InvalidPayloadError as exc:
            assert "validation" in str(exc).lower() or "zone_geometry" in str(exc).lower(), (
                f"Error message should mention missing keys: {exc}"
            )
    finally:
        os.unlink(db)

"""
Tests for ZILFIT Emotion Session Layer (SQLite persistence).

6 tests:
  1. إنشاء قاعدة البيانات          — DB + table auto-created
  2. حفظ جلسة CALM                  — save a CALM session
  3. حفظ جلسة hybrid                — save a hybrid session
  4. قراءة آخر جلسة                 — read the latest session
  5. schema يحتوي المفاتيح المطلوبة — schema has all required keys
  6. لا يقبل payload ناقص           — rejects incomplete payload
"""

from __future__ import annotations

import json
import uuid
from datetime import datetime, timezone
from pathlib import Path

import pytest

from runtime.zilfit_emotion_session import (
    build_session_payload,
    get_latest_session,
    get_session,
    init_db,
    load_schema,
    save_session,
    validate_schema_keys,
    _REQUIRED_PAYLOAD_KEYS,
)

# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def tmp_db(tmp_path: Path) -> Path:
    """Return a temporary SQLite DB path."""
    db = tmp_path / "test_experiments.db"
    return db


@pytest.fixture
def calm_payload() -> dict:
    """A complete CALM session payload."""
    return build_session_payload(
        edition="p01_balance",
        emotional_target="CALM",
        density_map={"heel": 0.35, "arch": 0.22, "forefoot": 0.30},
        pressure_zones={
            "heel": {"force_kPa": 150, "status": "nominal"},
            "arch": {"force_kPa": 80, "status": "low"},
        },
        geometry_hints={"wall_thickness_mm": 0.6, "cell_size_mm": 6.0},
        cad_directives=["use_gyroid", "tpu_75a"],
        simulation_profile={"load_case": "static_stand", "max_stress_MPa": 0.9},
        warnings=[],
    )


@pytest.fixture
def hybrid_payload() -> dict:
    """A complete hybrid (CALM + DYNAMIC) session payload."""
    return build_session_payload(
        edition="p02_hybrid",
        emotional_target="CALM_DYNAMIC",
        density_map={
            "heel": 0.40,
            "arch": 0.28,
            "forefoot": 0.35,
        },
        pressure_zones={
            "heel": {"force_kPa": 170, "status": "high"},
            "arch": {"force_kPa": 95, "status": "nominal"},
            "forefoot": {"force_kPa": 120, "status": "nominal"},
        },
        geometry_hints={
            "wall_thickness_mm": 0.6,
            "cell_size_mm": 5.5,
            "transition_zones": ["lateral_arch"],
        },
        cad_directives=["use_gyroid", "tpu_80a", "hybrid_blend"],
        simulation_profile={
            "load_cases": ["static_stand", "slow_walk"],
            "max_stress_MPa": 0.85,
        },
        warnings=["hybrid transition not yet validated"],
    )


# ---------------------------------------------------------------------------
# Test 1 — إنشاء قاعدة البيانات
# ---------------------------------------------------------------------------
class TestInitDB:
    """DB + emotion_sessions table are created automatically."""

    def test_db_and_table_created(self, tmp_db: Path):
        assert not tmp_db.exists()
        db_path = init_db(tmp_db)
        assert db_path == tmp_db
        assert tmp_db.exists()

        # Verify the table exists via sqlite3
        import sqlite3
        conn = sqlite3.connect(str(tmp_db))
        cursor = conn.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name='emotion_sessions'"
        )
        rows = cursor.fetchall()
        conn.close()
        assert len(rows) == 1
        assert rows[0][0] == "emotion_sessions"


# ---------------------------------------------------------------------------
# Test 2 — حفظ جلسة CALM
# ---------------------------------------------------------------------------
class TestSaveCALM:
    """A CALM session is saved successfully."""

    def test_save_calm_session(self, tmp_db: Path, calm_payload: dict):
        sid = save_session(calm_payload, db_path=tmp_db)
        assert sid == calm_payload["session_id"]

        # Verify row exists
        session = get_session(sid, db_path=tmp_db)
        assert session is not None
        assert session["edition"] == "p01_balance"
        assert session["emotional_target"] == "CALM"

        # JSON fields deserialized
        assert isinstance(session["density_map"], dict)
        assert session["density_map"]["heel"] == pytest.approx(0.35)
        assert session["pressure_zones"]["heel"]["force_kPa"] == 150


# ---------------------------------------------------------------------------
# Test 3 — حفظ جلسة hybrid
# ---------------------------------------------------------------------------
class TestSaveHybrid:
    """A hybrid session is saved successfully."""

    def test_save_hybrid_session(self, tmp_db: Path, hybrid_payload: dict):
        sid = save_session(hybrid_payload, db_path=tmp_db)
        assert sid == hybrid_payload["session_id"]

        session = get_session(sid, db_path=tmp_db)
        assert session is not None
        assert session["edition"] == "p02_hybrid"
        assert session["emotional_target"] == "CALM_DYNAMIC"

        # Complex nested structures preserved
        geo = session["geometry_hints"]
        assert geo["cell_size_mm"] == 5.5
        assert "lateral_arch" in geo["transition_zones"]
        assert session["warnings"] == ["hybrid transition not yet validated"]


# ---------------------------------------------------------------------------
# Test 4 — قراءة آخر جلسة
# ---------------------------------------------------------------------------
class TestLatestSession:
    """Reading the latest session returns the most recent entry."""

    def test_get_latest_session(self, tmp_db: Path, calm_payload: dict, hybrid_payload: dict):
        import time

        # Save CALM first
        save_session(calm_payload, db_path=tmp_db)
        time.sleep(0.05)

        # Save hybrid second (should be latest)
        save_session(hybrid_payload, db_path=tmp_db)

        latest = get_latest_session(db_path=tmp_db)
        assert latest is not None
        assert latest["session_id"] == hybrid_payload["session_id"]
        assert latest["emotional_target"] == "CALM_DYNAMIC"


# ---------------------------------------------------------------------------
# Test 5 — schema يحتوي المفاتيح المطلوبة
# ---------------------------------------------------------------------------
class TestSchemaKeys:
    """The JSON schema contains all required payload keys."""

    def test_schema_has_required_keys(self):
        schema = load_schema()
        assert schema != {}, "Expected emotion_pipeline.schema.json to exist"

        required_in_schema = set(schema.get("required", []))
        assert _REQUIRED_PAYLOAD_KEYS.issubset(required_in_schema), (
            f"Missing from schema: {_REQUIRED_PAYLOAD_KEYS - required_in_schema}"
        )

        # Also validate via helper
        assert validate_schema_keys(schema) is True


# ---------------------------------------------------------------------------
# Test 6 — لا يقبل payload ناقص
# ---------------------------------------------------------------------------
class TestRejectIncomplete:
    """save_session rejects payloads missing required keys."""

    def test_rejects_incomplete_payload(self, tmp_db: Path):
        # Missing critical fields
        incomplete = {
            "session_id": str(uuid.uuid4()),
            "timestamp": datetime.now(timezone.utc).isoformat(),
            # edition missing
            # emotional_target missing
            # density_map missing
            # pressure_zones missing
            # geometry_hints missing
            # cad_directives missing
            # simulation_profile missing
            # warnings missing
            # raw_payload_json missing
        }

        with pytest.raises(ValueError, match="Missing required payload keys"):
            save_session(incomplete, db_path=tmp_db)

#!/usr/bin/env python3
"""ZILFIT Emotion Session Layer — SQLite persistence.

Stores every emotion-pipeline run in a local SQLite database so that
sessions can be queried, compared, and audited later.

Usage:
    from runtime.zilfit_emotion_session import EmotionSession

    session = EmotionSession(db_path="learning/experiments.db")
    session.save(pipeline_result, edition="CALM", payload=raw_dict)
    latest = session.get_latest()
"""

from __future__ import annotations

import json
import sqlite3
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional


# ── Database schema ───────────────────────────────────────────────────
_CREATE_SESSIONS_TABLE = """
CREATE TABLE IF NOT EXISTS emotion_sessions (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    session_id      TEXT    NOT NULL UNIQUE,
    timestamp       TEXT    NOT NULL,
    edition         TEXT    NOT NULL,
    emotional_target TEXT   NOT NULL DEFAULT '',
    density_map     TEXT    NOT NULL DEFAULT '{}',
    pressure_zones  TEXT    NOT NULL DEFAULT '[]',
    geometry_hints  TEXT    NOT NULL DEFAULT '{}',
    cad_directives  TEXT    NOT NULL DEFAULT '{}',
    simulation_profile TEXT NOT NULL DEFAULT '{}',
    warnings        TEXT    NOT NULL DEFAULT '[]',
    raw_payload_json TEXT   NOT NULL
);
"""

# Required keys for payload validation
_REQUIRED_PAYLOAD_KEYS = {
    "pipeline_status",
    "selected_edition",
    "edition_profile",
    "zone_geometry",
    "validation",
}


def _default_db_path() -> Path:
    """Return the default experiments.db path, creating parent dirs."""
    root = Path(__file__).resolve().parent.parent
    db = root / "learning" / "experiments.db"
    db.parent.mkdir(parents=True, exist_ok=True)
    return db


def _connect(db_path: Optional[str | Path] = None) -> sqlite3.Connection:
    """Open a connection and ensure the sessions table exists."""
    p = Path(db_path) if db_path else _default_db_path()
    p.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(p))
    conn.row_factory = sqlite3.Row
    conn.execute(_CREATE_SESSIONS_TABLE)
    conn.commit()
    return conn


class InvalidPayloadError(Exception):
    """Raised when a pipeline payload is missing required keys."""


class EmotionSession:
    """Persist and query ZILFIT emotion-pipeline sessions."""

    def __init__(self, db_path: Optional[str | Path] = None):
        self.db_path = db_path or _default_db_path()

    # ── Public API ─────────────────────────────────────────────────

    def save(
        self,
        pipeline_result: Dict[str, Any],
        raw_payload: Optional[Dict[str, Any]] = None,
    ) -> str:
        """Save a pipeline run result to SQLite.

        Args:
            pipeline_result: Structured result from EmotionPipeline.run().
            raw_payload: Optional original dict for raw_payload_json column.

        Returns:
            The session_id string.

        Raises:
            InvalidPayloadError: If the payload is missing required keys.
        """
        self._validate_payload(pipeline_result)

        session_id = str(uuid.uuid4())
        ts = datetime.now(timezone.utc).isoformat()

        edition = pipeline_result.get("selected_edition", "UNKNOWN")
        edition_profile = pipeline_result.get("edition_profile", {})
        foot_zones = edition_profile.get("foot_zones", {})
        density_map = {z: foot_zones[z].get("density", 0.30) for z in foot_zones}

        zone_geometry = pipeline_result.get("zone_geometry", {})
        pressure_zones = zone_geometry.get("active_zones", [])
        geometry_hints = zone_geometry.get("zone_geometry_hints", {})

        cad_directives = {
            "stimulation_type": edition_profile.get(
                "stimulation_profile", {}
            ).get("type", "unknown"),
            "intensity": edition_profile.get(
                "stimulation_profile", {}
            ).get("intensity", "unknown"),
            "coverage_percent": edition_profile.get(
                "stimulation_profile", {}
            ).get("coverage_percent", 0),
        }

        simulation_profile = edition_profile.get("stimulation_profile", {})
        validation = pipeline_result.get("validation", {})
        warnings = validation.get("warnings", [])

        emotional_target = edition_profile.get(
            "reflexology_inspired_zones", {}
        ).get(
            "primary_zone",
            edition_profile.get("intended_effect", ""),
        )

        if raw_payload is None:
            raw_payload = pipeline_result
        raw_json = json.dumps(raw_payload, ensure_ascii=False)

        with _connect(self.db_path) as conn:
            conn.execute(
                """
                INSERT INTO emotion_sessions (
                    session_id, timestamp, edition, emotional_target,
                    density_map, pressure_zones, geometry_hints,
                    cad_directives, simulation_profile, warnings,
                    raw_payload_json
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    session_id,
                    ts,
                    edition,
                    emotional_target,
                    json.dumps(density_map),
                    json.dumps(pressure_zones),
                    json.dumps(geometry_hints),
                    json.dumps(cad_directives),
                    json.dumps(simulation_profile),
                    json.dumps(warnings),
                    raw_json,
                ),
            )
            conn.commit()

        return session_id

    def get_latest(self, edition: Optional[str] = None) -> Optional[Dict[str, Any]]:
        """Return the most recent session, optionally filtered by edition."""
        with _connect(self.db_path) as conn:
            if edition:
                row = conn.execute(
                    "SELECT * FROM emotion_sessions WHERE edition = ? ORDER BY id DESC LIMIT 1",
                    (edition,),
                ).fetchone()
            else:
                row = conn.execute(
                    "SELECT * FROM emotion_sessions ORDER BY id DESC LIMIT 1"
                ).fetchone()

        if row is None:
            return None

        return self._row_to_dict(row)

    def get_all(self, limit: int = 100) -> List[Dict[str, Any]]:
        """Return up to *limit* recent sessions."""
        with _connect(self.db_path) as conn:
            rows = conn.execute(
                "SELECT * FROM emotion_sessions ORDER BY id DESC LIMIT ?",
                (limit,),
            ).fetchall()

        return [self._row_to_dict(r) for r in rows]

    def count(self) -> int:
        """Return total number of stored sessions."""
        with _connect(self.db_path) as conn:
            row = conn.execute("SELECT COUNT(*) AS c FROM emotion_sessions").fetchone()
            return row["c"] if row else 0

    def table_exists(self) -> bool:
        """Check whether the emotion_sessions table exists."""
        with _connect(self.db_path) as conn:
            row = conn.execute(
                """
                SELECT name FROM sqlite_master
                WHERE type='table' AND name='emotion_sessions'
                """
            ).fetchone()
            return row is not None

    # ── Internal helpers ────────────────────────────────────────────

    @staticmethod
    def _validate_payload(payload: Dict[str, Any]) -> None:
        """Raise InvalidPayloadError if required keys are missing."""
        missing = _REQUIRED_PAYLOAD_KEYS - set(payload.keys())
        if missing:
            raise InvalidPayloadError(
                f"Payload missing required keys: {sorted(missing)}"
            )

    @staticmethod
    def _row_to_dict(row: sqlite3.Row) -> Dict[str, Any]:
        """Convert a DB row into a clean dict, deserialising JSON fields."""
        d = dict(row)
        for json_col in (
            "density_map",
            "pressure_zones",
            "geometry_hints",
            "cad_directives",
            "simulation_profile",
            "warnings",
            "raw_payload_json",
        ):
            try:
                d[json_col] = json.loads(d[json_col]) if d[json_col] else {}
            except (json.JSONDecodeError, TypeError):
                d[json_col] = {}
        return d

"""
ZILFIT Emotion Session Layer — SQLite Persistence

Saves every emotion-pipeline session to a local SQLite database.
Auto-creates tables if they do not exist.

Storage: learning/experiments.db
"""

from __future__ import annotations

import json
import sqlite3
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------
_PROJECT_ROOT = Path(__file__).resolve().parent.parent
_DB_DIR = _PROJECT_ROOT / "learning"
_DB_PATH = _DB_DIR / "experiments.db"

# ---------------------------------------------------------------------------
# Schema
# ---------------------------------------------------------------------------
_SCHEMA_PATH = _PROJECT_ROOT / "schemas" / "emotion_pipeline.schema.json"

_REQUIRED_PAYLOAD_KEYS = {
    "session_id",
    "timestamp",
    "edition",
    "emotional_target",
    "density_map",
    "pressure_zones",
    "geometry_hints",
    "cad_directives",
    "simulation_profile",
    "warnings",
    "raw_payload_json",
}

# ---------------------------------------------------------------------------
# SQLite helpers
# ---------------------------------------------------------------------------
_TABLE = "emotion_sessions"

_CREATE_TABLE_SQL = f"""
CREATE TABLE IF NOT EXISTS {_TABLE} (
    session_id    TEXT PRIMARY KEY,
    timestamp     TEXT NOT NULL,
    edition       TEXT NOT NULL,
    emotional_target TEXT NOT NULL,
    density_map   TEXT,
    pressure_zones TEXT,
    geometry_hints TEXT,
    cad_directives TEXT,
    simulation_profile TEXT,
    warnings      TEXT,
    raw_payload_json TEXT NOT NULL
);
"""


def _get_connection(db_path: Path | None = None) -> sqlite3.Connection:
    """Return a connection, creating the database directory if needed."""
    target = db_path or _DB_PATH
    target.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(target))
    conn.row_factory = sqlite3.Row
    return conn


def _ensure_table(conn: sqlite3.Connection) -> None:
    conn.execute(_CREATE_TABLE_SQL)
    conn.commit()


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------
def init_db(db_path: Path | None = None) -> Path:
    """Create the database and tables. Returns the database path."""
    conn = _get_connection(db_path)
    try:
        _ensure_table(conn)
    finally:
        conn.close()
    return db_path or _DB_PATH


def save_session(
    payload: Dict[str, Any],
    db_path: Path | None = None,
) -> str:
    """Save an emotion session to SQLite.

    Accepts a dict that must contain all required keys.
    Returns the session_id.

    Raises ValueError if required keys are missing.
    """
    missing = _REQUIRED_PAYLOAD_KEYS - set(payload.keys())
    if missing:
        raise ValueError(f"Missing required payload keys: {sorted(missing)}")

    session_id = payload["session_id"]
    density_map = json.dumps(payload["density_map"], ensure_ascii=False) if payload["density_map"] is not None else None
    pressure_zones = json.dumps(payload["pressure_zones"], ensure_ascii=False) if payload["pressure_zones"] is not None else None
    geometry_hints = json.dumps(payload["geometry_hints"], ensure_ascii=False) if payload["geometry_hints"] is not None else None
    cad_directives = json.dumps(payload["cad_directives"], ensure_ascii=False) if payload["cad_directives"] is not None else None
    simulation_profile = json.dumps(payload["simulation_profile"], ensure_ascii=False) if payload["simulation_profile"] is not None else None
    warnings = json.dumps(payload["warnings"], ensure_ascii=False) if payload["warnings"] is not None else None
    raw_payload_json = json.dumps(payload, ensure_ascii=False, default=str)

    conn = _get_connection(db_path)
    try:
        _ensure_table(conn)
        conn.execute(
            f"""INSERT OR REPLACE INTO {_TABLE}
               (session_id, timestamp, edition, emotional_target,
                density_map, pressure_zones, geometry_hints,
                cad_directives, simulation_profile, warnings,
                raw_payload_json)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (
                session_id,
                payload["timestamp"],
                payload["edition"],
                payload["emotional_target"],
                density_map,
                pressure_zones,
                geometry_hints,
                cad_directives,
                simulation_profile,
                warnings,
                raw_payload_json,
            ),
        )
        conn.commit()
    finally:
        conn.close()

    return session_id


def get_latest_session(
    db_path: Path | None = None,
) -> Optional[Dict[str, Any]]:
    """Return the most recently saved session as a dict, or None."""
    conn = _get_connection(db_path)
    try:
        _ensure_table(conn)
        row = conn.execute(
            f"SELECT * FROM {_TABLE} ORDER BY timestamp DESC LIMIT 1"
        ).fetchone()
        if row is None:
            return None

        result: Dict[str, Any] = dict(row)
        # Deserialize JSON fields back into native types
        for key in ("density_map", "pressure_zones", "geometry_hints",
                     "cad_directives", "simulation_profile", "warnings",
                     "raw_payload_json"):
            val = result.get(key)
            if val is not None:
                result[key] = json.loads(val)
        return result
    finally:
        conn.close()


def get_session(
    session_id: str,
    db_path: Path | None = None,
) -> Optional[Dict[str, Any]]:
    """Return a single session by ID, or None."""
    conn = _get_connection(db_path)
    try:
        _ensure_table(conn)
        row = conn.execute(
            f"SELECT * FROM {_TABLE} WHERE session_id = ?", (session_id,)
        ).fetchone()
        if row is None:
            return None
        result: Dict[str, Any] = dict(row)
        for key in ("density_map", "pressure_zones", "geometry_hints",
                     "cad_directives", "simulation_profile", "warnings",
                     "raw_payload_json"):
            val = result.get(key)
            if val is not None:
                result[key] = json.loads(val)
        return result
    finally:
        conn.close()


def list_sessions(db_path: Path | None = None) -> List[Dict[str, str]]:
    """Return a list of {session_id, timestamp, edition, emotional_target}."""
    conn = _get_connection(db_path)
    try:
        _ensure_table(conn)
        rows = conn.execute(
            f"SELECT session_id, timestamp, edition, emotional_target "
            f"FROM {_TABLE} ORDER BY timestamp DESC"
        ).fetchall()
        return [dict(r) for r in rows]
    finally:
        conn.close()


# ---------------------------------------------------------------------------
# Schema validation
# ---------------------------------------------------------------------------
def load_schema() -> Dict[str, Any]:
    """Load the emotion_pipeline JSON schema."""
    if _SCHEMA_PATH.exists():
        with open(_SCHEMA_PATH, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}


def validate_schema_keys(schema: Dict[str, Any] | None = None) -> bool:
    """Check that the schema covers all required payload keys."""
    if schema is None:
        schema = load_schema()
    if not schema:
        return False
    props = set(schema.get("properties", {}).keys())
    return _REQUIRED_PAYLOAD_KEYS.issubset(props)


# ---------------------------------------------------------------------------
# Convenience: build a session payload dict
# ---------------------------------------------------------------------------
def build_session_payload(
    edition: str,
    emotional_target: str,
    density_map: Any = None,
    pressure_zones: Any = None,
    geometry_hints: Any = None,
    cad_directives: Any = None,
    simulation_profile: Any = None,
    warnings: List[str] | None = None,
) -> Dict[str, Any]:
    """Build a complete payload dict ready for save_session()."""
    return {
        "session_id": str(uuid.uuid4()),
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "edition": edition,
        "emotional_target": emotional_target,
        "density_map": density_map,
        "pressure_zones": pressure_zones,
        "geometry_hints": geometry_hints,
        "cad_directives": cad_directives,
        "simulation_profile": simulation_profile,
        "warnings": warnings or [],
        "raw_payload_json": "",  # filled during save
    }

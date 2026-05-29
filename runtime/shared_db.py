"""ZILFIT Shared Database Foundation.

Minimal SQLite-backed agent task registry so future ZILFIT agents can
record their work.  Designed to be importable from any agent script.

Schema columns:
  agent_name, task_id, status, summary, created_at, updated_at,
  risk_level, next_action

Usage:
    from runtime.shared_db import SharedDB

    db = SharedDB()                              # uses ./runtime/zilfit_shared.db
    db.upsert(
        agent_name="Z-Bio",
        task_id="bio-001",
        status="completed",
        summary="Collected heel pressure data",
        risk_level="low",
        next_action="Z-Design review",
    )
    rows = db.list_by_agent("Z-Bio")
"""

import os
import sqlite3
from datetime import datetime, timezone

_DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "zilfit_shared.db")

_SCHEMA = """\
CREATE TABLE IF NOT EXISTS agent_tasks (
    id            INTEGER PRIMARY KEY AUTOINCREMENT,
    agent_name    TEXT    NOT NULL,
    task_id       TEXT    NOT NULL,
    status        TEXT    NOT NULL DEFAULT 'pending',
    summary       TEXT    DEFAULT '',
    created_at    TEXT    NOT NULL,
    updated_at    TEXT    NOT NULL,
    risk_level    TEXT    DEFAULT 'low',
    next_action   TEXT    DEFAULT '',
    UNIQUE(agent_name, task_id)
);
"""

_VALID_STATUSES = {"pending", "in_progress", "completed", "blocked", "cancelled"}
_VALID_RISKS = {"low", "medium", "high", "critical"}


class SharedDB:
    """Thread-unsafe, file-local SQLite store for agent task records."""

    def __init__(self, db_path: str | None = None):
        self._path = db_path or _DB_PATH
        self._init()

    # -- private ---------------------------------------------------------------

    def _conn(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self._path)
        conn.execute("PRAGMA journal_mode=WAL")
        return conn

    def _init(self) -> None:
        with self._conn() as conn:
            conn.execute(_SCHEMA)

    # -- public ----------------------------------------------------------------

    def upsert(
        self,
        *,
        agent_name: str,
        task_id: str,
        status: str = "pending",
        summary: str = "",
        risk_level: str = "low",
        next_action: str = "",
    ) -> dict:
        """Insert or update a single agent task record. Returns the record dict."""
        if status not in _VALID_STATUSES:
            raise ValueError(f"Invalid status '{status}'. Must be one of {_VALID_STATUSES}")
        if risk_level not in _VALID_RISKS:
            raise ValueError(
                f"Invalid risk_level '{risk_level}'. Must be one of {_VALID_RISKS}"
            )

        now = datetime.now(timezone.utc).isoformat()

        with self._conn() as conn:
            cursor = conn.execute(
                """
                INSERT INTO agent_tasks
                    (agent_name, task_id, status, summary, created_at, updated_at,
                     risk_level, next_action)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(agent_name, task_id) DO UPDATE SET
                    status = excluded.status,
                    summary = excluded.summary,
                    updated_at = excluded.updated_at,
                    risk_level = excluded.risk_level,
                    next_action = excluded.next_action
                """,
                (agent_name, task_id, status, summary, now, now, risk_level, next_action),
            )
            # Re-fetch to get the final row (covers both insert and update)
            row = conn.execute(
                "SELECT * FROM agent_tasks WHERE agent_name=? AND task_id=?",
                (agent_name, task_id),
            ).fetchone()
            if row is None:
                raise RuntimeError("upsert succeeded but row not found")

        return self._row_to_dict(row)

    def get(self, *, agent_name: str, task_id: str) -> dict | None:
        row = self._conn().execute(
            "SELECT * FROM agent_tasks WHERE agent_name=? AND task_id=?",
            (agent_name, task_id),
        ).fetchone()
        return self._row_to_dict(row) if row else None

    def list_by_agent(self, agent_name: str) -> list[dict]:
        rows = self._conn().execute(
            "SELECT * FROM agent_tasks WHERE agent_name=? ORDER BY created_at DESC",
            (agent_name,),
        ).fetchall()
        return [self._row_to_dict(r) for r in rows]

    def list_by_status(self, status: str) -> list[dict]:
        rows = self._conn().execute(
            "SELECT * FROM agent_tasks WHERE status=? ORDER BY updated_at DESC",
            (status,),
        ).fetchall()
        return [self._row_to_dict(r) for r in rows]

    def list_all(self) -> list[dict]:
        rows = self._conn().execute(
            "SELECT * FROM agent_tasks ORDER BY updated_at DESC"
        ).fetchall()
        return [self._row_to_dict(r) for r in rows]

    def count(self) -> int:
        row = self._conn().execute("SELECT COUNT(*) FROM agent_tasks").fetchone()
        return row[0]

    @staticmethod
    def _row_to_dict(row: sqlite3.Row | tuple) -> dict:
        if row is None:
            return {}
        return {
            "id": row[0],
            "agent_name": row[1],
            "task_id": row[2],
            "status": row[3],
            "summary": row[4],
            "created_at": row[5],
            "updated_at": row[6],
            "risk_level": row[7],
            "next_action": row[8],
        }

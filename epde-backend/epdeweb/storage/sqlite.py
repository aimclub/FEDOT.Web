"""SQLite-backed persistence for EPDE.Web.

Everything stored here is document-shaped -- grid descriptions, run
configurations, discovered systems of equations -- so it lives as JSON in a
handful of tables. A connection is opened per operation; with WAL that is cheap
and avoids the thread-affinity rules SQLite imposes on connections shared
between FastAPI's worker threads.
"""

from __future__ import annotations

import json
import sqlite3
import uuid
from collections.abc import Iterator
from contextlib import contextmanager
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

SCHEMA = """
CREATE TABLE IF NOT EXISTS datasets (
    uid          TEXT PRIMARY KEY,
    name         TEXT NOT NULL,
    filename     TEXT NOT NULL,
    kind         TEXT NOT NULL,
    variables    TEXT NOT NULL,
    axes         TEXT NOT NULL,
    shape        TEXT NOT NULL,
    origin       TEXT,
    note         TEXT,
    created_at   TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS runs (
    uid          TEXT PRIMARY KEY,
    name         TEXT NOT NULL,
    dataset_uid  TEXT,
    config       TEXT NOT NULL,
    status       TEXT NOT NULL,
    error        TEXT,
    objectives   TEXT,
    best_system  TEXT,
    created_at   TEXT NOT NULL,
    started_at   TEXT,
    finished_at  TEXT
);

CREATE TABLE IF NOT EXISTS run_events (
    id           INTEGER PRIMARY KEY AUTOINCREMENT,
    run_uid      TEXT NOT NULL,
    created_at   TEXT NOT NULL,
    kind         TEXT NOT NULL,
    payload      TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS systems (
    uid          TEXT PRIMARY KEY,
    name         TEXT NOT NULL,
    run_uid      TEXT,
    origin       TEXT,
    graph        TEXT NOT NULL,
    created_at   TEXT NOT NULL,
    updated_at   TEXT NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_run_events_run ON run_events (run_uid, id);
CREATE INDEX IF NOT EXISTS idx_systems_run ON systems (run_uid);
"""


def utcnow() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def new_uid() -> str:
    return uuid.uuid4().hex


class Store:
    """Thin persistence layer over SQLite."""

    def __init__(self, path: Path) -> None:
        self._path = path
        self._path.parent.mkdir(parents=True, exist_ok=True)
        with self._connect() as conn:
            conn.executescript(SCHEMA)

    @contextmanager
    def _connect(self) -> Iterator[sqlite3.Connection]:
        conn = sqlite3.connect(self._path, timeout=30.0)
        conn.row_factory = sqlite3.Row
        try:
            conn.execute("PRAGMA journal_mode=WAL")
            conn.execute("PRAGMA foreign_keys=ON")
            yield conn
            conn.commit()
        except Exception:
            conn.rollback()
            raise
        finally:
            conn.close()

    # ----------------------------------------------------------------- datasets

    def save_dataset(self, record: dict[str, Any]) -> str:
        uid = record.get("uid") or new_uid()
        with self._connect() as conn:
            conn.execute(
                """
                INSERT OR REPLACE INTO datasets
                    (uid, name, filename, kind, variables, axes, shape, origin, note, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    uid,
                    record["name"],
                    record["filename"],
                    record.get("kind", "field"),
                    json.dumps(record.get("variables", []), ensure_ascii=False),
                    json.dumps(record.get("axes", []), ensure_ascii=False),
                    json.dumps(record.get("shape", []), ensure_ascii=False),
                    record.get("origin"),
                    record.get("note"),
                    record.get("created_at") or utcnow(),
                ),
            )
        return uid

    def get_dataset(self, uid: str) -> dict[str, Any] | None:
        with self._connect() as conn:
            row = conn.execute("SELECT * FROM datasets WHERE uid = ?", (uid,)).fetchone()
        return self._dataset_row(row) if row else None

    def list_datasets(self) -> list[dict[str, Any]]:
        with self._connect() as conn:
            rows = conn.execute("SELECT * FROM datasets ORDER BY datetime(created_at) DESC").fetchall()
        return [self._dataset_row(row) for row in rows]

    def find_dataset_by_origin(self, origin: str) -> dict[str, Any] | None:
        with self._connect() as conn:
            row = conn.execute(
                "SELECT * FROM datasets WHERE origin = ? ORDER BY datetime(created_at) LIMIT 1",
                (origin,),
            ).fetchone()
        return self._dataset_row(row) if row else None

    def delete_dataset(self, uid: str) -> bool:
        with self._connect() as conn:
            cursor = conn.execute("DELETE FROM datasets WHERE uid = ?", (uid,))
        return cursor.rowcount > 0

    @staticmethod
    def _dataset_row(row: sqlite3.Row) -> dict[str, Any]:
        return {
            "uid": row["uid"],
            "name": row["name"],
            "filename": row["filename"],
            "kind": row["kind"],
            "variables": json.loads(row["variables"]),
            "axes": json.loads(row["axes"]),
            "shape": json.loads(row["shape"]),
            "origin": row["origin"],
            "note": row["note"],
            "created_at": row["created_at"],
        }

    # --------------------------------------------------------------------- runs

    def create_run(self, *, name: str, dataset_uid: str | None, config: dict[str, Any]) -> str:
        uid = new_uid()
        with self._connect() as conn:
            conn.execute(
                """
                INSERT INTO runs (uid, name, dataset_uid, config, status, created_at)
                VALUES (?, ?, ?, ?, 'pending', ?)
                """,
                (uid, name, dataset_uid, json.dumps(config, ensure_ascii=False), utcnow()),
            )
        return uid

    def update_run(self, uid: str, **fields: Any) -> None:
        if not fields:
            return
        allowed = {"status", "error", "objectives", "best_system", "started_at", "finished_at"}
        assignments, params = [], []
        for key, value in fields.items():
            if key not in allowed:
                raise KeyError(f"Cannot update run field: {key}")
            assignments.append(f"{key} = ?")
            params.append(
                json.dumps(value, ensure_ascii=False) if isinstance(value, (dict, list)) else value
            )
        params.append(uid)
        with self._connect() as conn:
            conn.execute(f"UPDATE runs SET {', '.join(assignments)} WHERE uid = ?", params)

    def get_run(self, uid: str) -> dict[str, Any] | None:
        with self._connect() as conn:
            row = conn.execute("SELECT * FROM runs WHERE uid = ?", (uid,)).fetchone()
        return self._run_row(row) if row else None

    def list_runs(self, limit: int = 100) -> list[dict[str, Any]]:
        with self._connect() as conn:
            rows = conn.execute(
                "SELECT * FROM runs ORDER BY datetime(created_at) DESC LIMIT ?", (limit,)
            ).fetchall()
        return [self._run_row(row) for row in rows]

    def delete_run(self, uid: str) -> bool:
        with self._connect() as conn:
            conn.execute("DELETE FROM run_events WHERE run_uid = ?", (uid,))
            conn.execute("DELETE FROM systems WHERE run_uid = ?", (uid,))
            cursor = conn.execute("DELETE FROM runs WHERE uid = ?", (uid,))
        return cursor.rowcount > 0

    @staticmethod
    def _run_row(row: sqlite3.Row) -> dict[str, Any]:
        return {
            "uid": row["uid"],
            "name": row["name"],
            "dataset_uid": row["dataset_uid"],
            "config": json.loads(row["config"]),
            "status": row["status"],
            "error": row["error"],
            "objectives": json.loads(row["objectives"]) if row["objectives"] else None,
            "best_system": row["best_system"],
            "created_at": row["created_at"],
            "started_at": row["started_at"],
            "finished_at": row["finished_at"],
        }

    # ------------------------------------------------------------------ systems

    def save_system(
        self,
        *,
        graph: dict[str, Any],
        name: str,
        origin: str = "run",
        run_uid: str | None = None,
        uid: str | None = None,
    ) -> str:
        uid = uid or new_uid()
        now = utcnow()
        payload = json.dumps(graph, ensure_ascii=False, allow_nan=False)
        with self._connect() as conn:
            conn.execute(
                """
                INSERT INTO systems (uid, name, run_uid, origin, graph, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(uid) DO UPDATE SET
                    name = excluded.name,
                    graph = excluded.graph,
                    updated_at = excluded.updated_at
                """,
                (uid, name, run_uid, origin, payload, now, now),
            )
        return uid

    def get_system(self, uid: str) -> dict[str, Any] | None:
        with self._connect() as conn:
            row = conn.execute("SELECT * FROM systems WHERE uid = ?", (uid,)).fetchone()
        return self._system_row(row) if row else None

    def list_systems(self, *, run_uid: str | None = None, limit: int = 200) -> list[dict[str, Any]]:
        query = "SELECT * FROM systems"
        params: list[Any] = []
        if run_uid:
            query += " WHERE run_uid = ?"
            params.append(run_uid)
        query += " ORDER BY datetime(updated_at) DESC LIMIT ?"
        params.append(limit)
        with self._connect() as conn:
            rows = conn.execute(query, params).fetchall()
        return [self._system_row(row) for row in rows]

    def delete_system(self, uid: str) -> bool:
        with self._connect() as conn:
            cursor = conn.execute("DELETE FROM systems WHERE uid = ?", (uid,))
        return cursor.rowcount > 0

    @staticmethod
    def _system_row(row: sqlite3.Row) -> dict[str, Any]:
        return {
            "uid": row["uid"],
            "name": row["name"],
            "run_uid": row["run_uid"],
            "origin": row["origin"],
            "graph": json.loads(row["graph"]),
            "created_at": row["created_at"],
            "updated_at": row["updated_at"],
        }

    # --------------------------------------------------------------- run events

    def append_event(self, run_uid: str, kind: str, payload: dict[str, Any]) -> int:
        with self._connect() as conn:
            cursor = conn.execute(
                "INSERT INTO run_events (run_uid, created_at, kind, payload) VALUES (?, ?, ?, ?)",
                (run_uid, utcnow(), kind, json.dumps(payload, ensure_ascii=False, default=str)),
            )
        return int(cursor.lastrowid)

    def list_events(
        self,
        run_uid: str,
        *,
        after_id: int = 0,
        kinds: list[str] | None = None,
        limit: int = 5000,
    ) -> list[dict[str, Any]]:
        """Events for a run, oldest first.

        ``kinds`` narrows the query in SQL. A ``population`` event carries every
        candidate system in a generation and dwarfs everything else, so a caller
        that only wants the objective curves should not have to fetch and parse
        it.
        """
        query = "SELECT * FROM run_events WHERE run_uid = ? AND id > ?"
        params: list[Any] = [run_uid, after_id]
        if kinds:
            placeholders = ", ".join("?" * len(kinds))
            query += f" AND kind IN ({placeholders})"
            params.extend(kinds)
        query += " ORDER BY id LIMIT ?"
        params.append(limit)
        with self._connect() as conn:
            rows = conn.execute(query, params).fetchall()
        return [
            {
                "id": row["id"],
                "created_at": row["created_at"],
                "kind": row["kind"],
                "payload": json.loads(row["payload"]),
            }
            for row in rows
        ]

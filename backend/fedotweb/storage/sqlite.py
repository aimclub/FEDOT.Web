"""SQLite-backed persistence.

The data here is document-shaped (pipeline graphs, run configurations, evolution
histories), so it is stored as JSON in a handful of tables rather than through an
ORM.  A connection is opened per operation -- with WAL enabled that is cheap and
sidesteps the thread-affinity rules SQLite imposes on connections shared between
FastAPI's worker threads.
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
CREATE TABLE IF NOT EXISTS pipelines (
    uid          TEXT PRIMARY KEY,
    name         TEXT NOT NULL,
    task         TEXT,
    graph        TEXT NOT NULL,
    origin       TEXT,
    run_uid      TEXT,
    created_at   TEXT NOT NULL,
    updated_at   TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS datasets (
    uid          TEXT PRIMARY KEY,
    name         TEXT NOT NULL,
    filename     TEXT NOT NULL,
    task         TEXT,
    target       TEXT,
    n_rows       INTEGER,
    n_columns    INTEGER,
    columns      TEXT NOT NULL,
    created_at   TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS runs (
    uid          TEXT PRIMARY KEY,
    name         TEXT NOT NULL,
    dataset_uid  TEXT,
    config       TEXT NOT NULL,
    status       TEXT NOT NULL,
    error        TEXT,
    metrics      TEXT,
    best_pipeline TEXT,
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

CREATE TABLE IF NOT EXISTS analyses (
    uid          TEXT PRIMARY KEY,
    run_uid      TEXT NOT NULL,
    kind         TEXT NOT NULL,
    pipeline_uid TEXT,
    options      TEXT NOT NULL,
    status       TEXT NOT NULL,
    error        TEXT,
    result       TEXT,
    created_at   TEXT NOT NULL,
    finished_at  TEXT
);

CREATE INDEX IF NOT EXISTS idx_run_events_run ON run_events (run_uid, id);
CREATE INDEX IF NOT EXISTS idx_pipelines_run ON pipelines (run_uid);
CREATE INDEX IF NOT EXISTS idx_analyses_run ON analyses (run_uid, datetime(created_at));
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

    # ---------------------------------------------------------------- pipelines

    def save_pipeline(
        self,
        *,
        graph: dict[str, Any],
        name: str,
        task: str | None = None,
        origin: str = "editor",
        run_uid: str | None = None,
        uid: str | None = None,
    ) -> str:
        uid = uid or new_uid()
        now = utcnow()
        payload = json.dumps(graph, ensure_ascii=False, allow_nan=False)
        with self._connect() as conn:
            conn.execute(
                """
                INSERT INTO pipelines (uid, name, task, graph, origin, run_uid, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(uid) DO UPDATE SET
                    name = excluded.name,
                    task = excluded.task,
                    graph = excluded.graph,
                    updated_at = excluded.updated_at
                """,
                (uid, name, task, payload, origin, run_uid, now, now),
            )
        return uid

    def get_pipeline(self, uid: str) -> dict[str, Any] | None:
        with self._connect() as conn:
            row = conn.execute("SELECT * FROM pipelines WHERE uid = ?", (uid,)).fetchone()
        return self._pipeline_row(row) if row else None

    def list_pipelines(self, *, run_uid: str | None = None, limit: int = 200) -> list[dict[str, Any]]:
        query = "SELECT * FROM pipelines"
        params: list[Any] = []
        if run_uid:
            query += " WHERE run_uid = ?"
            params.append(run_uid)
        query += " ORDER BY datetime(updated_at) DESC LIMIT ?"
        params.append(limit)
        with self._connect() as conn:
            rows = conn.execute(query, params).fetchall()
        return [self._pipeline_row(row) for row in rows]

    def delete_pipeline(self, uid: str) -> bool:
        with self._connect() as conn:
            cursor = conn.execute("DELETE FROM pipelines WHERE uid = ?", (uid,))
        return cursor.rowcount > 0

    @staticmethod
    def _pipeline_row(row: sqlite3.Row) -> dict[str, Any]:
        graph = json.loads(row["graph"])
        return {
            "uid": row["uid"],
            "name": row["name"],
            "task": row["task"],
            "origin": row["origin"],
            "run_uid": row["run_uid"],
            "created_at": row["created_at"],
            "updated_at": row["updated_at"],
            "graph": graph,
            "length": graph.get("length", len(graph.get("nodes", []))),
            "depth": graph.get("depth", 0),
        }

    # ----------------------------------------------------------------- datasets

    def save_dataset(self, record: dict[str, Any]) -> str:
        uid = record.get("uid") or new_uid()
        with self._connect() as conn:
            conn.execute(
                """
                INSERT OR REPLACE INTO datasets
                    (uid, name, filename, task, target, n_rows, n_columns, columns, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    uid,
                    record["name"],
                    record["filename"],
                    record.get("task"),
                    record.get("target"),
                    record.get("n_rows"),
                    record.get("n_columns"),
                    json.dumps(record.get("columns", []), ensure_ascii=False),
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
            "task": row["task"],
            "target": row["target"],
            "n_rows": row["n_rows"],
            "n_columns": row["n_columns"],
            "columns": json.loads(row["columns"]),
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
        allowed = {"status", "error", "metrics", "best_pipeline", "started_at", "finished_at"}
        assignments, params = [], []
        for key, value in fields.items():
            if key not in allowed:
                raise KeyError(f"Cannot update run field: {key}")
            assignments.append(f"{key} = ?")
            params.append(json.dumps(value, ensure_ascii=False) if isinstance(value, (dict, list)) else value)
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
            conn.execute("DELETE FROM pipelines WHERE run_uid = ?", (uid,))
            conn.execute("DELETE FROM analyses WHERE run_uid = ?", (uid,))
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
            "metrics": json.loads(row["metrics"]) if row["metrics"] else None,
            "best_pipeline": row["best_pipeline"],
            "created_at": row["created_at"],
            "started_at": row["started_at"],
            "finished_at": row["finished_at"],
        }

    # ----------------------------------------------------------------- analyses

    def create_analysis(
        self, *, run_uid: str, kind: str, pipeline_uid: str | None, options: dict[str, Any]
    ) -> str:
        uid = new_uid()
        with self._connect() as conn:
            conn.execute(
                """
                INSERT INTO analyses (uid, run_uid, kind, pipeline_uid, options, status, created_at)
                VALUES (?, ?, ?, ?, ?, 'running', ?)
                """,
                (uid, run_uid, kind, pipeline_uid, json.dumps(options, ensure_ascii=False), utcnow()),
            )
        return uid

    def finish_analysis(
        self, uid: str, *, result: dict[str, Any] | None = None, error: str | None = None
    ) -> None:
        with self._connect() as conn:
            conn.execute(
                "UPDATE analyses SET status = ?, result = ?, error = ?, finished_at = ? WHERE uid = ?",
                (
                    "failed" if error else "finished",
                    json.dumps(result, ensure_ascii=False, default=str) if result else None,
                    error,
                    utcnow(),
                    uid,
                ),
            )

    def fail_running_analyses(self, reason: str) -> int:
        """Mark every analysis still 'running' as failed.

        Called at startup: an analysis worker is owned by the server process, so
        anything still marked running after a restart is definitionally dead --
        and would otherwise be polled by the UI forever.
        """
        with self._connect() as conn:
            cursor = conn.execute(
                "UPDATE analyses SET status = 'failed', error = ?, finished_at = ? "
                "WHERE status = 'running'",
                (reason, utcnow()),
            )
        return cursor.rowcount

    def get_analysis(self, uid: str) -> dict[str, Any] | None:
        with self._connect() as conn:
            row = conn.execute("SELECT * FROM analyses WHERE uid = ?", (uid,)).fetchone()
        return self._analysis_row(row) if row else None

    def list_analyses(self, run_uid: str) -> list[dict[str, Any]]:
        with self._connect() as conn:
            rows = conn.execute(
                "SELECT * FROM analyses WHERE run_uid = ? ORDER BY datetime(created_at) DESC",
                (run_uid,),
            ).fetchall()
        return [self._analysis_row(row) for row in rows]

    @staticmethod
    def _analysis_row(row: sqlite3.Row) -> dict[str, Any]:
        return {
            "uid": row["uid"],
            "run_uid": row["run_uid"],
            "kind": row["kind"],
            "pipeline_uid": row["pipeline_uid"],
            "options": json.loads(row["options"]),
            "status": row["status"],
            "error": row["error"],
            "result": json.loads(row["result"]) if row["result"] else None,
            "created_at": row["created_at"],
            "finished_at": row["finished_at"],
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

        ``kinds`` narrows the query in SQL. Population events carry whole
        pipelines and dwarf everything else, so a caller that only needs the
        fitness curve should not have to fetch and parse them.
        """
        query = "SELECT * FROM run_events WHERE run_uid = ? AND id > ?"
        params: list[Any] = [run_uid, after_id]
        if kinds:
            query += f" AND kind IN ({', '.join('?' * len(kinds))})"
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

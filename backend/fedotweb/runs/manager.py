"""Supervision of AutoML runs: spawning, progress fan-out and cancellation."""

from __future__ import annotations

import asyncio
import json
import os
import subprocess
import sys
from contextlib import suppress
from pathlib import Path
from typing import Any

from ..settings import Settings
from ..storage.sqlite import Store, utcnow
from .worker import CONFIG_FILE, EVENTS_FILE

#: Statuses a run can be in.  ``pending`` and ``running`` are the only live ones.
TERMINAL_STATUSES = frozenset({"finished", "failed", "cancelled"})

#: How often the event tail polls the worker's JSONL file.
POLL_INTERVAL_SECONDS = 0.4


class RunError(RuntimeError):
    """Raised when a run cannot be started or cancelled."""


class _Subscribers:
    """Fan-out of run events to any number of WebSocket listeners."""

    def __init__(self) -> None:
        self._queues: dict[str, set[asyncio.Queue]] = {}

    def add(self, run_uid: str) -> asyncio.Queue:
        queue: asyncio.Queue = asyncio.Queue(maxsize=1000)
        self._queues.setdefault(run_uid, set()).add(queue)
        return queue

    def remove(self, run_uid: str, queue: asyncio.Queue) -> None:
        listeners = self._queues.get(run_uid)
        if not listeners:
            return
        listeners.discard(queue)
        if not listeners:
            self._queues.pop(run_uid, None)

    def publish(self, run_uid: str, event: dict[str, Any]) -> None:
        for queue in list(self._queues.get(run_uid, ())):
            try:
                queue.put_nowait(event)
            except asyncio.QueueFull:
                # A listener that cannot keep up is dropped rather than allowed to
                # stall the run; the client can refetch the event log on reconnect.
                self.remove(run_uid, queue)


class RunManager:
    """Owns the worker processes and turns their output into stored events."""

    def __init__(self, store: Store, settings: Settings) -> None:
        self._store = store
        self._settings = settings
        self._processes: dict[str, subprocess.Popen] = {}
        self._tails: dict[str, asyncio.Task] = {}
        #: Runs the user stopped. A killed worker cannot write its own farewell
        #: event, so without this the tail would finalise them as failures.
        self._cancelled: set[str] = set()
        self._subscribers = _Subscribers()
        self._lock = asyncio.Lock()

    # ------------------------------------------------------------------ helpers

    def run_dir(self, run_uid: str) -> Path:
        return self._settings.runs_dir / run_uid

    @property
    def active_runs(self) -> list[str]:
        return [uid for uid, process in self._processes.items() if process.poll() is None]

    def is_running(self, run_uid: str) -> bool:
        process = self._processes.get(run_uid)
        return process is not None and process.poll() is None

    # -------------------------------------------------------------------- start

    async def start(self, run_uid: str, config: dict[str, Any]) -> None:
        async with self._lock:
            if self.is_running(run_uid):
                raise RunError(f"Run {run_uid} is already in progress")
            if len(self.active_runs) >= self._settings.max_concurrent_runs:
                raise RunError(
                    f"Too many runs in progress (limit is {self._settings.max_concurrent_runs}); "
                    "wait for one to finish or stop it"
                )

            directory = self.run_dir(run_uid)
            directory.mkdir(parents=True, exist_ok=True)
            (directory / CONFIG_FILE).write_text(
                json.dumps(config, ensure_ascii=False, indent=2), encoding="utf-8"
            )
            # A fresh event log per attempt keeps replay unambiguous.
            (directory / EVENTS_FILE).write_text("", encoding="utf-8")

            environment = os.environ.copy()
            # The worker imports ``fedotweb`` itself, so it must find the package.
            package_root = str(Path(__file__).resolve().parents[2])
            environment["PYTHONPATH"] = os.pathsep.join(
                filter(None, [package_root, environment.get("PYTHONPATH", "")])
            )
            environment["PYTHONUNBUFFERED"] = "1"

            log_file = (directory / "worker.log").open("w", encoding="utf-8")
            creation_flags = 0
            if sys.platform == "win32":
                # Own process group so that cancellation does not signal the API server.
                creation_flags = subprocess.CREATE_NEW_PROCESS_GROUP

            process = subprocess.Popen(
                [sys.executable, "-m", "fedotweb.runs.worker", str(directory)],
                cwd=package_root,
                env=environment,
                stdout=log_file,
                stderr=subprocess.STDOUT,
                creationflags=creation_flags,
                start_new_session=sys.platform != "win32",
            )
            self._processes[run_uid] = process

            self._store.update_run(run_uid, status="running", started_at=utcnow())
            self._tails[run_uid] = asyncio.create_task(self._tail(run_uid, log_file))

    # --------------------------------------------------------------------- tail

    async def _tail(self, run_uid: str, log_file: Any) -> None:
        """Stream the worker's event log into storage and to subscribers."""
        directory = self.run_dir(run_uid)
        events_path = directory / EVENTS_FILE
        offset = 0
        buffer = ""
        final_status = "failed"
        error_message: str | None = None

        try:
            while True:
                process = self._processes.get(run_uid)
                process_alive = process is not None and process.poll() is None

                if events_path.exists():
                    with events_path.open("r", encoding="utf-8") as handle:
                        handle.seek(offset)
                        chunk = handle.read()
                        offset = handle.tell()
                    buffer += chunk
                    lines = buffer.split("\n")
                    # The last element is a possibly-incomplete line; keep it buffered.
                    buffer = lines.pop()
                    for line in lines:
                        line = line.strip()
                        if not line:
                            continue
                        try:
                            event = json.loads(line)
                        except json.JSONDecodeError:
                            continue
                        kind = event.get("kind", "log")
                        payload = event.get("payload", {})
                        if kind == "finished":
                            final_status = "finished"
                        elif kind == "error":
                            final_status = "failed"
                            error_message = payload.get("message")
                        elif kind == "cancelled":
                            final_status = "cancelled"
                        self._record(run_uid, kind, payload, elapsed=event.get("elapsed"))

                # Stop only once the worker is gone *and* its log has been drained,
                # so the final event is never lost to a race with the exit.
                unread = events_path.exists() and offset < events_path.stat().st_size
                if not process_alive and not buffer and not unread:
                    break

                await asyncio.sleep(POLL_INTERVAL_SECONDS)

            await self._finalise(run_uid, final_status, error_message)
        except asyncio.CancelledError:
            raise
        except Exception as exc:  # noqa: BLE001 - the tail must never take down the server
            self._record(run_uid, "error", {"message": f"progress reader failed: {exc}"})
            await self._finalise(run_uid, "failed", str(exc))
        finally:
            with suppress(Exception):
                log_file.close()

    def _record(self, run_uid: str, kind: str, payload: dict[str, Any], elapsed: float | None = None) -> None:
        event_id = self._store.append_event(run_uid, kind, payload)
        self._subscribers.publish(
            run_uid, {"id": event_id, "kind": kind, "payload": payload, "elapsed": elapsed}
        )

    async def _finalise(self, run_uid: str, status: str, error: str | None) -> None:
        directory = self.run_dir(run_uid)

        if run_uid in self._cancelled:
            # A killed worker never gets to report its own outcome, so the tail
            # would otherwise record the user's stop as a failure.
            self._cancelled.discard(run_uid)
            status, error = "cancelled", None

        updates: dict[str, Any] = {"status": status, "finished_at": utcnow()}
        if error:
            updates["error"] = error

        result_path = directory / "result.json"
        if status == "finished" and result_path.exists():
            try:
                result = json.loads(result_path.read_text(encoding="utf-8"))
            except json.JSONDecodeError:
                result = {}
            if result.get("metrics"):
                updates["metrics"] = result["metrics"]
            best_graph = result.get("best_pipeline")
            if best_graph:
                run = self._store.get_run(run_uid) or {}
                pipeline_uid = self._store.save_pipeline(
                    graph=best_graph,
                    name=f"{run.get('name', 'run')} — best pipeline",
                    task=(run.get("config") or {}).get("problem"),
                    origin="automl",
                    run_uid=run_uid,
                )
                updates["best_pipeline"] = pipeline_uid

        self._store.update_run(run_uid, **updates)
        self._processes.pop(run_uid, None)
        # The tail task is about to return; dropping the reference here keeps the
        # dict from growing by one entry per run for the life of the server.
        self._tails.pop(run_uid, None)
        self._subscribers.publish(run_uid, {"kind": "run_status", "payload": updates})

    # ------------------------------------------------------------------- cancel

    async def cancel(self, run_uid: str) -> bool:
        process = self._processes.get(run_uid)
        if process is None or process.poll() is not None:
            return False

        self._cancelled.add(run_uid)
        _terminate_tree(process)
        self._record(run_uid, "cancelled", {"message": "Run cancelled by user"})
        # ``_tail`` notices the dead process and finalises; force the status here so
        # a slow poll cannot leave the run looking alive.
        self._store.update_run(run_uid, status="cancelled", finished_at=utcnow())
        return True

    async def shutdown(self) -> None:
        for run_uid in list(self._processes):
            with suppress(Exception):
                await self.cancel(run_uid)
        for task in list(self._tails.values()):
            task.cancel()
            with suppress(asyncio.CancelledError):
                await task
        self._tails.clear()

    # --------------------------------------------------------------- subscribe

    def subscribe(self, run_uid: str) -> asyncio.Queue:
        return self._subscribers.add(run_uid)

    def unsubscribe(self, run_uid: str, queue: asyncio.Queue) -> None:
        self._subscribers.remove(run_uid, queue)


def _terminate_tree(process: subprocess.Popen) -> None:
    """Kill the worker and anything it spawned.

    FEDOT starts its own worker processes when ``n_jobs > 1``; killing only the
    direct child would leave those running and holding the dataset open.
    """
    try:
        import psutil  # FEDOT depends on psutil, so it is always available.

        parent = psutil.Process(process.pid)
        children = parent.children(recursive=True)
        for child in children:
            with suppress(psutil.Error):
                child.terminate()
        psutil.wait_procs(children, timeout=5)
        for child in children:
            with suppress(psutil.Error):
                if child.is_running():
                    child.kill()
        with suppress(psutil.Error):
            parent.terminate()
            parent.wait(timeout=5)
        with suppress(psutil.Error):
            if parent.is_running():
                parent.kill()
    except Exception:
        # Fall back to the plain subprocess API if psutil is unavailable.
        with suppress(Exception):
            process.terminate()
        with suppress(Exception):
            process.wait(timeout=5)
        with suppress(Exception):
            process.kill()

"""Running on-demand analyses out of process and collecting their results."""

from __future__ import annotations

import asyncio
import json
import subprocess
import sys
from pathlib import Path
from typing import Any

from ..settings import Settings
from ..storage.sqlite import Store
from .worker import JOB_FILE, RESULT_FILE

#: An analysis refits a pipeline many times; this stops a pathological one from
#: holding a slot forever.
DEFAULT_TIMEOUT_SECONDS = 1800.0


class AnalysisError(RuntimeError):
    """Raised when an analysis cannot be started."""


class AnalysisManager:
    """Spawns analysis workers and writes their results back to the store."""

    def __init__(self, store: Store, settings: Settings) -> None:
        self._store = store
        self._settings = settings
        self._tasks: dict[str, asyncio.Task] = {}

    def job_dir(self, analysis_uid: str) -> Path:
        return self._settings.workspace / "analyses" / analysis_uid

    @property
    def active(self) -> int:
        return sum(1 for task in self._tasks.values() if not task.done())

    async def start(
        self,
        *,
        run_uid: str,
        kind: str,
        spec: dict[str, Any],
        pipeline_uid: str | None,
        options: dict[str, Any],
    ) -> str:
        if self.active >= self._settings.max_concurrent_runs:
            raise AnalysisError(
                f"Too many analyses in progress (limit is {self._settings.max_concurrent_runs})"
            )

        analysis_uid = self._store.create_analysis(
            run_uid=run_uid, kind=kind, pipeline_uid=pipeline_uid, options=options
        )
        directory = self.job_dir(analysis_uid)
        directory.mkdir(parents=True, exist_ok=True)
        (directory / JOB_FILE).write_text(
            json.dumps({**spec, "kind": kind}, ensure_ascii=False, default=str), encoding="utf-8"
        )

        self._tasks[analysis_uid] = asyncio.create_task(self._supervise(analysis_uid, directory))
        return analysis_uid

    async def _supervise(self, analysis_uid: str, directory: Path) -> None:
        package_root = str(Path(__file__).resolve().parents[2])
        log_file = (directory / "worker.log").open("w", encoding="utf-8")

        try:
            process = await asyncio.create_subprocess_exec(
                sys.executable,
                "-m",
                "fedotweb.analysis.worker",
                str(directory),
                cwd=package_root,
                stdout=log_file,
                stderr=subprocess.STDOUT,
            )
            try:
                await asyncio.wait_for(process.wait(), timeout=DEFAULT_TIMEOUT_SECONDS)
            except asyncio.TimeoutError:
                process.kill()
                await process.wait()
                self._store.finish_analysis(
                    analysis_uid,
                    error=f"The analysis exceeded {DEFAULT_TIMEOUT_SECONDS / 60:g} minutes and was stopped",
                )
                return

            payload = self._read_result(directory)
            if payload is None:
                self._store.finish_analysis(
                    analysis_uid, error="The analysis produced no result; see worker.log"
                )
            elif "error" in payload:
                self._store.finish_analysis(analysis_uid, error=payload["error"])
            else:
                self._store.finish_analysis(analysis_uid, result=payload["result"])
        except Exception as exc:  # noqa: BLE001 - a failed analysis must not take the server down
            self._store.finish_analysis(analysis_uid, error=f"{type(exc).__name__}: {exc}")
        finally:
            log_file.close()
            self._tasks.pop(analysis_uid, None)

    @staticmethod
    def _read_result(directory: Path) -> dict[str, Any] | None:
        path = directory / RESULT_FILE
        if not path.exists():
            return None
        try:
            return json.loads(path.read_text(encoding="utf-8"))
        except json.JSONDecodeError as exc:
            return {"error": f"The analysis wrote an unreadable result: {exc}"}

    async def shutdown(self) -> None:
        for task in list(self._tasks.values()):
            task.cancel()
        self._tasks.clear()

"""Watch a FEDOT run that you started yourself.

The rest of this package drives FEDOT from the browser. This module turns that
round: you keep your own script, and the GUI attaches to it -- the server starts
if it is not already up, a browser tab opens on the run's page, and every
generation appears there as it happens, with the same live genealogy and the same
controls for changing the evolution mid-flight.

The whole of it::

    import fedotweb.autowatch          # noqa: F401  -- opens the GUI on fit()

    from fedot import Fedot
    Fedot(problem='classification', timeout=10).fit(features=..., target=...)

Or explicitly, when you want to name the run or keep the handle::

    from fedotweb import watch

    with watch('sea level forecast') as session:
        model = Fedot(problem='ts_forecasting', timeout=10, optimizer=session.optimizer)
        model.fit(train)
"""

from __future__ import annotations

import socket
import threading
import time
import webbrowser
from collections.abc import Iterator
from contextlib import contextmanager
from pathlib import Path
from typing import Any

from .settings import get_settings
from .storage.sqlite import Store, utcnow

#: How long to wait for the background server to answer before giving up on it.
SERVER_START_TIMEOUT = 30.0

_server_lock = threading.Lock()
_server_thread: threading.Thread | None = None


def _port_is_open(host: str, port: int, timeout: float = 0.4) -> bool:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as probe:
        probe.settimeout(timeout)
        return probe.connect_ex((host, port)) == 0


def ensure_server(host: str | None = None, port: int | None = None) -> str:
    """Start the FEDOT.Web server in this process if nothing is serving yet.

    Returns the base URL. An already-running instance -- yours or someone else's
    -- is reused, so several scripts can report into the same GUI.
    """
    settings = get_settings()
    host = host or settings.host
    port = port or settings.port

    if _port_is_open(host, port):
        return f"http://{host}:{port}"

    global _server_thread
    with _server_lock:
        if _server_thread is None or not _server_thread.is_alive():
            import uvicorn

            from .main import create_app

            config = uvicorn.Config(
                create_app(), host=host, port=port, log_level="warning", access_log=False
            )
            server = uvicorn.Server(config)
            # A daemon thread so the script can exit without joining it; the run
            # is already persisted, so nothing is lost when the process ends.
            _server_thread = threading.Thread(
                target=server.run, name="fedot-web-server", daemon=True
            )
            _server_thread.start()

    deadline = time.monotonic() + SERVER_START_TIMEOUT
    while time.monotonic() < deadline:
        if _port_is_open(host, port):
            return f"http://{host}:{port}"
        time.sleep(0.2)
    raise RuntimeError(f"The FEDOT.Web server did not start on {host}:{port}")


class WatchSession:
    """A run started outside the GUI, reporting into it."""

    def __init__(self, uid: str, url: str, store: Store, run_dir: Path) -> None:
        self.uid = uid
        self.url = url
        self._store = store
        self._run_dir = run_dir
        self._started = time.monotonic()
        self._optimizer_instance: Any = None
        self._last_generation = 0

    # ------------------------------------------------------------------- events

    def emit(self, kind: str, **payload: Any) -> None:
        self._store.append_event(self.uid, kind, payload)

    # ---------------------------------------------------------------- optimizer

    @property
    def optimizer(self) -> type:
        """Pass this to ``Fedot(optimizer=...)``.

        It is an ``EvoGraphOptimizer`` that reports each generation into the GUI
        and applies whatever controls the GUI has been asked for.
        """
        from golem.core.optimisers.genetic.gp_optimizer import EvoGraphOptimizer

        from .runs.control import apply_controls, describe_effective, install_overrides, read_controls
        from .runs.evaltrace import TracingObjectiveEvaluate
        from .runs.worker import describe_lineage, serialise_individual, summarise_population

        session = self

        def on_iteration(population, optimizer) -> None:
            try:
                generation = int(getattr(optimizer, "current_generation_num", 0))
                members = list(population)
                best_individuals = list(getattr(optimizer, "best_individuals", None) or [])
                best = serialise_individual(best_individuals[0]) if best_individuals else None

                session._last_generation = generation
                session.emit(
                    "generation",
                    generation=generation,
                    best_pipeline=best,
                    **summarise_population(members),
                )
                session.emit(
                    "population",
                    generation=generation,
                    individuals=describe_lineage(members),
                    best_uids=[str(individual.uid) for individual in best_individuals],
                )
            except Exception as exc:  # reporting must never disturb the run
                session.emit("log", level="warning", message=f"progress callback failed: {exc}")

            try:
                changes = apply_controls(optimizer, read_controls(session._run_dir))
                if changes:
                    session.emit("control_applied", generation=session._last_generation, changes=changes)
                session.emit("effective_params", **describe_effective(optimizer))
            except Exception as exc:
                session.emit("log", level="warning", message=f"could not apply controls: {exc}")

        class AttachedOptimizer(EvoGraphOptimizer):
            def __init__(self, *args, **kwargs):
                super().__init__(*args, **kwargs)
                install_overrides(self)
                self.set_iteration_callback(on_iteration)
                session._optimizer_instance = self
                try:
                    apply_controls(self, read_controls(session._run_dir))
                except Exception:
                    pass

            def optimise(self, objective):
                # Same per-pipeline, per-fold trace as GUI-launched runs.
                return super().optimise(
                    TracingObjectiveEvaluate.wrap(objective, session._run_dir)
                )

        return AttachedOptimizer

    # ------------------------------------------------------------------ closing

    def finish(self, error: str | None = None) -> None:
        """Mark the run done and keep whatever the optimiser produced."""
        history = getattr(self._optimizer_instance, "history", None)
        if history is not None:
            try:
                (self._run_dir / "history.json").write_text(history.save(), encoding="utf-8")
            except Exception as exc:
                self.emit("log", level="warning", message=f"history not saved: {exc}")

        if error:
            self.emit("error", message=error)
            self._store.update_run(self.uid, status="failed", error=error, finished_at=utcnow())
        else:
            self.emit("finished", generations=self._last_generation)
            self._store.update_run(self.uid, status="finished", finished_at=utcnow())

    def record_result(self, model: Any) -> None:
        """Store the fitted pipeline and its metrics, if the model has them.

        Optional: a run is perfectly readable without it, but calling this makes
        the results panel show the same thing a GUI-started run would.
        """
        from .pipelines.convert import pipeline_to_graph

        pipeline = getattr(model, "current_pipeline", None)
        if pipeline is None:
            return
        try:
            graph = pipeline_to_graph(pipeline)
        except Exception as exc:
            self.emit("log", level="warning", message=f"pipeline not stored: {exc}")
            return

        run = self._store.get_run(self.uid) or {}
        pipeline_uid = self._store.save_pipeline(
            graph=graph,
            name=f"{run.get('name', 'run')} — best pipeline",
            task=(run.get("config") or {}).get("problem"),
            origin="attached",
            run_uid=self.uid,
        )
        updates: dict[str, Any] = {"best_pipeline": pipeline_uid}

        # `get_metrics` scores whatever `predict` last ran on. A script that only
        # fitted has no test data, and FEDOT then returns a number that looks like
        # a metric but means nothing -- so it is better to show none at all.
        if getattr(model, "prediction", None) is not None:
            try:
                metrics = model.get_metrics()
                updates["metrics"] = {
                    str(name): float(value)
                    for name, value in dict(metrics).items()
                    if isinstance(value, (int, float)) and value == value
                }
            except Exception as exc:
                self.emit("log", level="warning", message=f"metrics unavailable: {exc}")
        else:
            self.emit(
                "log",
                level="info",
                message="No metrics: call predict() before record_result() to score the model",
            )

        self._store.update_run(self.uid, **updates)


@contextmanager
def watch(
    name: str | None = None,
    *,
    open_browser: bool = True,
    config: dict[str, Any] | None = None,
) -> Iterator[WatchSession]:
    """Attach the GUI to a FEDOT run you drive yourself.

    Args:
        name: what to call the run in the GUI.
        open_browser: set ``False`` on a headless machine; the URL is still
            printed and the run is still recorded.
        config: extra facts about the run to show alongside it, e.g. the task.
    """
    settings = get_settings()
    url = ensure_server()

    store = Store(settings.database_path)
    run_config = {"origin": "attached", **(config or {})}
    uid = store.create_run(name=name or "Attached FEDOT run", dataset_uid=None, config=run_config)
    store.update_run(uid, status="running", started_at=utcnow())

    run_dir = settings.runs_dir / uid
    run_dir.mkdir(parents=True, exist_ok=True)

    session = WatchSession(uid, f"{url}/runs/{uid}", store, run_dir)
    session.emit("status", status="attached", url=session.url)

    # Trace node fits happening in this process from the very start, so the
    # minutes FEDOT spends fitting the initial assumptions are not silence.
    from .runs.evaltrace import begin_main_process_trace

    begin_main_process_trace(run_dir)

    print(f"FEDOT.Web is watching this run: {session.url}")
    if open_browser:
        try:
            webbrowser.open(session.url)
        except Exception:
            # A machine without a browser is not a reason to fail the run.
            pass

    try:
        yield session
    except BaseException as exc:
        session.finish(error=f"{type(exc).__name__}: {exc}")
        raise
    else:
        session.finish()

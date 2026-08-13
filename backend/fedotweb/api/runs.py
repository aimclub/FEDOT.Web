"""Endpoints that drive the framework: start, watch and stop AutoML runs."""

from __future__ import annotations

import asyncio
import json
import shutil
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Query, WebSocket, WebSocketDisconnect
from fastapi.responses import Response

from ..analysis import AnalysisManager
from ..history import (
    HistoryUnavailable,
    individual_pipeline,
    lineage_graph,
    live_individual_pipeline,
    live_lineage_graph,
)
from ..runs.control import read_controls, write_controls
from ..runs.manager import RunError, RunManager
from ..schemas import (
    EffectiveParams,
    EvolutionControls,
    GenerationPoint,
    IndividualPipeline,
    LineageGraph,
    PipelineGraph,
    RunControlState,
    RunEvent,
    RunProgress,
    RunRecord,
    StartRunRequest,
)
from ..settings import Settings, get_settings
from ..storage.sqlite import Store, utcnow
from .deps import get_analysis_manager, get_manager, get_store

router = APIRouter(prefix="/runs", tags=["runs"])

#: How often the progress socket looks for new events when nothing wakes it.
WS_POLL_SECONDS = 0.5

#: Idle time after which the socket sends a keep-alive frame.
WS_PING_SECONDS = 20.0


def _generation_points(events: list[dict[str, Any]]) -> list[GenerationPoint]:
    points: list[GenerationPoint] = []
    for event in events:
        if event["kind"] != "generation":
            continue
        payload = event["payload"]
        points.append(
            GenerationPoint(
                generation=payload.get("generation", len(points)),
                size=payload.get("size", 0),
                best_fitness=payload.get("best_fitness"),
                mean_fitness=payload.get("mean_fitness"),
                worst_fitness=payload.get("worst_fitness"),
            )
        )
    return points


@router.get("", response_model=list[RunRecord])
def list_runs(store: Store = Depends(get_store)) -> list[RunRecord]:
    return [RunRecord(**record) for record in store.list_runs()]


@router.post("", response_model=RunRecord, status_code=202)
async def start_run(
    request: StartRunRequest,
    store: Store = Depends(get_store),
    manager: RunManager = Depends(get_manager),
    settings: Settings = Depends(get_settings),
) -> RunRecord:
    """Configure and launch a FEDOT composition."""
    config = request.config

    dataset = store.get_dataset(config.dataset_uid)
    if dataset is None:
        raise HTTPException(status_code=404, detail=f"Unknown dataset: {config.dataset_uid}")

    target = config.target or dataset.get("target")
    if not target:
        raise HTTPException(status_code=422, detail="No target column was selected for this dataset")
    known_columns = {column["name"] for column in dataset["columns"]}
    if target not in known_columns:
        raise HTTPException(status_code=422, detail=f"Column '{target}' is not in the dataset")

    if config.timeout > settings.max_run_timeout_minutes:
        raise HTTPException(
            status_code=422,
            detail=f"The time budget exceeds the server limit of {settings.max_run_timeout_minutes:g} minutes",
        )

    worker_config = config.model_dump(exclude_none=True)
    worker_config["dataset_path"] = dataset["filename"]
    worker_config["target"] = target
    if config.initial_pipeline is not None:
        worker_config["initial_pipeline"] = config.initial_pipeline.model_dump()

    name = request.name or f"{config.problem} on {dataset['name']}"
    run_uid = store.create_run(name=name, dataset_uid=config.dataset_uid, config=worker_config)

    try:
        await manager.start(run_uid, worker_config)
    except RunError as exc:
        store.update_run(run_uid, status="failed", error=str(exc))
        raise HTTPException(status_code=409, detail=str(exc)) from exc

    record = store.get_run(run_uid)
    if record is None:  # pragma: no cover
        raise HTTPException(status_code=500, detail="The run could not be created")
    return RunRecord(**record)


@router.get("/{uid}", response_model=RunRecord)
def get_run(uid: str, store: Store = Depends(get_store)) -> RunRecord:
    record = store.get_run(uid)
    if record is None:
        raise HTTPException(status_code=404, detail=f"Unknown run: {uid}")
    return RunRecord(**record)


@router.get("/{uid}/progress", response_model=RunProgress)
def get_progress(uid: str, store: Store = Depends(get_store)) -> RunProgress:
    """A snapshot of the run: status, the fitness curve so far and the best pipeline."""
    record = store.get_run(uid)
    if record is None:
        raise HTTPException(status_code=404, detail=f"Unknown run: {uid}")

    # Population events carry whole pipelines; the progress snapshot needs none of that.
    events = store.list_events(uid, kinds=["generation"])
    generations = _generation_points(events)

    best_graph: PipelineGraph | None = None
    if record["best_pipeline"]:
        stored = store.get_pipeline(record["best_pipeline"])
        if stored:
            best_graph = PipelineGraph(**stored["graph"])
    else:
        # While the run is live the best pipeline comes from the latest generation.
        for event in reversed(events):
            if event["kind"] == "generation" and event["payload"].get("best_pipeline"):
                best_graph = PipelineGraph(**event["payload"]["best_pipeline"])
                break

    return RunProgress(
        run=RunRecord(**record),
        generations=generations,
        best_pipeline=best_graph,
        last_event_id=events[-1]["id"] if events else 0,
    )


@router.get("/{uid}/events", response_model=list[RunEvent])
def get_events(
    uid: str,
    after_id: int = Query(default=0, ge=0),
    store: Store = Depends(get_store),
) -> list[RunEvent]:
    if store.get_run(uid) is None:
        raise HTTPException(status_code=404, detail=f"Unknown run: {uid}")
    return [RunEvent(**event) for event in store.list_events(uid, after_id=after_id)]


@router.get("/{uid}/history")
def get_history(uid: str, manager: RunManager = Depends(get_manager)) -> dict:
    """The full GOLEM optimisation history, as saved by the worker."""
    path = manager.run_dir(uid) / "history.json"
    if not path.exists():
        raise HTTPException(status_code=404, detail="No history was saved for this run")
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise HTTPException(status_code=422, detail=f"The stored history is unreadable: {exc}") from exc


@router.get("/{uid}/lineage", response_model=LineageGraph)
def get_lineage(
    uid: str,
    full: bool = Query(
        default=False,
        description="Include every individual, not only the ancestry of the best pipeline",
    ),
    store: Store = Depends(get_store),
    manager: RunManager = Depends(get_manager),
) -> LineageGraph:
    """The evolution history as a graph.

    Individuals and the operators that produced them, laid out generation by
    generation, so the descent of the best pipeline is visible.

    A finished run is read from its saved history. A run still in progress has no
    history file yet, so the graph is assembled from the progress events instead
    -- which is what makes this usable for watching a composition as it happens.
    """
    if store.get_run(uid) is None:
        raise HTTPException(status_code=404, detail=f"Unknown run: {uid}")

    path = manager.run_dir(uid) / "history.json"
    try:
        if path.exists():
            return LineageGraph(**lineage_graph(path, only_winning_path=not full))
    except (ValueError, KeyError, TypeError) as exc:
        raise HTTPException(
            status_code=422, detail=f"The stored history could not be interpreted: {exc}"
        ) from exc

    graph = live_lineage_graph(
        store.list_events(uid, kinds=["population"]), only_winning_path=not full
    )
    if graph is None:
        raise HTTPException(
            status_code=404,
            detail="No generation has been reported for this run yet",
        )
    return LineageGraph(**graph)


@router.get("/{uid}/lineage/{individual_uid}", response_model=IndividualPipeline)
def get_lineage_pipeline(
    uid: str,
    individual_uid: str,
    store: Store = Depends(get_store),
    manager: RunManager = Depends(get_manager),
) -> IndividualPipeline:
    """The pipeline of one individual in the genealogy, live or finished."""
    if store.get_run(uid) is None:
        raise HTTPException(status_code=404, detail=f"Unknown run: {uid}")

    path = manager.run_dir(uid) / "history.json"
    described = None
    if path.exists():
        try:
            described = individual_pipeline(path, individual_uid)
        except HistoryUnavailable:
            described = None

    if described is None:
        described = live_individual_pipeline(
            store.list_events(uid, kinds=["population"]), individual_uid
        )

    if described is None:
        raise HTTPException(status_code=404, detail=f"No individual {individual_uid} in this run")
    return IndividualPipeline(**described)


def _control_state(uid: str, store: Store, manager: RunManager) -> RunControlState:
    record = store.get_run(uid)
    if record is None:
        raise HTTPException(status_code=404, detail=f"Unknown run: {uid}")

    requested = read_controls(manager.run_dir(uid))

    effective = None
    applied: list[str] = []
    for event in reversed(store.list_events(uid, kinds=["effective_params", "control_applied"])):
        if effective is None and event["kind"] == "effective_params":
            effective = EffectiveParams(**event["payload"])
        elif not applied and event["kind"] == "control_applied":
            applied = list(event["payload"].get("changes") or [])
        if effective is not None and applied:
            break

    return RunControlState(
        requested=EvolutionControls(**requested.as_dict()),
        effective=effective,
        can_control=record["status"] in {"pending", "running"},
        applied=applied,
    )


@router.get("/{uid}/controls", response_model=RunControlState)
def get_controls(
    uid: str,
    store: Store = Depends(get_store),
    manager: RunManager = Depends(get_manager),
) -> RunControlState:
    """What has been asked for, and what the optimiser is currently using."""
    return _control_state(uid, store, manager)


@router.patch("/{uid}/controls", response_model=RunControlState)
def update_controls(
    uid: str,
    patch: dict,
    store: Store = Depends(get_store),
    manager: RunManager = Depends(get_manager),
) -> RunControlState:
    """Change how the evolution behaves, without restarting it.

    The request is recorded for the worker, which picks it up between generations
    -- a generation in flight is never disturbed. Fields left out keep their
    current value; a field set to ``null`` hands that parameter back to GOLEM's
    own adaptive policy.
    """
    record = store.get_run(uid)
    if record is None:
        raise HTTPException(status_code=404, detail=f"Unknown run: {uid}")
    if record["status"] not in {"pending", "running"}:
        raise HTTPException(
            status_code=409, detail="This run has finished; there is nothing left to control"
        )

    write_controls(manager.run_dir(uid), patch)
    return _control_state(uid, store, manager)


@router.post("/{uid}/stop", response_model=RunRecord)
async def stop_run(
    uid: str,
    store: Store = Depends(get_store),
    manager: RunManager = Depends(get_manager),
) -> RunRecord:
    record = store.get_run(uid)
    if record is None:
        raise HTTPException(status_code=404, detail=f"Unknown run: {uid}")

    if await manager.cancel(uid):
        return RunRecord(**(store.get_run(uid) or record))

    if record["status"] in {"pending", "running"}:
        # No worker of ours to kill, yet the run reads as live: it is driven by an
        # external process (a script that attached), or that process died without
        # saying so. Leave a graceful-finish request for a script that is still
        # alive, and mark the record so it stops showing as running forever.
        write_controls(manager.run_dir(uid), {"finish_now": True})
        store.update_run(
            uid,
            status="cancelled",
            finished_at=utcnow(),
            error="Stopped from the GUI; a script attached to this run may still be finishing",
        )
        return RunRecord(**(store.get_run(uid) or record))

    raise HTTPException(status_code=409, detail="This run is not in progress")


@router.delete("/{uid}", status_code=204)
async def delete_run(
    uid: str,
    store: Store = Depends(get_store),
    manager: RunManager = Depends(get_manager),
    analyses: AnalysisManager = Depends(get_analysis_manager),
) -> Response:
    if store.get_run(uid) is None:
        raise HTTPException(status_code=404, detail=f"Unknown run: {uid}")
    if manager.is_running(uid):
        raise HTTPException(status_code=409, detail="Stop the run before deleting it")
    # Analysis job directories are keyed by analysis uid, so collect them before
    # the rows (and the uids with them) are gone.
    for analysis in store.list_analyses(uid):
        shutil.rmtree(analyses.job_dir(analysis["uid"]), ignore_errors=True)
    store.delete_run(uid)
    shutil.rmtree(manager.run_dir(uid), ignore_errors=True)
    return Response(status_code=204)


@router.websocket("/{uid}/stream")
async def stream_run(websocket: WebSocket, uid: str) -> None:
    """Push evolution progress to the browser as it happens."""
    await websocket.accept()
    state = getattr(websocket.app.state, "container", None)
    if state is None:  # pragma: no cover
        await websocket.close(code=1011)
        return

    store, manager = state.store, state.manager
    if store.get_run(uid) is None:
        await websocket.send_json({"kind": "error", "payload": {"message": f"Unknown run: {uid}"}})
        await websocket.close(code=1008)
        return

    queue = manager.subscribe(uid)
    last_id = 0
    last_status: str | None = None
    idle_ticks = 0

    async def flush_new_events() -> None:
        """Send everything stored since the last send. The store is the truth.

        Reading from the store rather than only from the manager's queue is what
        lets a run started outside the GUI stream too: an attached script writes
        its events straight to the database and has no manager process to publish
        through.
        """
        nonlocal last_id
        for event in store.list_events(uid, after_id=last_id):
            await websocket.send_json(event)
            last_id = max(last_id, int(event.get("id") or 0))

    try:
        # Replay what already happened so a client that connects late, or
        # reconnects, sees the whole curve.
        await flush_new_events()

        while True:
            record = store.get_run(uid)
            status = record["status"] if record else None
            if status != last_status:
                last_status = status
                await websocket.send_json({"kind": "run_status", "payload": {"status": status}})

            try:
                # The queue is only a wake-up hint; whatever it carries is read
                # back from the store so ordering and ids stay consistent.
                await asyncio.wait_for(queue.get(), timeout=WS_POLL_SECONDS)
                idle_ticks = 0
            except asyncio.TimeoutError:
                idle_ticks += 1

            await flush_new_events()

            if status in {"finished", "failed", "cancelled"}:
                # Nothing more will arrive; keep the socket open but quiet so the
                # client can decide when to close it.
                await websocket.send_json({"kind": "ping", "payload": {}})
                return

            if idle_ticks * WS_POLL_SECONDS >= WS_PING_SECONDS:
                # A periodic ping keeps intermediate proxies from closing an idle
                # socket during a long generation.
                idle_ticks = 0
                await websocket.send_json({"kind": "ping", "payload": {}})
    except (WebSocketDisconnect, RuntimeError):
        # The client went away, or Starlette closed the socket underneath us.
        pass
    finally:
        manager.unsubscribe(uid, queue)

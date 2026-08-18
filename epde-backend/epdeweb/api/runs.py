"""Endpoints that drive EPDE: start, watch and stop equation searches."""

from __future__ import annotations

import asyncio
import json
import shutil
from pathlib import Path
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Query, WebSocket, WebSocketDisconnect
from fastapi.responses import JSONResponse, Response

from ..adapters.availability import describe_epde
from ..adapters.controls import (
    CONTROL_BY_NAME,
    Controls,
    read_controls,
    write_controls,
)
from ..datasets.service import DatasetError, DatasetService
from ..history.live import lineage_from_events, system_from_events
from ..history.service import HistoryUnavailable, saved_lineage_graph, saved_system
from ..runs.manager import RunError, RunManager
from ..schemas import (
    EvolutionControls,
    GenerationPoint,
    LineageGraph,
    ParetoPoint,
    RunControlState,
    RunEvent,
    RunProgress,
    RunRecord,
    RunResult,
    StartRunRequest,
    SystemGraph,
)
from ..settings import Settings
from ..storage.sqlite import Store, utcnow
from .deps import get_datasets, get_manager, get_run_settings, get_store

router = APIRouter(prefix="/runs", tags=["epde runs"])

#: How often the progress socket looks for new events when nothing wakes it.
WS_POLL_SECONDS = 0.5

#: Idle time after which the socket sends a keep-alive frame.
WS_PING_SECONDS = 20.0

LIVE_STATUSES = {"pending", "running"}


def _generation_points(events: list[dict[str, Any]]) -> list[GenerationPoint]:
    points: list[GenerationPoint] = []
    for event in events:
        if event["kind"] != "generation":
            continue
        payload = event["payload"]
        points.append(
            GenerationPoint(
                generation=payload.get("generation", len(points)),
                label=str(payload.get("label") or ""),
                size=payload.get("size", 0),
                evaluated=payload.get("evaluated", 0),
                front_size=payload.get("front_size", 0),
                objectives=payload.get("objectives") or [],
                hypervolume=payload.get("hypervolume"),
                elapsed=payload.get("elapsed"),
            )
        )
    return points


def _read_result(run_dir: Path) -> dict[str, Any] | None:
    path = run_dir / "result.json"
    if not path.exists():
        return None
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return None


@router.get("", response_model=list[RunRecord])
def list_runs(store: Store = Depends(get_store)) -> list[RunRecord]:
    return [RunRecord(**record) for record in store.list_runs()]


@router.post("", response_model=RunRecord, status_code=202)
async def start_run(
    request: StartRunRequest,
    store: Store = Depends(get_store),
    manager: RunManager = Depends(get_manager),
    datasets: DatasetService = Depends(get_datasets),
    settings: Settings = Depends(get_run_settings),
) -> RunRecord:
    """Configure and launch an equation search."""
    availability = describe_epde()
    if not availability.available:
        raise HTTPException(status_code=503, detail=availability.error or "EPDE is not installed")

    config = request.config
    record = store.get_dataset(config.dataset_uid)
    if record is None:
        raise HTTPException(status_code=404, detail=f"Unknown dataset: {config.dataset_uid}")

    known = {variable["name"] for variable in record["variables"]}
    variables = list(config.variables) if config.variables else sorted(known)
    unknown = [name for name in variables if name not in known]
    if unknown:
        raise HTTPException(
            status_code=422, detail=f"The dataset has no variable(s) {', '.join(unknown)}"
        )
    if not variables:
        raise HTTPException(status_code=422, detail="Choose at least one variable to describe")

    if config.timeout is not None and config.timeout > settings.max_run_timeout_minutes:
        raise HTTPException(
            status_code=422,
            detail=(
                f"The time budget exceeds the server limit of "
                f"{settings.max_run_timeout_minutes:g} minutes"
            ),
        )
    if config.sparsity_min >= config.sparsity_max and config.multiobjective:
        raise HTTPException(
            status_code=422,
            detail=(
                "The sparsity interval is empty. A multi-objective search evolves the sparsity "
                "constant inside this interval, so its ends must differ."
            ),
        )

    try:
        dataset_path = str(datasets.export_path(config.dataset_uid))
    except DatasetError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc

    worker_config = config.model_dump()
    worker_config["dataset_path"] = dataset_path
    worker_config["variables"] = variables
    worker_config["token_families"] = [family.model_dump() for family in config.token_families]

    name = request.name or f"{'+'.join(variables)} on {record['name']}"
    run_uid = store.create_run(name=name, dataset_uid=config.dataset_uid, config=worker_config)

    try:
        await manager.start(run_uid, worker_config)
    except RunError as exc:
        store.update_run(run_uid, status="failed", error=str(exc))
        raise HTTPException(status_code=409, detail=str(exc)) from exc

    stored = store.get_run(run_uid)
    if stored is None:  # pragma: no cover
        raise HTTPException(status_code=500, detail="The run could not be created")
    return RunRecord(**stored)


@router.get("/{uid}", response_model=RunRecord)
def get_run(uid: str, store: Store = Depends(get_store)) -> RunRecord:
    record = store.get_run(uid)
    if record is None:
        raise HTTPException(status_code=404, detail=f"Unknown run: {uid}")
    return RunRecord(**record)


@router.get("/{uid}/progress", response_model=RunProgress)
def get_progress(
    uid: str,
    store: Store = Depends(get_store),
    manager: RunManager = Depends(get_manager),
) -> RunProgress:
    """A snapshot: status, the objective curves so far, and the leading front."""
    record = store.get_run(uid)
    if record is None:
        raise HTTPException(status_code=404, detail=f"Unknown run: {uid}")

    # Population events carry whole systems; the snapshot needs none of that.
    events = store.list_events(uid, kinds=["generation", "finished"])
    generations = _generation_points(events)

    objective_names: list[str] = []
    for event in reversed(events):
        names = event["payload"].get("objective_names")
        if names:
            objective_names = [str(name) for name in names]
            break

    front: list[ParetoPoint] = []
    best_graph: SystemGraph | None = None

    result = _read_result(manager.run_dir(uid))
    if result:
        objective_names = objective_names or [str(name) for name in result.get("objective_names") or []]
        front = [
            ParetoPoint(
                uid=str(entry.get("uid") or ""),
                objectives=[float(value) for value in entry.get("objectives") or []],
                text=str(entry.get("text") or ""),
                latex=str(entry.get("latex") or ""),
                complexity=int(entry.get("complexity") or 0),
                active_terms=int(entry.get("active_terms") or 0),
            )
            for entry in result.get("front") or []
        ]
        if result.get("best_system"):
            best_graph = SystemGraph(**result["best_system"])

    if best_graph is None:
        if record["best_system"]:
            stored = store.get_system(record["best_system"])
            if stored:
                best_graph = SystemGraph(**stored["graph"])
        else:
            # While the run is live the leader comes from the latest generation.
            for event in reversed(events):
                candidate = event["payload"].get("best")
                if candidate:
                    best_graph = SystemGraph(**candidate)
                    break

    return RunProgress(
        run=RunRecord(**record),
        generations=generations,
        objective_names=objective_names,
        front=front,
        best_system=best_graph,
        last_event_id=events[-1]["id"] if events else 0,
    )


@router.get("/{uid}/result", response_model=RunResult)
def get_result(
    uid: str,
    store: Store = Depends(get_store),
    manager: RunManager = Depends(get_manager),
) -> RunResult:
    """The full outcome: the whole Pareto front, with per-term ablation."""
    if store.get_run(uid) is None:
        raise HTTPException(status_code=404, detail=f"Unknown run: {uid}")
    result = _read_result(manager.run_dir(uid))
    if result is None:
        raise HTTPException(status_code=404, detail="This run has not produced a result")
    return RunResult(**result)


@router.get("/{uid}/events", response_model=list[RunEvent])
def get_events(
    uid: str,
    after_id: int = Query(default=0, ge=0),
    store: Store = Depends(get_store),
) -> list[RunEvent]:
    if store.get_run(uid) is None:
        raise HTTPException(status_code=404, detail=f"Unknown run: {uid}")
    # The population events are the genealogy, which has its own endpoint; a
    # client polling the log should not be handed the whole population every
    # generation.
    kinds = ["status", "log", "generation", "progress", "finished", "error", "cancelled",
             "control_applied", "effective_params", "operators", "run_status"]
    return [RunEvent(**event) for event in store.list_events(uid, after_id=after_id, kinds=kinds)]


@router.get("/{uid}/history")
def get_history(uid: str, manager: RunManager = Depends(get_manager)) -> JSONResponse:
    """The saved history of the run, as written by the worker.

    EPDE keeps nothing after a search, so this file is the module's own record
    rather than a framework artefact -- which is also why it is worth
    downloading: it is the only copy.
    """
    path = manager.run_dir(uid) / "history.json"
    if not path.exists():
        raise HTTPException(status_code=404, detail="No history was saved for this run")
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise HTTPException(status_code=422, detail=f"The stored history is unreadable: {exc}") from exc
    return JSONResponse(
        content=payload,
        headers={"Content-Disposition": f'attachment; filename="epde_history_{uid}.json"'},
    )


@router.get("/{uid}/lineage", response_model=LineageGraph)
def get_lineage(
    uid: str,
    full: bool = Query(
        default=False,
        description="Include every candidate, not only the ancestry of the final front",
    ),
    store: Store = Depends(get_store),
    manager: RunManager = Depends(get_manager),
) -> LineageGraph:
    """The evolution history as a graph.

    Candidate systems and the operators that produced them, laid out generation
    by generation, so the descent of the final Pareto front is visible.

    A finished run is read from its saved history; a run still in progress has
    no history file yet, so the graph is assembled from the progress events
    instead -- which is what makes it usable for watching a search happen.
    """
    if store.get_run(uid) is None:
        raise HTTPException(status_code=404, detail=f"Unknown run: {uid}")

    path = manager.run_dir(uid) / "history.json"
    if path.exists():
        try:
            return LineageGraph(**saved_lineage_graph(path, only_winning_path=not full))
        except HistoryUnavailable:
            pass
        except (ValueError, KeyError, TypeError) as exc:
            raise HTTPException(
                status_code=422, detail=f"The stored history could not be interpreted: {exc}"
            ) from exc

    graph = lineage_from_events(
        store.list_events(uid, kinds=["population"]), only_winning_path=not full
    )
    if graph is None:
        raise HTTPException(
            status_code=404, detail="No generation has been reported for this run yet"
        )
    graph["only_winning_path"] = not full
    graph["source"] = "live"
    graph["is_live"] = True
    graph.setdefault("objective_names", _objective_names_from_events(store, uid))
    return LineageGraph(**graph)


def _objective_names_from_events(store: Store, uid: str) -> list[str]:
    for event in reversed(store.list_events(uid, kinds=["generation", "finished"])):
        names = event["payload"].get("objective_names")
        if names:
            return [str(name) for name in names]
    return []


@router.get("/{uid}/lineage/{individual_uid}", response_model=SystemGraph)
def get_lineage_system(
    uid: str,
    individual_uid: str,
    store: Store = Depends(get_store),
    manager: RunManager = Depends(get_manager),
) -> SystemGraph:
    """The system one candidate in the genealogy stands for, live or finished."""
    if store.get_run(uid) is None:
        raise HTTPException(status_code=404, detail=f"Unknown run: {uid}")

    path = manager.run_dir(uid) / "history.json"
    described = None
    if path.exists():
        try:
            described = saved_system(path, individual_uid)
        except HistoryUnavailable:
            described = None

    if described is None:
        described = system_from_events(
            store.list_events(uid, kinds=["population"]), individual_uid
        )
    if described is None:
        raise HTTPException(status_code=404, detail=f"No candidate {individual_uid} in this run")
    return SystemGraph(**described)


# --------------------------------------------------------------------- controls


def _control_state(uid: str, store: Store, manager: RunManager) -> RunControlState:
    record = store.get_run(uid)
    if record is None:
        raise HTTPException(status_code=404, detail=f"Unknown run: {uid}")

    requested = read_controls(manager.run_dir(uid))

    effective: dict[str, float | None] = {}
    applied: list[str] = []
    available: list[str] = []
    for event in reversed(
        store.list_events(uid, kinds=["effective_params", "control_applied", "operators"])
    ):
        payload = event["payload"]
        if not effective and event["kind"] in {"effective_params", "operators"}:
            effective = dict(payload.get("effective") or {})
        if not applied and event["kind"] == "control_applied":
            applied = list(payload.get("changes") or [])
        if not available and event["kind"] == "operators":
            available = [str(name) for name in payload.get("available") or []]
        if effective and applied and available:
            break

    return RunControlState(
        requested=EvolutionControls(**_controls_payload(requested)),
        effective=effective,
        can_control=record["status"] in LIVE_STATUSES,
        applied=applied,
        available_operators=available,
    )


def _controls_payload(controls: Controls) -> dict[str, Any]:
    payload = {name: None for name in CONTROL_BY_NAME}
    payload.update(controls.values)
    payload["finish_now"] = controls.finish_now
    payload["epochs"] = controls.epochs
    return payload


@router.get("/{uid}/controls", response_model=RunControlState)
def get_controls(
    uid: str,
    store: Store = Depends(get_store),
    manager: RunManager = Depends(get_manager),
) -> RunControlState:
    """What has been asked for, and what the operators are currently using."""
    return _control_state(uid, store, manager)


@router.patch("/{uid}/controls", response_model=RunControlState)
def update_controls(
    uid: str,
    patch: dict,
    store: Store = Depends(get_store),
    manager: RunManager = Depends(get_manager),
) -> RunControlState:
    """Change how the search behaves, without restarting it.

    The request is recorded for the worker, which picks it up between
    generations, so a generation already in flight is never disturbed. A field
    left out keeps its value; a field set to ``null`` hands the parameter back
    to the value EPDE loaded from its defaults file.
    """
    record = store.get_run(uid)
    if record is None:
        raise HTTPException(status_code=404, detail=f"Unknown run: {uid}")
    if record["status"] not in LIVE_STATUSES:
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
    """Kill the run. To keep the result instead, ask it to finish now."""
    record = store.get_run(uid)
    if record is None:
        raise HTTPException(status_code=404, detail=f"Unknown run: {uid}")

    if await manager.cancel(uid):
        return RunRecord(**(store.get_run(uid) or record))

    if record["status"] in LIVE_STATUSES:
        # No worker of ours to kill, yet the run reads as live: its process died
        # without saying so. Mark it, so it stops showing as running forever.
        store.update_run(
            uid,
            status="cancelled",
            finished_at=utcnow(),
            error="Stopped from the GUI; the worker process was already gone",
        )
        return RunRecord(**(store.get_run(uid) or record))

    raise HTTPException(status_code=409, detail="This run is not in progress")


@router.delete("/{uid}", status_code=204)
async def delete_run(
    uid: str,
    store: Store = Depends(get_store),
    manager: RunManager = Depends(get_manager),
) -> Response:
    if store.get_run(uid) is None:
        raise HTTPException(status_code=404, detail=f"Unknown run: {uid}")
    if manager.is_running(uid):
        raise HTTPException(status_code=409, detail="Stop the run before deleting it")
    store.delete_run(uid)
    shutil.rmtree(manager.run_dir(uid), ignore_errors=True)
    return Response(status_code=204)


@router.websocket("/{uid}/stream")
async def stream_run(websocket: WebSocket, uid: str) -> None:
    """Push search progress to the browser as it happens."""
    await websocket.accept()
    from .deps import STATE_ATTRIBUTE

    state = getattr(websocket.app.state, STATE_ATTRIBUTE, None)
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

        Population events are skipped: they carry every candidate system in a
        generation, and the genealogy endpoint serves them on demand. A socket
        that pushed them would spend most of its bandwidth on a view that may
        not even be open.
        """
        nonlocal last_id
        for event in store.list_events(uid, after_id=last_id):
            last_id = max(last_id, int(event.get("id") or 0))
            if event["kind"] == "population":
                continue
            await websocket.send_json(event)

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
                await websocket.send_json({"kind": "ping", "payload": {}})
                return

            if idle_ticks * WS_POLL_SECONDS >= WS_PING_SECONDS:
                # A periodic ping keeps intermediate proxies from closing an
                # idle socket during a long generation -- and EPDE generations
                # on a real field are long.
                idle_ticks = 0
                await websocket.send_json({"kind": "ping", "payload": {}})
    except (WebSocketDisconnect, RuntimeError):
        pass
    finally:
        manager.unsubscribe(uid, queue)

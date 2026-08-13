"""Endpoints for the analyses you ask for rather than get automatically."""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Depends, HTTPException

from ..analysis import AnalysisError, AnalysisManager
from ..history import individual_pipeline, live_individual_pipeline
from ..runs.manager import RunManager
from ..schemas import AnalysisRecord, StartAnalysisRequest
from ..storage.sqlite import Store
from .deps import get_analysis_manager, get_manager, get_store

router = APIRouter(tags=["analysis"])


def _resolve_graph(
    request: StartAnalysisRequest,
    run: dict[str, Any],
    store: Store,
    manager: RunManager,
) -> tuple[dict[str, Any], str | None]:
    """Find the pipeline to analyse: one that was named, or the run's best."""
    if request.individual_uid:
        path = manager.run_dir(run["uid"]) / "history.json"
        described = None
        if path.exists():
            described = individual_pipeline(path, request.individual_uid)
        if described is None:
            described = live_individual_pipeline(
                store.list_events(run["uid"], kinds=["population"]), request.individual_uid
            )
        if described is None:
            raise HTTPException(
                status_code=404, detail=f"No individual {request.individual_uid} in this run"
            )
        return described, None

    pipeline_uid = request.pipeline_uid or run.get("best_pipeline")
    if not pipeline_uid:
        raise HTTPException(
            status_code=409,
            detail="This run has no pipeline to analyse yet",
        )
    stored = store.get_pipeline(pipeline_uid)
    if stored is None:
        raise HTTPException(status_code=404, detail=f"Unknown pipeline: {pipeline_uid}")
    return stored["graph"], pipeline_uid


@router.post("/runs/{uid}/analyses", response_model=AnalysisRecord, status_code=202)
async def start_analysis(
    uid: str,
    request: StartAnalysisRequest,
    store: Store = Depends(get_store),
    manager: RunManager = Depends(get_manager),
    analyses: AnalysisManager = Depends(get_analysis_manager),
) -> AnalysisRecord:
    """Start an analysis of one of the run's pipelines.

    Both kinds refit the pipeline repeatedly, so they run out of process and are
    polled for; the response comes back immediately with a job to watch.
    """
    run = store.get_run(uid)
    if run is None:
        raise HTTPException(status_code=404, detail=f"Unknown run: {uid}")

    dataset_uid = run.get("dataset_uid")
    dataset = store.get_dataset(dataset_uid) if dataset_uid else None
    if dataset is None:
        raise HTTPException(
            status_code=409,
            detail="This run has no dataset on file, so its pipelines cannot be re-evaluated. "
            "Runs attached from a script keep their data in the script.",
        )

    graph, pipeline_uid = _resolve_graph(request, run, store, manager)
    config = run.get("config") or {}

    spec: dict[str, Any] = {
        "graph": graph,
        "dataset_path": dataset["filename"],
        "target": config.get("target") or dataset.get("target"),
        "problem": config.get("problem") or dataset.get("task") or "classification",
        "metric": config.get("metric"),
        "cv_folds": config.get("cv_folds", 5),
        "seed": config.get("seed"),
        "holdout_fraction": config.get("holdout_fraction"),
        "forecast_length": config.get("forecast_length"),
        "validation_blocks": config.get("validation_blocks"),
        "available_operations": config.get("available_operations"),
        "replacements": request.replacements,
        "analyse_edges": request.analyse_edges,
    }

    try:
        analysis_uid = await analyses.start(
            run_uid=uid,
            kind=request.kind,
            spec=spec,
            pipeline_uid=pipeline_uid,
            options=request.model_dump(),
        )
    except AnalysisError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc

    record = store.get_analysis(analysis_uid)
    if record is None:  # pragma: no cover
        raise HTTPException(status_code=500, detail="The analysis could not be created")
    return AnalysisRecord(**record)


@router.get("/runs/{uid}/analyses", response_model=list[AnalysisRecord])
def list_analyses(uid: str, store: Store = Depends(get_store)) -> list[AnalysisRecord]:
    if store.get_run(uid) is None:
        raise HTTPException(status_code=404, detail=f"Unknown run: {uid}")
    return [AnalysisRecord(**record) for record in store.list_analyses(uid)]


@router.get("/analyses/{analysis_uid}", response_model=AnalysisRecord)
def get_analysis(analysis_uid: str, store: Store = Depends(get_store)) -> AnalysisRecord:
    record = store.get_analysis(analysis_uid)
    if record is None:
        raise HTTPException(status_code=404, detail=f"Unknown analysis: {analysis_uid}")
    return AnalysisRecord(**record)

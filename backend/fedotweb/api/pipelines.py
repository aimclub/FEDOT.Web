"""Endpoints for building, validating, storing and exporting pipelines."""

from __future__ import annotations

import json

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import JSONResponse, Response

from ..pipelines.convert import (
    PipelineConversionError,
    graph_to_pipeline,
    pipeline_to_graph,
    validate_graph,
)
from ..schemas import (
    PipelineGraph,
    PipelineRecord,
    SavePipelineRequest,
    ValidatePipelineRequest,
    ValidationResult,
)
from ..storage.sqlite import Store
from .deps import get_store

router = APIRouter(prefix="/pipelines", tags=["pipelines"])


@router.get("", response_model=list[PipelineRecord])
def list_pipelines(
    run_uid: str | None = Query(default=None),
    store: Store = Depends(get_store),
) -> list[PipelineRecord]:
    return [PipelineRecord(**record) for record in store.list_pipelines(run_uid=run_uid)]


@router.post("", response_model=PipelineRecord, status_code=201)
def save_pipeline(request: SavePipelineRequest, store: Store = Depends(get_store)) -> PipelineRecord:
    """Persist a pipeline drawn in the editor.

    The graph is round-tripped through FEDOT first, so what comes back carries the
    depth, length and node roles FEDOT itself computes rather than the editor's
    guesses.
    """
    graph = request.graph.model_dump()
    try:
        pipeline = graph_to_pipeline(graph)
    except PipelineConversionError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc

    described = pipeline_to_graph(pipeline)
    uid = store.save_pipeline(
        graph=described,
        name=request.name,
        task=request.task,
        origin="editor",
        uid=request.uid,
    )
    record = store.get_pipeline(uid)
    if record is None:  # pragma: no cover - the row was just written
        raise HTTPException(status_code=500, detail="Pipeline could not be stored")
    return PipelineRecord(**record)


@router.post("/validate", response_model=ValidationResult)
def validate(request: ValidatePipelineRequest) -> ValidationResult:
    """Check a graph against FEDOT's own pipeline rules for the given task."""
    graph = request.graph.model_dump()
    is_valid, problems = validate_graph(graph, task=request.task)

    depth = length = 0
    if is_valid:
        try:
            pipeline = graph_to_pipeline(graph)
            depth, length = pipeline.depth, pipeline.length
        except PipelineConversionError:
            pass

    return ValidationResult(is_valid=is_valid, problems=problems, depth=depth, length=length)


@router.post("/describe", response_model=PipelineGraph)
def describe(graph: PipelineGraph) -> PipelineGraph:
    """Enrich an editor graph with everything FEDOT knows about it.

    Used when the user drops a node onto the canvas: the backend fills in the
    operation's group, tags, defaults and the recomputed depth/length.
    """
    try:
        pipeline = graph_to_pipeline(graph.model_dump())
    except PipelineConversionError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    return PipelineGraph(**pipeline_to_graph(pipeline, uid=graph.uid))


@router.get("/{uid}", response_model=PipelineRecord)
def get_pipeline(uid: str, store: Store = Depends(get_store)) -> PipelineRecord:
    record = store.get_pipeline(uid)
    if record is None:
        raise HTTPException(status_code=404, detail=f"Unknown pipeline: {uid}")
    return PipelineRecord(**record)


@router.delete("/{uid}", status_code=204)
def delete_pipeline(uid: str, store: Store = Depends(get_store)) -> Response:
    if not store.delete_pipeline(uid):
        raise HTTPException(status_code=404, detail=f"Unknown pipeline: {uid}")
    return Response(status_code=204)


@router.get("/{uid}/export")
def export_pipeline(uid: str, store: Store = Depends(get_store)) -> JSONResponse:
    """Download the pipeline in FEDOT's own JSON format.

    The result can be fed straight back into ``Pipeline.load``, which is what
    makes a pipeline built in the browser usable from a script.
    """
    record = store.get_pipeline(uid)
    if record is None:
        raise HTTPException(status_code=404, detail=f"Unknown pipeline: {uid}")

    try:
        pipeline = graph_to_pipeline(record["graph"])
        dumped, _ = pipeline.save()
    except PipelineConversionError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc

    payload = json.loads(dumped) if isinstance(dumped, str) else dumped
    filename = f"{record['name'].replace(' ', '_')}.json"
    return JSONResponse(
        content=payload,
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


@router.post("/import", response_model=PipelineGraph)
def import_pipeline(payload: dict) -> PipelineGraph:
    """Load a pipeline saved by FEDOT (``Pipeline.save``) into the editor."""
    from fedot.core.pipelines.pipeline import Pipeline

    try:
        pipeline = Pipeline()
        pipeline.load(payload)
    except Exception as exc:
        raise HTTPException(status_code=422, detail=f"Not a valid FEDOT pipeline: {exc}") from exc

    return PipelineGraph(**pipeline_to_graph(pipeline))

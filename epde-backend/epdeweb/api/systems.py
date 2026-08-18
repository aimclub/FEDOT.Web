"""Discovered systems of equations, kept beyond the run that found them."""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import Response

from ..schemas import SystemGraph, SystemRecord
from ..storage.sqlite import Store
from .deps import get_store

router = APIRouter(prefix="/systems", tags=["epde systems"])


@router.get("", response_model=list[SystemRecord])
def list_systems(
    run_uid: str | None = Query(default=None),
    store: Store = Depends(get_store),
) -> list[SystemRecord]:
    return [SystemRecord(**record) for record in store.list_systems(run_uid=run_uid)]


@router.get("/{uid}", response_model=SystemRecord)
def get_system(uid: str, store: Store = Depends(get_store)) -> SystemRecord:
    record = store.get_system(uid)
    if record is None:
        raise HTTPException(status_code=404, detail=f"Unknown system: {uid}")
    return SystemRecord(**record)


@router.post("", response_model=SystemRecord, status_code=201)
def save_system(
    graph: SystemGraph,
    name: str = Query(default="Saved system"),
    run_uid: str | None = Query(default=None),
    store: Store = Depends(get_store),
) -> SystemRecord:
    """Keep a candidate from a run's genealogy under a name of its own.

    A run's own artefacts go away when the run is deleted; a system saved here
    does not, which is what makes it usable as the answer to a question rather
    than a by-product of the search that produced it.
    """
    uid = store.save_system(
        graph=graph.model_dump(), name=name, origin="saved", run_uid=run_uid
    )
    record = store.get_system(uid)
    if record is None:  # pragma: no cover
        raise HTTPException(status_code=500, detail="The system could not be saved")
    return SystemRecord(**record)


@router.delete("/{uid}", status_code=204)
def delete_system(uid: str, store: Store = Depends(get_store)) -> Response:
    if not store.delete_system(uid):
        raise HTTPException(status_code=404, detail=f"Unknown system: {uid}")
    return Response(status_code=204)

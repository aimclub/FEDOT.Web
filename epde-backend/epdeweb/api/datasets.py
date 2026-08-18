"""Field datasets: upload, inspect, fix the grid, preview."""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Depends, File, Form, HTTPException, Query, UploadFile
from fastapi.responses import FileResponse, Response

from ..datasets.service import DatasetError, DatasetService
from ..schemas import DatasetPreview, DatasetRecord, UpdateAxesRequest
from ..storage.sqlite import Store
from .deps import get_datasets, get_store

router = APIRouter(prefix="/datasets", tags=["epde datasets"])


@router.get("", response_model=list[DatasetRecord])
def list_datasets(store: Store = Depends(get_store)) -> list[DatasetRecord]:
    return [DatasetRecord(**record) for record in store.list_datasets()]


@router.post("", response_model=DatasetRecord, status_code=201)
async def upload_dataset(
    file: UploadFile = File(...),
    name: str | None = Form(default=None),
    datasets: DatasetService = Depends(get_datasets),
) -> DatasetRecord:
    """Upload a field.

    Accepts a ``.npy`` array, a ``.npz`` bundle of arrays and coordinate
    vectors, or a CSV -- either a numeric matrix or a table with a time column.
    Whatever comes in is normalised to one stored form, and anything that had to
    be guessed comes back in ``warnings`` so it can be corrected before a run.
    """
    content = await file.read()
    try:
        record = datasets.create_from_upload(
            filename=file.filename or "upload", content=content, name=name
        )
    except DatasetError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    return DatasetRecord(**record)


@router.post("/samples/{sample_id}", response_model=DatasetRecord, status_code=201)
def create_sample(
    sample_id: str, datasets: DatasetService = Depends(get_datasets)
) -> DatasetRecord:
    """Materialise one of the built-in fields with a known governing equation."""
    try:
        record = datasets.create_sample(sample_id)
    except DatasetError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    return DatasetRecord(**record)


@router.get("/{uid}", response_model=DatasetRecord)
def get_dataset(uid: str, store: Store = Depends(get_store)) -> DatasetRecord:
    record = store.get_dataset(uid)
    if record is None:
        raise HTTPException(status_code=404, detail=f"Unknown dataset: {uid}")
    return DatasetRecord(**record)


@router.patch("/{uid}/axes", response_model=DatasetRecord)
def update_axes(
    uid: str,
    request: UpdateAxesRequest,
    datasets: DatasetService = Depends(get_datasets),
) -> DatasetRecord:
    """Give the grid its real ranges.

    A file that carried only values arrives with axes running ``0, 1, 2, ...``.
    Every derivative EPDE takes scales with the spacing, so the discovered
    coefficients are wrong by a power of it until this is set -- the structure
    survives, the numbers do not.
    """
    try:
        record = datasets.update_axes(uid, [axis.model_dump() for axis in request.axes])
    except DatasetError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    return DatasetRecord(**record)


@router.get("/{uid}/preview", response_model=DatasetPreview)
def preview_dataset(
    uid: str,
    slice_at: list[int] | None = Query(default=None, description="Index to fix each axis beyond the first two at"),
    datasets: DatasetService = Depends(get_datasets),
) -> DatasetPreview:
    fixed: dict[int, int] | None = None
    if slice_at:
        fixed = {index + 2: value for index, value in enumerate(slice_at)}
    try:
        payload: dict[str, Any] = datasets.preview(uid, fixed)
    except DatasetError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    return DatasetPreview(**payload)


@router.get("/{uid}/export")
def export_dataset(uid: str, datasets: DatasetService = Depends(get_datasets)) -> FileResponse:
    """Download the normalised field, coordinates included."""
    try:
        path = datasets.export_path(uid)
    except DatasetError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    return FileResponse(path, filename=f"{uid}.npz", media_type="application/octet-stream")


@router.delete("/{uid}", status_code=204)
def delete_dataset(uid: str, datasets: DatasetService = Depends(get_datasets)) -> Response:
    if not datasets.delete(uid):
        raise HTTPException(status_code=404, detail=f"Unknown dataset: {uid}")
    return Response(status_code=204)

"""Endpoints for uploading and inspecting datasets."""

from __future__ import annotations

import shutil
import tempfile
from pathlib import Path

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile
from fastapi.responses import Response

from ..datasets.preprocessing import describe_preprocessing
from ..datasets.service import DatasetError, inspect_csv, store_upload, suggest_target
from ..schemas import DatasetRecord, DatasetUploadResult, PreprocessingReport
from ..settings import Settings, get_settings
from ..storage.sqlite import Store, new_uid, utcnow
from .deps import get_store

router = APIRouter(prefix="/datasets", tags=["datasets"])

ALLOWED_SUFFIXES = {".csv", ".tsv", ".txt"}


@router.get("", response_model=list[DatasetRecord])
def list_datasets(store: Store = Depends(get_store)) -> list[DatasetRecord]:
    return [DatasetRecord(**record) for record in store.list_datasets()]


@router.post("", response_model=DatasetUploadResult, status_code=201)
async def upload_dataset(
    file: UploadFile = File(...),
    name: str | None = Form(default=None),
    task: str | None = Form(default=None),
    target: str | None = Form(default=None),
    store: Store = Depends(get_store),
    settings: Settings = Depends(get_settings),
) -> DatasetUploadResult:
    """Accept a CSV, describe its columns and suggest a target."""
    suffix = Path(file.filename or "").suffix.lower()
    if suffix not in ALLOWED_SUFFIXES:
        raise HTTPException(
            status_code=415,
            detail=f"Unsupported file type '{suffix or 'unknown'}'. Upload a CSV, TSV or TXT file.",
        )

    uid = new_uid()
    limit_bytes = int(settings.max_upload_mb * 1024 * 1024)

    # Stream to a temporary file first so an oversized upload never lands in the
    # workspace, and so a failed inspection leaves nothing behind.
    with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as staging:
        staged_path = Path(staging.name)
        written = 0
        while chunk := await file.read(1024 * 1024):
            written += len(chunk)
            if written > limit_bytes:
                staging.close()
                staged_path.unlink(missing_ok=True)
                raise HTTPException(
                    status_code=413,
                    detail=f"The file exceeds the {settings.max_upload_mb:g} MB upload limit",
                )
            staging.write(chunk)

    try:
        inspection = inspect_csv(staged_path)
    except DatasetError as exc:
        staged_path.unlink(missing_ok=True)
        raise HTTPException(status_code=422, detail=str(exc)) from exc

    destination_dir = settings.datasets_dir / uid
    try:
        stored_path = store_upload(staged_path, destination_dir, file.filename or f"{uid}{suffix}")
    except DatasetError as exc:
        staged_path.unlink(missing_ok=True)
        raise HTTPException(status_code=422, detail=str(exc)) from exc

    suggested = suggest_target(inspection["columns"])
    record = {
        "uid": uid,
        "name": name or Path(file.filename or uid).stem,
        "filename": str(stored_path),
        "task": task,
        "target": target or suggested,
        "n_rows": inspection["n_rows"],
        "n_columns": inspection["n_columns"],
        "columns": inspection["columns"],
        "created_at": utcnow(),
    }
    store.save_dataset(record)

    return DatasetUploadResult(
        **record,
        preview=inspection["preview"],
        suggested_target=suggested,
    )


@router.get("/{uid}", response_model=DatasetRecord)
def get_dataset(uid: str, store: Store = Depends(get_store)) -> DatasetRecord:
    record = store.get_dataset(uid)
    if record is None:
        raise HTTPException(status_code=404, detail=f"Unknown dataset: {uid}")
    return DatasetRecord(**record)


@router.get("/{uid}/preview")
def preview_dataset(uid: str, store: Store = Depends(get_store)) -> dict:
    """Re-read the head of a stored dataset."""
    record = store.get_dataset(uid)
    if record is None:
        raise HTTPException(status_code=404, detail=f"Unknown dataset: {uid}")
    try:
        inspection = inspect_csv(Path(record["filename"]))
    except DatasetError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    return {"columns": inspection["columns"], "preview": inspection["preview"], "n_rows": inspection["n_rows"]}


@router.get("/{uid}/preprocessing", response_model=PreprocessingReport)
def preprocessing_report(
    uid: str,
    task: str | None = None,
    target: str | None = None,
    forecast_length: int = 30,
    store: Store = Depends(get_store),
) -> PreprocessingReport:
    """What FEDOT's preprocessing does to this dataset, and the resulting types.

    Runs the framework's own preprocessor rather than re-implementing its rules,
    so what is reported is what a run would actually see.
    """
    record = store.get_dataset(uid)
    if record is None:
        raise HTTPException(status_code=404, detail=f"Unknown dataset: {uid}")

    problem = task or record.get("task") or "classification"
    chosen_target = target or record.get("target")
    if not chosen_target:
        raise HTTPException(status_code=422, detail="No target column is set for this dataset")

    try:
        report = describe_preprocessing(
            Path(record["filename"]),
            problem=problem,
            target=chosen_target,
            forecast_length=forecast_length,
        )
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(
            status_code=422, detail=f"The dataset could not be preprocessed: {exc}"
        ) from exc
    return PreprocessingReport(**report)


@router.patch("/{uid}", response_model=DatasetRecord)
def update_dataset(
    uid: str,
    target: str | None = Form(default=None),
    task: str | None = Form(default=None),
    store: Store = Depends(get_store),
) -> DatasetRecord:
    record = store.get_dataset(uid)
    if record is None:
        raise HTTPException(status_code=404, detail=f"Unknown dataset: {uid}")
    if target is not None:
        known = {column["name"] for column in record["columns"]}
        if target not in known:
            raise HTTPException(status_code=422, detail=f"Column '{target}' is not in this dataset")
        record["target"] = target
    if task is not None:
        record["task"] = task
    store.save_dataset(record)
    return DatasetRecord(**record)


@router.delete("/{uid}", status_code=204)
def delete_dataset(
    uid: str,
    store: Store = Depends(get_store),
    settings: Settings = Depends(get_settings),
) -> Response:
    record = store.get_dataset(uid)
    if record is None:
        raise HTTPException(status_code=404, detail=f"Unknown dataset: {uid}")
    store.delete_dataset(uid)
    shutil.rmtree(settings.datasets_dir / uid, ignore_errors=True)
    return Response(status_code=204)

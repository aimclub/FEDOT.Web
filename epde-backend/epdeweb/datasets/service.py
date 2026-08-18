"""Storing and serving field datasets."""

from __future__ import annotations

import shutil
import tempfile
from pathlib import Path
from typing import Any

import numpy as np

from ..settings import Settings
from ..storage.sqlite import Store, new_uid
from .fields import (
    FieldDataset,
    FieldError,
    build_preview,
    describe_axes,
    describe_variables,
    load_field_file,
    read_dataset,
    write_dataset,
)
from .samples import SAMPLE_BY_ID, build_sample


class DatasetError(ValueError):
    """Raised when a dataset cannot be created or read."""


class DatasetService:
    """Uploads, samples, previews and the grid a run is given."""

    def __init__(self, store: Store, settings: Settings) -> None:
        self._store = store
        self._settings = settings

    # ------------------------------------------------------------------ paths

    def path_for(self, uid: str) -> Path:
        return self._settings.datasets_dir / f"{uid}.npz"

    def load(self, uid: str) -> FieldDataset:
        record = self._store.get_dataset(uid)
        if record is None:
            raise DatasetError(f"Unknown dataset: {uid}")
        try:
            return read_dataset(Path(record["filename"]))
        except (FieldError, OSError, ValueError) as exc:
            raise DatasetError(f"The stored field could not be read: {exc}") from exc

    # ---------------------------------------------------------------- creation

    def create_from_upload(self, *, filename: str, content: bytes, name: str | None = None) -> dict[str, Any]:
        limit = self._settings.max_upload_mb * 1024 * 1024
        if len(content) > limit:
            raise DatasetError(
                f"The file is {len(content) / 1024 / 1024:.1f} MB; the limit is "
                f"{self._settings.max_upload_mb:g} MB"
            )

        # numpy needs a real file for .npy / .npz, and the parsers are all
        # file-based, so the upload lands in a temporary file first and is only
        # moved into the workspace once it has been understood.
        suffix = Path(filename).suffix or ".bin"
        with tempfile.NamedTemporaryFile(suffix=suffix, delete=False) as handle:
            handle.write(content)
            staged = Path(handle.name)

        try:
            dataset = load_field_file(staged, original_name=filename)
            dataset.validate()
            self._check_size(dataset)
            return self._store_dataset(
                dataset,
                name=name or Path(filename).stem,
                origin=f"upload:{filename}",
            )
        except FieldError as exc:
            raise DatasetError(str(exc)) from exc
        finally:
            staged.unlink(missing_ok=True)

    def create_sample(self, sample_id: str) -> dict[str, Any]:
        """Materialise one of the built-in fields, reusing it if it exists."""
        if sample_id not in SAMPLE_BY_ID:
            raise DatasetError(f"Unknown sample: {sample_id}")
        origin = f"sample:{sample_id}"
        existing = self._store.find_dataset_by_origin(origin)
        if existing is not None and Path(existing["filename"]).exists():
            return existing

        sample, dataset = build_sample(sample_id)
        dataset.validate()
        return self._store_dataset(
            dataset,
            name=sample.name,
            origin=origin,
            note=f"Expected equation: {sample.expected}",
        )

    def _store_dataset(
        self,
        dataset: FieldDataset,
        *,
        name: str,
        origin: str,
        note: str | None = None,
    ) -> dict[str, Any]:
        uid = new_uid()
        path = self.path_for(uid)
        write_dataset(path, dataset)

        record = {
            "uid": uid,
            "name": name,
            "filename": str(path),
            "kind": "series" if len(dataset.shape) == 1 else "field",
            "variables": describe_variables(dataset.variables),
            "axes": describe_axes(dataset.axes, dataset.axis_names),
            "shape": list(dataset.shape),
            "origin": origin,
            "note": note or dataset.note,
        }
        self._store.save_dataset(record)
        stored = self._store.get_dataset(uid)
        assert stored is not None
        stored["warnings"] = list(dataset.warnings)
        return stored

    def _check_size(self, dataset: FieldDataset) -> None:
        nodes = int(np.prod(dataset.shape))
        if nodes > self._settings.max_grid_nodes:
            raise DatasetError(
                f"The field has {nodes:,} grid nodes; this server allows "
                f"{self._settings.max_grid_nodes:,}. Derivative preprocessing scales with the "
                "node count, so a larger field would take hours. Subsample it before uploading."
            )

    # ----------------------------------------------------------------- editing

    def update_axes(self, uid: str, axes: list[dict[str, Any]]) -> dict[str, Any]:
        """Replace the coordinate vectors with evenly spaced ranges.

        The common case by far: a file that carried only values, so the axes
        came in as ``0, 1, 2, ...`` and every derivative is off by the true
        spacing. Rewriting them here is the fix, and it has to rewrite the
        stored field because the grid is part of the data, not a display option.
        """
        record = self._store.get_dataset(uid)
        if record is None:
            raise DatasetError(f"Unknown dataset: {uid}")
        dataset = self.load(uid)

        if len(axes) != len(dataset.axes):
            raise DatasetError(
                f"The field has {len(dataset.axes)} axes; {len(axes)} were given"
            )

        names: list[str] = []
        vectors: list[np.ndarray] = []
        for index, (requested, current) in enumerate(zip(axes, dataset.axes, strict=True)):
            size = int(current.size)
            name = str(requested.get("name") or dataset.axis_names[index]).strip()
            if not name:
                raise DatasetError(f"Axis {index} needs a name")
            start = requested.get("start")
            stop = requested.get("stop")
            if start is None or stop is None:
                vectors.append(np.asarray(current, dtype=float))
            else:
                start, stop = float(start), float(stop)
                if stop == start:
                    raise DatasetError(f"Axis '{name}' has a zero-length range")
                vectors.append(np.linspace(start, stop, size))
            names.append(name)

        if len(set(names)) != len(names):
            raise DatasetError("Axis names must be distinct")

        updated = FieldDataset(
            variables=dataset.variables, axes=vectors, axis_names=names, note=dataset.note
        )
        updated.validate()
        write_dataset(Path(record["filename"]), updated)

        record["axes"] = describe_axes(updated.axes, updated.axis_names)
        self._store.save_dataset(record)
        stored = self._store.get_dataset(uid)
        assert stored is not None
        return stored

    def delete(self, uid: str) -> bool:
        record = self._store.get_dataset(uid)
        if record is None:
            return False
        Path(record["filename"]).unlink(missing_ok=True)
        return self._store.delete_dataset(uid)

    # ----------------------------------------------------------------- preview

    def preview(self, uid: str, slice_index: dict[int, int] | None = None) -> dict[str, Any]:
        return build_preview(self.load(uid), slice_index=slice_index)

    def export_path(self, uid: str) -> Path:
        record = self._store.get_dataset(uid)
        if record is None:
            raise DatasetError(f"Unknown dataset: {uid}")
        path = Path(record["filename"])
        if not path.exists():
            raise DatasetError("The stored field is missing from the workspace")
        return path

    # ------------------------------------------------------------- maintenance

    def prune_orphans(self) -> int:
        """Delete stored fields no record points at, e.g. after a crashed upload."""
        known = {Path(record["filename"]).name for record in self._store.list_datasets()}
        removed = 0
        for path in self._settings.datasets_dir.glob("*.npz"):
            if path.name not in known:
                path.unlink(missing_ok=True)
                removed += 1
        return removed


def copy_into(path: Path, destination: Path) -> None:  # pragma: no cover - trivial
    destination.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(path, destination)

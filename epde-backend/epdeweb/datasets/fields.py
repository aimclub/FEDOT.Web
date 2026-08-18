"""Reading, storing and describing gridded field data.

Whatever a user uploads -- a ``.npy`` array, an ``.npz`` bundle, a CSV matrix or
a CSV time series -- is normalised into one canonical form: an ``.npz`` holding
``var__<name>`` arrays that all share a shape, and one ``axis__<name>`` vector
per dimension. Everything downstream (the preview, the run worker, the solver
grids) reads that single form, so the format-guessing happens exactly once, at
upload, where a wrong guess can still be corrected by hand.

The axes matter more than they look. EPDE differentiates with respect to the
coordinates it is given, so an axis left as ``0, 1, 2, ...`` when the real
spacing is ``0.01`` scales every first derivative by a hundred and every second
by ten thousand. The discovered *structure* survives that; the coefficients do
not. So an axis is stored explicitly, its uniformity is checked, and a
non-uniform one is flagged rather than quietly accepted.
"""

from __future__ import annotations

import csv
import io
import math
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import numpy as np

#: Default axis names, in the order EPDE expects them: time first, because its
#: ``time_axis`` parameter defaults to axis 0 and the derivative naming
#: (``du/dx1``) is derived from the same ordering.
DEFAULT_AXIS_NAMES = ("t", "x", "y", "z")

#: Column names that mark the independent variable of a tabular upload.
TIME_COLUMN_NAMES = {"t", "time", "tau", "step"}

#: Largest preview grid handed to the browser, per side.
PREVIEW_SIDE = 160


class FieldError(ValueError):
    """Raised when an upload cannot be read as a field."""


@dataclass
class FieldDataset:
    """A field and the grid it lives on."""

    variables: dict[str, np.ndarray]
    axes: list[np.ndarray]
    axis_names: list[str]
    note: str | None = None
    warnings: list[str] = field(default_factory=list)

    @property
    def shape(self) -> tuple[int, ...]:
        return next(iter(self.variables.values())).shape

    def validate(self) -> None:
        if not self.variables:
            raise FieldError("No field variables were found in the upload")
        shapes = {name: array.shape for name, array in self.variables.items()}
        distinct = set(shapes.values())
        if len(distinct) > 1:
            listed = ", ".join(f"{name}{shape}" for name, shape in shapes.items())
            raise FieldError(f"All variables must share one grid; found {listed}")
        shape = self.shape
        if len(self.axes) != len(shape):
            raise FieldError(
                f"The field has {len(shape)} dimensions but {len(self.axes)} coordinate vectors were given"
            )
        for index, (axis, size) in enumerate(zip(self.axes, shape, strict=True)):
            if axis.ndim != 1 or axis.size != size:
                raise FieldError(
                    f"Coordinate vector {self.axis_names[index]!r} has {axis.size} values "
                    f"for an axis of {size} points"
                )


def axis_from_vector(name: str, values: np.ndarray) -> dict[str, Any]:
    """Describe one coordinate axis, including whether its spacing is even."""
    array = np.asarray(values, dtype=float).reshape(-1)
    size = int(array.size)
    described: dict[str, Any] = {
        "name": name,
        "size": size,
        "start": float(array[0]) if size else 0.0,
        "stop": float(array[-1]) if size else 0.0,
        "uniform": True,
        "step": None,
    }
    if size < 2:
        return described

    steps = np.diff(array)
    step = float(np.mean(steps))
    described["step"] = step
    spread = float(np.max(steps) - np.min(steps))
    scale = abs(step) if step else 1.0
    # EPDE's finite-difference and polynomial preprocessors assume an even grid;
    # saying so up front is better than a silently wrong second derivative.
    described["uniform"] = spread <= 1e-6 * scale
    return described


def describe_axes(axes: list[np.ndarray], names: list[str]) -> list[dict[str, Any]]:
    return [axis_from_vector(name, values) for name, values in zip(names, axes, strict=True)]


def describe_variables(variables: dict[str, np.ndarray]) -> list[dict[str, Any]]:
    described = []
    for name, array in variables.items():
        values = np.asarray(array, dtype=float)
        finite = values[np.isfinite(values)]
        described.append(
            {
                "name": name,
                "min": float(finite.min()) if finite.size else None,
                "max": float(finite.max()) if finite.size else None,
                "mean": float(finite.mean()) if finite.size else None,
                "missing": int(values.size - finite.size),
            }
        )
    return described


# ------------------------------------------------------------------- storage


def write_dataset(path: Path, dataset: FieldDataset) -> None:
    payload: dict[str, np.ndarray] = {}
    for name, array in dataset.variables.items():
        payload[f"var__{name}"] = np.asarray(array, dtype=float)
    for name, values in zip(dataset.axis_names, dataset.axes, strict=True):
        payload[f"axis__{name}"] = np.asarray(values, dtype=float)
    path.parent.mkdir(parents=True, exist_ok=True)
    np.savez_compressed(path, **payload)


def read_dataset(path: Path) -> FieldDataset:
    with np.load(path, allow_pickle=False) as bundle:
        variables = {
            key[len("var__") :]: np.asarray(bundle[key]) for key in bundle.files if key.startswith("var__")
        }
        axis_items = [
            (key[len("axis__") :], np.asarray(bundle[key]))
            for key in bundle.files
            if key.startswith("axis__")
        ]
    if not variables:
        raise FieldError(f"{path.name} holds no field variables")
    # np.savez does not promise key order, but the axes must line up with the
    # array dimensions, so they are re-sorted by the shape they have to match.
    shape = next(iter(variables.values())).shape
    ordered: list[tuple[str, np.ndarray]] = []
    remaining = list(axis_items)
    for size in shape:
        match = next((item for item in remaining if item[1].size == size), None)
        if match is None:
            raise FieldError(f"{path.name} is missing a coordinate vector of length {size}")
        remaining.remove(match)
        ordered.append(match)
    return FieldDataset(
        variables=variables,
        axes=[values for _, values in ordered],
        axis_names=[name for name, _ in ordered],
    )


def grids_for_epde(dataset: FieldDataset) -> list[np.ndarray]:
    """The coordinate tensors EPDE wants: one full-shape array per axis.

    EPDE takes the output of ``numpy.meshgrid(..., indexing='ij')`` rather than
    the 1-D vectors, and the indexing matters: with the default ``'xy'`` the
    first two axes come back transposed, which silently swaps time and space.
    """
    if len(dataset.axes) == 1:
        return [np.asarray(dataset.axes[0], dtype=float)]
    return list(np.meshgrid(*[np.asarray(axis, dtype=float) for axis in dataset.axes], indexing="ij"))


# -------------------------------------------------------------------- loading


def load_field_file(path: Path, *, original_name: str | None = None) -> FieldDataset:
    """Read an uploaded file into the canonical form."""
    suffix = Path(original_name or path.name).suffix.lower()
    if suffix == ".npy":
        return _load_npy(path)
    if suffix == ".npz":
        return _load_npz(path)
    if suffix in {".csv", ".txt", ".tsv", ".dat"}:
        return _load_text(path)
    raise FieldError(
        f"Unsupported file type '{suffix or path.name}'. "
        "Upload a .npy array, a .npz bundle, or a .csv table."
    )


def _load_npy(path: Path) -> FieldDataset:
    array = np.load(path, allow_pickle=False)
    array = np.asarray(array, dtype=float)
    if array.ndim == 0:
        raise FieldError("The array is a scalar; a field needs at least one dimension")
    return _with_default_axes({"u": array}, note="single array")


def _load_npz(path: Path) -> FieldDataset:
    with np.load(path, allow_pickle=False) as bundle:
        arrays = {key: np.asarray(bundle[key], dtype=float) for key in bundle.files}
    if not arrays:
        raise FieldError("The archive is empty")

    # Already in canonical form: round-tripping an exported dataset should not
    # go through the guessing below.
    if any(key.startswith("var__") for key in arrays):
        return read_dataset(path)

    biggest = max(arrays.values(), key=lambda array: array.size)
    shape = biggest.shape
    variables = {name: array for name, array in arrays.items() if array.shape == shape}
    if not variables:  # pragma: no cover - `biggest` always qualifies
        raise FieldError("No array in the archive could be read as a field")

    axis_candidates = {
        name: array
        for name, array in arrays.items()
        if array.ndim == 1 and name not in variables
    }
    axes: list[np.ndarray] = []
    axis_names: list[str] = []
    used: set[str] = set()
    warnings: list[str] = []
    for index, size in enumerate(shape):
        match = next(
            (name for name, array in axis_candidates.items() if name not in used and array.size == size),
            None,
        )
        if match is None:
            axes.append(np.arange(size, dtype=float))
            axis_names.append(_default_axis_name(index, len(shape)))
            warnings.append(
                f"No coordinate vector of length {size} was found for axis {index}; "
                "index positions were used. Set the real range before running a search."
            )
        else:
            used.add(match)
            axes.append(axis_candidates[match])
            axis_names.append(match)

    return FieldDataset(
        variables=variables,
        axes=axes,
        axis_names=axis_names,
        note="npz bundle",
        warnings=warnings,
    )


def _load_text(path: Path) -> FieldDataset:
    text = path.read_text(encoding="utf-8-sig", errors="replace")
    delimiter = _sniff_delimiter(text)
    rows = list(csv.reader(io.StringIO(text), delimiter=delimiter))
    rows = [row for row in rows if any(cell.strip() for cell in row)]
    if not rows:
        raise FieldError("The file is empty")

    header = rows[0]
    has_header = not all(_is_number(cell) for cell in header)
    body = rows[1:] if has_header else rows
    if not body:
        raise FieldError("The file has a header but no data")

    try:
        matrix = np.array([[float(cell) for cell in row] for row in body], dtype=float)
    except ValueError as exc:
        raise FieldError(f"The file has non-numeric values: {exc}") from exc

    if has_header:
        return _tabular_dataset(header, matrix)

    if matrix.ndim != 2:  # pragma: no cover - np.array of rows is always 2-D
        raise FieldError("The file could not be read as a matrix")
    if matrix.shape[0] == 1 or matrix.shape[1] == 1:
        # A single row or column is a one-dimensional field, not a matrix.
        return _with_default_axes({"u": matrix.reshape(-1)}, note="single column")
    return _with_default_axes({"u": matrix}, note="numeric matrix")


def _tabular_dataset(header: list[str], matrix: np.ndarray) -> FieldDataset:
    """A CSV with named columns: one column is the coordinate, the rest are fields.

    This is the ODE case -- a trajectory sampled in time, which EPDE handles as
    a one-dimensional field -- and it is also what a user exports from almost
    any simulation, so it is worth recognising rather than treating as a matrix
    of unknown meaning.
    """
    names = [name.strip() or f"c{index}" for index, name in enumerate(header)]
    if matrix.shape[1] != len(names):
        raise FieldError(
            f"The header names {len(names)} columns but the data has {matrix.shape[1]}"
        )

    time_index = next(
        (index for index, name in enumerate(names) if name.strip().lower() in TIME_COLUMN_NAMES),
        None,
    )
    warnings: list[str] = []
    if time_index is None:
        time_index = 0
        warnings.append(
            f"No column named t or time; '{names[0]}' was taken as the coordinate axis."
        )

    axis_values = matrix[:, time_index]
    variables = {
        names[index]: matrix[:, index] for index in range(len(names)) if index != time_index
    }
    if not variables:
        raise FieldError("The table has only a coordinate column and no variables")

    return FieldDataset(
        variables=variables,
        axes=[axis_values],
        axis_names=[names[time_index]],
        note="table",
        warnings=warnings,
    )


def _with_default_axes(variables: dict[str, np.ndarray], note: str | None = None) -> FieldDataset:
    shape = next(iter(variables.values())).shape
    return FieldDataset(
        variables=variables,
        axes=[np.arange(size, dtype=float) for size in shape],
        axis_names=[_default_axis_name(index, len(shape)) for index in range(len(shape))],
        note=note,
        warnings=[
            "The file carries no coordinates, so index positions were used. "
            "Set the real ranges before running a search: derivatives, and "
            "therefore every coefficient, scale with the grid spacing."
        ],
    )


def _default_axis_name(index: int, total: int) -> str:
    if index < len(DEFAULT_AXIS_NAMES):
        return DEFAULT_AXIS_NAMES[index]
    return f"x{index}"


def _sniff_delimiter(text: str) -> str:
    sample = "\n".join(text.splitlines()[:5])
    for candidate in (",", ";", "\t", " "):
        if candidate in sample:
            return candidate
    return ","


def _is_number(cell: str) -> bool:
    try:
        float(cell)
        return True
    except ValueError:
        return False


# -------------------------------------------------------------------- preview


def build_preview(dataset: FieldDataset, *, slice_index: dict[int, int] | None = None) -> dict[str, Any]:
    """A small, plottable summary of the field.

    One-dimensional fields come back as series; anything larger comes back as a
    downsampled 2-D grid over the first two axes, with the remaining axes fixed.
    A field of a million nodes is not going through a JSON payload, and a
    picture of the data is the whole point of looking at it before a run.
    """
    shape = dataset.shape
    if len(shape) == 1:
        axis = np.asarray(dataset.axes[0], dtype=float)
        step = max(1, axis.size // (PREVIEW_SIDE * 4))
        return {
            "kind": "series",
            "axes": describe_axes(dataset.axes, dataset.axis_names),
            "x": axis[::step].tolist(),
            "series": [
                {"name": name, "values": np.asarray(values, dtype=float)[::step].tolist()}
                for name, values in dataset.variables.items()
            ],
        }

    fixed = dict(slice_index or {})
    for index in range(2, len(shape)):
        fixed.setdefault(index, shape[index] // 2)

    row_step = max(1, shape[0] // PREVIEW_SIDE)
    column_step = max(1, shape[1] // PREVIEW_SIDE)

    surfaces = []
    for name, values in dataset.variables.items():
        array = np.asarray(values, dtype=float)
        selector: list[Any] = [slice(None), slice(None)]
        for index in range(2, len(shape)):
            selector.append(fixed[index])
        plane = array[tuple(selector)]
        plane = plane[::row_step, ::column_step]
        finite = plane[np.isfinite(plane)]
        surfaces.append(
            {
                "name": name,
                "values": [[_finite(value) for value in row] for row in plane.tolist()],
                "min": float(finite.min()) if finite.size else 0.0,
                "max": float(finite.max()) if finite.size else 0.0,
            }
        )

    return {
        "kind": "field",
        "axes": describe_axes(dataset.axes, dataset.axis_names),
        "rows": np.asarray(dataset.axes[0], dtype=float)[::row_step].tolist(),
        "columns": np.asarray(dataset.axes[1], dtype=float)[::column_step].tolist(),
        "fixed": {dataset.axis_names[index]: value for index, value in fixed.items()},
        "surfaces": surfaces,
    }


def _finite(value: float) -> float | None:
    return None if value is None or math.isnan(value) or math.isinf(value) else float(value)

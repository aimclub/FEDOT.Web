"""Dataset intake: upload, inspection and preview.

The legacy GUI could only work with three datasets baked into the repository and
seeded into MongoDB.  Here a user can upload their own CSV, see what is in it and
pick a target column before configuring a run.
"""

from __future__ import annotations

import csv
import math
import shutil
from pathlib import Path
from typing import Any

#: Rows read to infer column types and to build the preview.
INSPECTION_ROWS = 500

#: Delimiters tried when sniffing a CSV.
CANDIDATE_DELIMITERS = ",;\t|"


class DatasetError(ValueError):
    """Raised when an uploaded file cannot be used as a dataset."""


def _sniff_delimiter(sample: str) -> str:
    try:
        dialect = csv.Sniffer().sniff(sample, delimiters=CANDIDATE_DELIMITERS)
        return dialect.delimiter
    except csv.Error:
        # Fall back to whichever candidate appears most often in the header line.
        header = sample.splitlines()[0] if sample else ""
        counts = {d: header.count(d) for d in CANDIDATE_DELIMITERS}
        best = max(counts, key=counts.get)
        return best if counts[best] else ","


def _looks_numeric(value: str) -> bool:
    if value == "":
        return False
    try:
        number = float(value)
    except ValueError:
        return False
    return not math.isnan(number)


def _infer_column_type(values: list[str]) -> str:
    non_empty = [v for v in values if v not in ("", "nan", "NaN", "NA", "null", "None")]
    if not non_empty:
        return "empty"
    if all(_looks_numeric(v) for v in non_empty):
        # A small number of distinct integers reads better as a category.
        distinct = set(non_empty)
        if len(distinct) <= 10 and all(float(v).is_integer() for v in distinct):
            return "categorical_numeric"
        return "numeric"
    return "categorical"


def inspect_csv(path: Path) -> dict[str, Any]:
    """Read the head of a CSV and describe its columns."""
    try:
        raw = path.read_text(encoding="utf-8", errors="replace")
    except OSError as exc:
        raise DatasetError(f"Cannot read the uploaded file: {exc}") from exc

    if not raw.strip():
        raise DatasetError("The uploaded file is empty")

    delimiter = _sniff_delimiter(raw[:8192])
    reader = csv.reader(raw.splitlines(), delimiter=delimiter)

    try:
        header = next(reader)
    except StopIteration as exc:
        raise DatasetError("The uploaded file has no header row") from exc

    header = [name.strip() or f"column_{i}" for i, name in enumerate(header)]
    if len(header) < 2:
        raise DatasetError(
            "At least two columns are required: one or more features and a target"
        )

    sample_rows: list[list[str]] = []
    total_rows = 0
    for row in reader:
        total_rows += 1
        if len(sample_rows) < INSPECTION_ROWS:
            # Pad or trim ragged rows so the preview stays rectangular.
            normalised = (row + [""] * len(header))[: len(header)]
            sample_rows.append(normalised)

    columns: list[dict[str, Any]] = []
    for index, name in enumerate(header):
        values = [row[index] for row in sample_rows]
        non_empty = [v for v in values if v != ""]
        columns.append(
            {
                "name": name,
                "index": index,
                "type": _infer_column_type(values),
                "distinct_sample": len(set(non_empty)),
                "missing_sample": len(values) - len(non_empty),
                "examples": non_empty[:3],
            }
        )

    return {
        "delimiter": delimiter,
        "columns": columns,
        "n_rows": total_rows,
        "n_columns": len(header),
        # Ragged rows were padded to the header width above, so the lengths match.
        "preview": [dict(zip(header, row, strict=True)) for row in sample_rows[:20]],
    }


def suggest_target(columns: list[dict[str, Any]]) -> str | None:
    """Guess the target column, preferring FEDOT's own convention."""
    names = {column["name"].lower(): column["name"] for column in columns}
    for candidate in ("target", "label", "class", "y"):
        if candidate in names:
            return names[candidate]
    return columns[-1]["name"] if columns else None


def store_upload(source: Path, destination_dir: Path, filename: str) -> Path:
    """Move an uploaded file into the workspace under a safe name."""
    safe_name = Path(filename).name.replace("\\", "_").replace("/", "_")
    if not safe_name:
        raise DatasetError("The uploaded file has no usable name")
    destination_dir.mkdir(parents=True, exist_ok=True)
    destination = destination_dir / safe_name
    shutil.move(str(source), destination)
    return destination

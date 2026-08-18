"""What FEDOT does to a dataset before a pipeline ever sees it.

A pipeline is only half the story: FEDOT rewrites the input first -- dropping
columns that are almost entirely empty, dropping columns whose types conflict
beyond repair, turning numeric columns with few distinct values into categories
and sparse categorical ones back into numbers. None of that is visible from the
pipeline graph, and it changes what the model is actually trained on.

This module runs FEDOT's own preprocessor over a dataset and reports what it did,
column by column, together with the types the pipeline finally receives.

Index bookkeeping matters here. Obligatory preprocessing filters columns in two
passes, and each pass renumbers what follows: first the gap filter drops columns
(``ids_relevant_features`` holds the *original* indices of the survivors), then
the type corrector works on the filtered matrix, so all of its indices are
positions in that matrix, not in the file. Everything reported below is mapped
back to file columns, so the report reads against the data the user uploaded.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

#: Rows read for the report. The preprocessor's decisions are threshold-based, so
#: this has to be the whole column to be faithful -- but a guard keeps a huge file
#: from stalling the request.
MAX_ROWS_FOR_REPORT = 200_000


def _type_name(type_id: Any) -> str:
    """FEDOT stores column types as ids into a fixed tuple of Python types."""
    from fedot.preprocessing.data_types import ID_TO_TYPE

    try:
        python_type = ID_TO_TYPE[int(type_id)]
    except (KeyError, TypeError, ValueError):
        return str(type_id)
    return getattr(python_type, "__name__", str(python_type))


def _as_int_list(values: Any) -> list[int]:
    if values is None:
        return []
    try:
        return [int(value) for value in list(values)]
    except (TypeError, ValueError):
        return []


def describe_preprocessing(
    path: Path,
    *,
    problem: str,
    target: str,
    forecast_length: int = 30,
) -> dict[str, Any]:
    """Run FEDOT's preprocessing over a dataset and report what changed."""
    from fedot.core.data.data import InputData
    from fedot.core.repository.tasks import Task, TaskTypesEnum, TsForecastingParams
    from fedot.preprocessing.preprocessing import DataPreprocessor

    task_params = (
        TsForecastingParams(forecast_length=forecast_length)
        if problem == "ts_forecasting"
        else None
    )
    task = Task(TaskTypesEnum(problem), task_params)

    if problem == "ts_forecasting":
        data = InputData.from_csv_time_series(file_path=path, task=task, target_column=target)
    else:
        data = InputData.from_csv(file_path=path, task=task, target_columns=target)

    rows_before = int(len(data.idx))
    if rows_before > MAX_ROWS_FOR_REPORT:
        raise ValueError(
            f"This dataset has {rows_before} rows; the preprocessing report is limited to "
            f"{MAX_ROWS_FOR_REPORT}"
        )

    features_shape = getattr(data.features, "shape", (rows_before, 0))
    columns_before = int(features_shape[1]) if len(features_shape) > 1 else 1

    preprocessor = DataPreprocessor()
    prepared = preprocessor.obligatory_prepare_for_fit(data)

    corrector = getattr(preprocessor, "types_correctors", None)
    # The corrector is kept per data source; a single table has one.
    if isinstance(corrector, dict):
        corrector = next(iter(corrector.values()), None)

    # ---------------------------------------------------------- column mapping

    relevant = getattr(preprocessor, "ids_relevant_features", None)
    kept_after_gaps = _as_int_list(next(iter(relevant.values()), None)) if isinstance(relevant, dict) else []
    if not kept_after_gaps:
        # An empty id list means FEDOT skipped the filter and kept everything.
        kept_after_gaps = list(range(columns_before))
    dropped_for_gaps = sorted(set(range(columns_before)) - set(kept_after_gaps))

    def to_file_column(position: int) -> int:
        """Corrector position -> index of the column in the uploaded file."""
        return kept_after_gaps[position] if position < len(kept_after_gaps) else position

    conflict_positions = _as_int_list(getattr(corrector, "columns_to_del", None)) if corrector else []
    dropped_for_conflicts = sorted(to_file_column(p) for p in conflict_positions)

    #: File columns still present in the matrix the pipeline receives, in order.
    surviving = [
        kept_after_gaps[position]
        for position in range(len(kept_after_gaps))
        if position not in set(conflict_positions)
    ]

    # ------------------------------------------------------------- final types

    col_type_ids = getattr(getattr(prepared, "supplementary_data", None), "col_type_ids", None)
    raw_final = []
    if isinstance(col_type_ids, dict) and col_type_ids.get("features") is not None:
        raw_final = list(col_type_ids["features"])

    #: One entry per file column; ``None`` where the column did not survive.
    final_types: list[str | None] = [None] * columns_before
    for position, file_column in enumerate(surviving):
        if position < len(raw_final) and file_column < columns_before:
            final_types[file_column] = _type_name(raw_final[position])

    features_after = getattr(prepared.features, "shape", (0, 0))
    rows_after = int(features_after[0]) if features_after else 0
    columns_after = int(features_after[1]) if len(features_after) > 1 else 1

    # ------------------------------------------------------------ target type

    target_type = None
    target_type_ids = getattr(corrector, "target_type_ids", None) if corrector else None
    target_ids_list = _as_int_list(target_type_ids)
    if target_ids_list:
        target_type = _type_name(target_ids_list[0])

    return {
        "problem": problem,
        "target": target,
        "rows": {"before": rows_before, "after": rows_after},
        "columns": {"before": columns_before, "after": columns_after},
        "source_types": _summarise_source_types(
            corrector, columns_before, to_file_column, dropped_for_gaps
        ),
        "final_types": final_types,
        "target_type": target_type,
        "steps": _describe_steps(
            preprocessor, corrector, to_file_column, dropped_for_gaps, dropped_for_conflicts
        ),
        "note": (
            "This is FEDOT's obligatory preprocessing — the part applied to every run, "
            "before any pipeline. Encoding and imputation that belong to the pipeline "
            "itself appear as nodes in the pipeline graph instead."
        ),
    }


def _summarise_source_types(
    corrector: Any,
    columns_before: int,
    to_file_column,
    dropped_for_gaps: list[int],
) -> list[dict[str, Any]]:
    """Per-column counts of what the raw file actually held, in file order.

    ``features_columns_info`` is a frame indexed by the facts the corrector
    gathered -- how many ints, floats, strings and gaps each column had. That is
    exactly what its decisions were made from, so it belongs in the report.
    Columns the gap filter removed never reach the corrector, so their rows only
    say that much.
    """
    rows: dict[int, dict[str, Any]] = {index: {"column": index} for index in range(columns_before)}
    for index in dropped_for_gaps:
        rows[index]["types"] = []
        rows[index]["dropped_for_gaps"] = True

    info = getattr(corrector, "features_columns_info", None) if corrector else None
    if info is not None and not getattr(info, "empty", True):
        for position in info.columns:
            entry = rows.get(to_file_column(int(position)))
            if entry is None:
                continue
            for field in info.index:
                value = info.loc[field, position]
                if field == "nan_ids":
                    # The positions themselves are noise; the count is the fact.
                    entry["nan_number"] = 0 if value is None else int(len(value))
                    continue
                if field == "types":
                    # These arrive as numpy arrays, whose truthiness is ambiguous,
                    # so the emptiness check has to be explicit.
                    found = [] if value is None else list(value)
                    entry["types"] = sorted({_type_name(t) for t in found})
                    continue
                try:
                    entry[str(field)] = int(value)
                except (TypeError, ValueError):
                    entry[str(field)] = str(value)

    return [rows[index] for index in range(columns_before)]


def _describe_steps(
    preprocessor: Any,
    corrector: Any,
    to_file_column,
    dropped_for_gaps: list[int],
    dropped_for_conflicts: list[int],
) -> list[dict[str, Any]]:
    """The decisions the preprocessor made, in the order it makes them."""

    def step(step_id: str, title: str, detail: str, columns: list[int]) -> dict[str, Any]:
        return {
            "id": step_id,
            "title": title,
            "detail": detail,
            "columns": sorted(columns),
            "applied": bool(columns),
        }

    def mapped(attribute: str) -> list[int]:
        positions = _as_int_list(getattr(corrector, attribute, None)) if corrector else []
        return [to_file_column(position) for position in positions]

    failed = getattr(corrector, "string_columns_transformation_failed", None) if corrector else None
    failed_columns = [to_file_column(int(position)) for position in (failed or {})]

    steps = [
        step(
            "empty_columns",
            "Columns dropped as almost entirely empty",
            "A column that is more than 90% gaps has nothing to learn from, so FEDOT removes it.",
            dropped_for_gaps,
        ),
        step(
            "type_conflicts",
            "Columns dropped for irreconcilable types",
            "A column holding roughly as many genuine strings as numbers cannot be "
            "converted either way, so FEDOT removes it.",
            dropped_for_conflicts,
        ),
        step(
            "numeric_to_categorical",
            "Numeric columns treated as categories",
            "Fewer distinct values than FEDOT's threshold, so the numbers are labels.",
            mapped("numerical_into_str"),
        ),
        step(
            "categorical_to_numeric",
            "Categorical columns converted to numbers",
            "Enough distinct numeric-looking values that a numeric column is a better fit.",
            mapped("categorical_into_float"),
        ),
        step(
            "conversion_failed",
            "Columns kept as text after a failed numeric conversion",
            "Some cells could not be parsed as numbers, so the column stays categorical.",
            failed_columns,
        ),
    ]

    encoders = getattr(preprocessor, "features_encoders", None)
    if isinstance(encoders, dict) and encoders:
        steps.append(
            {
                "id": "encoding",
                "title": "Categorical encoding",
                "detail": ", ".join(type(encoder).__name__ for encoder in encoders.values()),
                "columns": [],
                "applied": True,
            }
        )

    return steps

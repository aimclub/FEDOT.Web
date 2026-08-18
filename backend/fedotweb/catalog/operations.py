"""The catalogue of operations FEDOT can place into a pipeline.

Everything the UI needs to render an operation palette and to validate a node
comes from FEDOT's own repositories: which tasks an operation supports, which
data types it consumes and produces, whether it may sit at the root of a
pipeline, and -- via :mod:`fedotweb.catalog.hyperparams` -- what its
hyperparameters look like.
"""

from __future__ import annotations

import json
from functools import lru_cache
from pathlib import Path
from typing import Any

from fedot.core.repository import operation_types_repository as _otr_module
from fedot.core.repository.operation_types_repository import OperationMetaInfo, OperationTypesRepository
from fedot.core.repository.tasks import TaskTypesEnum

from .hyperparams import HyperparameterCatalog

#: Repository files, in the order the UI should group them.
REPOSITORY_KINDS = ("data_operation", "model")

#: Coarse groups used to colour nodes in the pipeline editor.  The first tag that
#: matches wins, so more specific groups must come first.
TAG_GROUPS: dict[str, str] = {
    "data_source": "source",
    "imputation": "preprocessing",
    "encoding": "preprocessing",
    "feature_scaling": "preprocessing",
    "feature_reduction": "feature_engineering",
    "feature_selection": "feature_engineering",
    "feature_engineering": "feature_engineering",
    "feature_space_transformation": "feature_engineering",
    "text": "preprocessing",
    "imbalanced": "preprocessing",
    "filtering": "preprocessing",
    "smoothing": "preprocessing",
    "ts_to_table": "ts_transform",
    "ts_to_ts": "ts_transform",
    "decompose": "ts_transform",
    "ts_model": "ts_model",
    "boosting": "ensemble",
    "tree": "tree",
    "linear": "linear",
    "non_linear": "non_linear",
    "deep": "deep",
}


def _enum_name(value: Any) -> str:
    """Render a FEDOT enum (or anything else) as a short string."""
    name = getattr(value, "name", None)
    return name if isinstance(name, str) else str(value)


@lru_cache(maxsize=1)
def _repository_metadata() -> dict[str, dict[str, Any]]:
    """Descriptions and tags declared in the repository JSON files.

    ``OperationMetaInfo`` does not carry the human-readable ``description``
    field, so it is read straight from the packaged repository data.
    """
    data_dir = Path(_otr_module.__file__).parent / "data"
    merged: dict[str, dict[str, Any]] = {}
    for kind in REPOSITORY_KINDS:
        path = data_dir / f"{kind}_repository.json"
        if not path.exists():
            continue
        content = json.loads(path.read_text(encoding="utf-8"))
        metadata = content.get("metadata", {})
        for operation_id, entry in content.get("operations", {}).items():
            meta_key = entry.get("meta")
            meta = metadata.get(meta_key, {}) if meta_key else {}
            merged[operation_id] = {
                "kind": kind,
                "family": meta_key,
                "description": meta.get("description"),
                "presets": entry.get("presets", []),
            }
    return merged


def _group_for(tags: list[str], kind: str) -> str:
    for tag in tags:
        group = TAG_GROUPS.get(tag)
        if group:
            return group
    return "data_operation" if kind == "data_operation" else "model"


class OperationCatalog:
    """Read-only view over the FEDOT operation repositories."""

    def __init__(self) -> None:
        # Instantiating the repository is what loads the JSON files; FEDOT caches
        # them on the class, so repeated construction is cheap.
        OperationTypesRepository.init_default_repositories()
        self._repo = OperationTypesRepository(operation_type="all")
        self._hyperparams = HyperparameterCatalog()
        self._metadata = _repository_metadata()

    @property
    def hyperparams(self) -> HyperparameterCatalog:
        return self._hyperparams

    def _describe(self, info: OperationMetaInfo, *, with_parameters: bool) -> dict[str, Any]:
        meta = self._metadata.get(info.id, {})
        tags = list(info.tags or [])
        kind = meta.get("kind") or "model"

        described: dict[str, Any] = {
            "id": info.id,
            "kind": kind,
            "group": _group_for(tags, kind),
            "family": meta.get("family"),
            "description": meta.get("description"),
            "tags": tags,
            "presets": list(info.presets or meta.get("presets") or []),
            "tasks": [_enum_name(t) for t in (info.task_type or [])],
            "input_types": [_enum_name(t) for t in (info.input_types or [])],
            "output_types": [_enum_name(t) for t in (info.output_types or [])],
            "allowed_positions": list(info.allowed_positions or []),
            "is_default": "non-default" not in tags,
        }
        if with_parameters:
            described["parameters"] = self._hyperparams.schema_for(info.id)
            described["defaults"] = self._hyperparams.defaults_for(info.id)
        return described

    def list_operations(
        self,
        *,
        task: str | None = None,
        kind: str | None = None,
        include_non_default: bool = True,
        with_parameters: bool = False,
    ) -> list[dict[str, Any]]:
        """All operations, optionally narrowed to a task type and repository kind."""
        task_type = None
        if task:
            try:
                task_type = TaskTypesEnum(task)
            except ValueError as exc:
                raise ValueError(f"Unknown task type: {task}") from exc

        result: list[dict[str, Any]] = []
        seen = set()
        for info in self._repo.operations:
            if info.id in seen:
                continue
            if task_type is not None and task_type not in (info.task_type or []):
                continue
            described = self._describe(info, with_parameters=with_parameters)
            if kind and described["kind"] != kind:
                continue
            if not include_non_default and not described["is_default"]:
                continue
            seen.add(info.id)
            result.append(described)

        result.sort(key=lambda item: (item["kind"], item["group"], item["id"]))
        return result

    def get(self, operation_id: str) -> dict[str, Any] | None:
        """Full description of a single operation, including parameter schemas."""
        info = self._repo.operation_info_by_id(operation_id)
        if info is None:
            return None
        return self._describe(info, with_parameters=True)

    def exists(self, operation_id: str) -> bool:
        return self._repo.operation_info_by_id(operation_id) is not None

    def tasks(self) -> list[dict[str, str]]:
        """Task types FEDOT can solve, with labels for the run-configuration form."""
        labels = {
            "classification": "Classification",
            "regression": "Regression",
            "ts_forecasting": "Time series forecasting",
            "clustering": "Clustering",
        }
        return [
            {"id": task.value, "label": labels.get(task.value, task.value.replace("_", " ").title())}
            for task in TaskTypesEnum
        ]


@lru_cache(maxsize=1)
def get_catalog() -> OperationCatalog:
    """Process-wide catalogue instance (building it parses several JSON files)."""
    return OperationCatalog()

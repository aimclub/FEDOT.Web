"""Endpoints describing what FEDOT can do: operations, hyperparameters, presets."""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query

from ..catalog import OperationCatalog
from ..schemas import (
    CapabilitiesResponse,
    MetricInfo,
    OperationDetail,
    OperationSummary,
    PresetInfo,
    TaskInfo,
)
from ..settings import Settings, get_settings
from .deps import get_operation_catalog

router = APIRouter(tags=["catalog"])

#: Quality metrics, grouped by the tasks they apply to.  Mirrors the enums in
#: ``fedot.core.repository.metrics_repository``.
METRICS: list[MetricInfo] = [
    MetricInfo(id="roc_auc", label="ROC AUC", tasks=["classification"]),
    MetricInfo(id="accuracy", label="Accuracy", tasks=["classification"]),
    MetricInfo(id="f1", label="F1", tasks=["classification"]),
    MetricInfo(id="precision", label="Precision", tasks=["classification"]),
    MetricInfo(id="neg_log_loss", label="Log loss", tasks=["classification"]),
    MetricInfo(id="rmse", label="RMSE", tasks=["regression", "ts_forecasting"]),
    MetricInfo(id="mse", label="MSE", tasks=["regression", "ts_forecasting"]),
    MetricInfo(id="mae", label="MAE", tasks=["regression", "ts_forecasting"]),
    MetricInfo(id="mape", label="MAPE", tasks=["regression", "ts_forecasting"]),
    MetricInfo(id="smape", label="SMAPE", tasks=["regression", "ts_forecasting"]),
    MetricInfo(id="r2", label="R²", tasks=["regression", "ts_forecasting"]),
    MetricInfo(id="mase", label="MASE", tasks=["ts_forecasting"]),
    MetricInfo(id="node_number", label="Pipeline size (complexity)", tasks=[]),
    MetricInfo(id="structural", label="Structural complexity", tasks=[]),
]

#: FEDOT presets trade composition time against the breadth of the search.
PRESETS: list[PresetInfo] = [
    PresetInfo(id="auto", label="Auto", description="Let FEDOT pick a preset from the data and the time budget"),
    PresetInfo(id="fast_train", label="Fast train", description="Only cheap models — good for a first look"),
    PresetInfo(id="best_quality", label="Best quality", description="The full operation set; needs a large budget"),
    PresetInfo(id="stable", label="Stable", description="Operations that rarely fail on messy data"),
    PresetInfo(id="ts", label="Time series", description="Operations tailored to forecasting"),
    PresetInfo(id="gpu", label="GPU", description="Operations with GPU implementations"),
]


@router.get("/capabilities", response_model=CapabilitiesResponse)
def capabilities(
    catalog: OperationCatalog = Depends(get_operation_catalog),
    settings: Settings = Depends(get_settings),
) -> CapabilitiesResponse:
    """Everything the run-configuration form needs, in one request."""
    import fedot

    golem_version: str | None = None
    try:
        from importlib.metadata import version

        golem_version = version("thegolem")
    except Exception:
        golem_version = None

    from ..epde_module import is_mounted

    return CapabilitiesResponse(
        fedot_version=getattr(fedot, "__version__", "unknown"),
        golem_version=golem_version,
        tasks=[TaskInfo(**task) for task in catalog.tasks()],
        metrics=METRICS,
        presets=PRESETS,
        max_run_timeout_minutes=settings.max_run_timeout_minutes,
        max_concurrent_runs=settings.max_concurrent_runs,
        epde_module=is_mounted(),
    )


@router.get("/operations", response_model=list[OperationSummary])
def list_operations(
    task: str | None = Query(default=None, description="Keep only operations supporting this task"),
    kind: str | None = Query(default=None, description="'model' or 'data_operation'"),
    include_non_default: bool = Query(default=True),
    catalog: OperationCatalog = Depends(get_operation_catalog),
) -> list[OperationSummary]:
    """The operation palette."""
    try:
        operations = catalog.list_operations(
            task=task, kind=kind, include_non_default=include_non_default
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return [OperationSummary(**operation) for operation in operations]


@router.get("/operations/{operation_id}", response_model=OperationDetail)
def get_operation(
    operation_id: str,
    catalog: OperationCatalog = Depends(get_operation_catalog),
) -> OperationDetail:
    """One operation with the typed schema of every hyperparameter it accepts."""
    operation = catalog.get(operation_id)
    if operation is None:
        raise HTTPException(status_code=404, detail=f"Unknown operation: {operation_id}")
    return OperationDetail(**operation)

"""On-demand analyses of a pipeline: where its score came from, and what it rests on.

Both analyses here refit pipelines, which is CPU-bound and can take a while, so
they run in their own process exactly as a composition does.

Run as::

    python -m fedotweb.analysis.worker <job_directory>
"""

from __future__ import annotations

import json
import sys
import traceback
from pathlib import Path
from typing import Any

JOB_FILE = "job.json"
RESULT_FILE = "result.json"

#: Metrics reported alongside the one the run optimised, so a score can be read
#: in more than one currency.
COMPANION_METRICS = {
    "classification": ["roc_auc", "accuracy", "f1", "neg_log_loss"],
    "regression": ["rmse", "mae", "r2"],
    "ts_forecasting": ["rmse", "mae", "smape"],
}


def metric_enum(metric_id: str):
    """Resolve a metric name to the enum member FEDOT indexes its registry by."""
    from fedot.core.repository.metrics_repository import (
        ClassificationMetricsEnum,
        ClusteringMetricsEnum,
        ComplexityMetricsEnum,
        RegressionMetricsEnum,
        TimeSeriesForecastingMetricsEnum,
    )

    for enum in (
        ClassificationMetricsEnum,
        RegressionMetricsEnum,
        TimeSeriesForecastingMetricsEnum,
        ClusteringMetricsEnum,
        ComplexityMetricsEnum,
    ):
        try:
            return enum(metric_id)
        except ValueError:
            continue
    return None


def _is_maximised(metric_enum) -> bool:
    """Whether FEDOT negates this metric to turn it into something to minimise.

    ``from_maximised_metric`` wraps the metric with ``functools.wraps``, so the
    wrapper carries ``__wrapped__`` and metrics that are already minimised do not.
    """
    from fedot.core.repository.metrics_repository import MetricsRepository

    try:
        metric_class = MetricsRepository.get_metric_class(metric_enum)
    except KeyError:
        return False
    return hasattr(getattr(metric_class, "metric", None), "__wrapped__")


def _metrics_for(problem: str, primary: str | None) -> list[str]:
    ordered = list(COMPANION_METRICS.get(problem, []))
    if primary and primary not in ordered:
        ordered.insert(0, primary)
    elif primary:
        ordered.remove(primary)
        ordered.insert(0, primary)
    return ordered


def _load_data(spec: dict[str, Any]):
    """Load the run's dataset and split off the same holdout the run used."""
    from fedot.core.data.data import InputData
    from fedot.core.data.data_split import train_test_data_setup
    from fedot.core.repository.tasks import Task, TaskTypesEnum, TsForecastingParams

    problem = spec["problem"]
    target = spec.get("target") or "target"
    path = Path(spec["dataset_path"])

    task_params = (
        TsForecastingParams(forecast_length=int(spec.get("forecast_length") or 30))
        if problem == "ts_forecasting"
        else None
    )
    task = Task(TaskTypesEnum(problem), task_params)

    if problem == "ts_forecasting":
        data = InputData.from_csv_time_series(file_path=path, task=task, target_column=target)
        blocks = int(spec.get("validation_blocks") or 2)
        train, holdout = train_test_data_setup(data, validation_blocks=blocks)
        return train, holdout, blocks

    data = InputData.from_csv(file_path=path, task=task, target_columns=target)
    # ``seed or 42`` would turn a legitimate seed of 0 into 42 — and this split
    # must reproduce the run worker's exactly, or the holdout stops being held out.
    seed = spec.get("seed")
    train, holdout = train_test_data_setup(
        data,
        split_ratio=1.0 - float(spec.get("holdout_fraction") or 0.2),
        shuffle=True,
        stratify=problem == "classification",
        random_seed=42 if seed is None else int(seed),
    )
    return train, holdout, None


def _evaluate(pipeline, data, metric_ids: list[str], validation_blocks: int | None) -> dict[str, Any]:
    """Every requested metric for one fitted pipeline on one dataset."""
    from fedot.core.repository.metrics_repository import MetricsRepository

    scores: dict[str, Any] = {}
    for metric_id in metric_ids:
        enum = metric_enum(metric_id)
        if enum is None:
            continue
        try:
            value = float(MetricsRepository.get_metric(enum)(pipeline, data, validation_blocks))
        except Exception:
            # A metric that cannot be computed here (wrong number of classes, say)
            # should not cost the whole breakdown.
            scores[metric_id] = None
            continue
        if value != value:  # NaN
            value = None
        scores[metric_id] = value
    return scores


def _readable(metric_id: str, value: float | None) -> float | None:
    """The metric as a person reads it, undoing FEDOT's negation for display."""
    if value is None:
        return None
    enum = metric_enum(metric_id)
    return -value if enum is not None and _is_maximised(enum) else value


def objective_breakdown(spec: dict[str, Any]) -> dict[str, Any]:
    """How the objective value was arrived at, fold by fold.

    FEDOT averages the per-fold metrics and keeps only the average -- that average
    is the fitness evolution compares individuals by. The folds behind it are
    discarded, so they are recomputed here on the same split the composer used.
    """
    from copy import deepcopy

    from fedot.core.optimisers.objective.data_source_splitter import DataSourceSplitter

    from ..pipelines.convert import graph_to_pipeline

    train, holdout, validation_blocks = _load_data(spec)
    metric_ids = _metrics_for(spec["problem"], spec.get("metric"))
    cv_folds = int(spec.get("cv_folds") or 5)
    template = graph_to_pipeline(spec["graph"])

    # The composer builds its folds exactly this way; matching it is what makes
    # the average below equal the fitness the run actually saw.
    producer = DataSourceSplitter(cv_folds, shuffle=True).build(train)

    folds: list[dict[str, Any]] = []
    for fold_id, (fold_train, fold_test) in enumerate(producer()):
        pipeline = deepcopy(template)
        try:
            pipeline.fit(fold_train)
            scores = _evaluate(pipeline, fold_test, metric_ids, validation_blocks)
            folds.append(
                {
                    "fold": fold_id,
                    "train_size": int(len(fold_train.idx)),
                    "test_size": int(len(fold_test.idx)),
                    "metrics": scores,
                    "readable": {k: _readable(k, v) for k, v in scores.items()},
                    "failed": False,
                }
            )
        except Exception as exc:
            folds.append({"fold": fold_id, "failed": True, "error": str(exc), "metrics": {}})
        finally:
            pipeline.unfit()

    # Mean over the folds that produced a value, per metric.
    summary: dict[str, Any] = {}
    for metric_id in metric_ids:
        values = [
            fold["metrics"].get(metric_id)
            for fold in folds
            if not fold["failed"] and fold["metrics"].get(metric_id) is not None
        ]
        if not values:
            summary[metric_id] = None
            continue
        mean = sum(values) / len(values)
        spread = max(values) - min(values)
        summary[metric_id] = {
            "mean": mean,
            "readable_mean": _readable(metric_id, mean),
            "min": min(values),
            "max": max(values),
            "spread": spread,
            "folds_used": len(values),
            "is_maximised": _is_maximised(metric_enum(metric_id)),
        }

    # And the same pipeline scored once on data neither evolution nor the folds saw.
    holdout_scores: dict[str, Any] = {}
    holdout_error: str | None = None
    final = deepcopy(template)
    try:
        final.fit(train)
        holdout_scores = _evaluate(final, holdout, metric_ids, validation_blocks)
    except Exception as exc:
        holdout_error = str(exc)
    finally:
        final.unfit()

    return {
        "kind": "objective",
        "problem": spec["problem"],
        "primary_metric": spec.get("metric") or metric_ids[0] if metric_ids else None,
        "cv_folds": cv_folds,
        "metrics": metric_ids,
        "folds": folds,
        "summary": summary,
        "holdout": {
            "size": int(len(holdout.idx)),
            "metrics": holdout_scores,
            "readable": {k: _readable(k, v) for k, v in holdout_scores.items()},
            "error": holdout_error,
        },
        "note": (
            "Fold metrics are what FEDOT averages into the objective value; the average "
            "below is the fitness evolution compared pipelines by. Values are shown as "
            "FEDOT computes them (negated for metrics it maximises) and, alongside, as "
            "they read normally."
        ),
    }


def sensitivity(spec: dict[str, Any]) -> dict[str, Any]:
    """How much the pipeline's score depends on each node and edge.

    Uses GOLEM's own structural analysis: each node is deleted, replaced and had
    its subtree removed, each edge deleted and replaced, and the resulting change
    in the objective is recorded.
    """
    from fedot.core.pipelines.adapters import PipelineAdapter
    from golem.core.optimisers.objective import Objective
    from golem.structural_analysis.graph_sa.edge_sa_approaches import (
        EdgeDeletionAnalyze,
        EdgeReplaceOperationAnalyze,
    )
    from golem.structural_analysis.graph_sa.graph_structural_analysis import GraphStructuralAnalysis
    from golem.structural_analysis.graph_sa.node_sa_approaches import (
        NodeDeletionAnalyze,
        NodeReplaceOperationAnalyze,
        SubtreeDeletionAnalyze,
    )
    from golem.structural_analysis.graph_sa.sa_requirements import StructuralAnalysisRequirements

    from ..pipelines.convert import graph_to_pipeline
    from .scoring import HoldoutScorer

    train, holdout, validation_blocks = _load_data(spec)
    metric_id = spec.get("metric") or _metrics_for(spec["problem"], None)[0]
    enum = metric_enum(metric_id)
    pipeline = graph_to_pipeline(spec["graph"])

    objective = Objective({metric_id: HoldoutScorer(train, holdout, metric_id, validation_blocks)})

    node_factory = _node_factory(spec)
    replacements = int(spec.get("replacements") or 2)
    requirements = StructuralAnalysisRequirements(
        is_visualize=False,
        is_save_results_to_json=False,
        # Each replacement means another fit, so this is the main cost dial.
        replacement_number_of_random_operations_nodes=replacements,
        replacement_number_of_random_operations_edges=replacements,
    )

    approaches = [NodeDeletionAnalyze, NodeReplaceOperationAnalyze, SubtreeDeletionAnalyze]
    if spec.get("analyse_edges", True):
        approaches += [EdgeDeletionAnalyze, EdgeReplaceOperationAnalyze]

    analysis = GraphStructuralAnalysis(
        objective=objective,
        node_factory=node_factory,
        approaches=approaches,
        requirements=requirements,
        path_to_save=str(Path(spec["job_dir"]) / "sa"),
    )
    # The analysis and its node factory both work on GOLEM's graph representation,
    # not on a FEDOT pipeline; the scorer restores it on the other side.
    results = analysis.analyze(graph=PipelineAdapter().adapt(pipeline), n_jobs=1)

    return {
        "kind": "sensitivity",
        "metric": metric_id,
        "is_maximised": _is_maximised(enum),
        "entities": _flatten_sa(results, pipeline),
        "note": (
            "GOLEM reports each change as a sign-normalised score ratio: above 1 means the "
            "change improved the objective — that part is dead weight or replaceable — and "
            "below 1 means it hurt, so the pipeline relies on the part. Exactly -1 marks a "
            "change that could not be evaluated."
        ),
    }


def _node_factory(spec: dict[str, Any]):
    """The factory structural analysis uses when proposing replacements.

    Restricted to the operations the run itself was allowed to use, so a proposed
    replacement is one the composer could genuinely have chosen.
    """
    from fedot.core.pipelines.pipeline_composer_requirements import PipelineComposerRequirements
    from fedot.core.pipelines.pipeline_node_factory import PipelineOptNodeFactory
    from fedot.core.repository.operation_types_repository import get_operations_for_task
    from fedot.core.repository.tasks import Task, TaskTypesEnum

    task = Task(TaskTypesEnum(spec["problem"]))
    available = spec.get("available_operations") or get_operations_for_task(task=task, mode="all")

    requirements = PipelineComposerRequirements(
        primary=list(available),
        secondary=list(available),
        cv_folds=None,
    )
    return PipelineOptNodeFactory(requirements=requirements)


def _flatten_sa(results: Any, pipeline: Any) -> list[dict[str, Any]]:
    """Turn GOLEM's nested analysis results into rows the UI can table and colour."""
    from golem.structural_analysis.graph_sa.results.utils import EntityTypesEnum

    rows: list[dict[str, Any]] = []
    operations = [node.name for node in pipeline.nodes]

    for iteration, per_type in (results.results_per_iteration or {}).items():
        for entity_type in (EntityTypesEnum.node.value, EntityTypesEnum.edge.value):
            for position, entity_result in enumerate(per_type.get(entity_type) or []):
                approaches: dict[str, Any] = {}
                for approach in getattr(entity_result, "result_approaches", []) or []:
                    name = type(approach).__name__.replace("SAApproachResult", "")
                    try:
                        approaches[name] = approach.get_all_results()
                    except Exception:
                        approaches[name] = None

                # GOLEM identifies a node by its index and an edge by "from_to",
                # which is a surer key than the order results come back in.
                entity = str(getattr(entity_result, "entity_idx", position))
                operation = None
                if entity_type == "node" and entity.isdigit() and int(entity) < len(operations):
                    operation = operations[int(entity)]
                elif entity_type == "edge":
                    ends = [part for part in entity.split("_") if part.isdigit()]
                    if len(ends) == 2:
                        source, target = (int(end) for end in ends)
                        if source < len(operations) and target < len(operations):
                            operation = f"{operations[source]} → {operations[target]}"

                # GOLEM's ratio is sign-normalised (see _compare_with_origin_by_metric):
                # above 1 always means the change IMPROVED the objective, whichever
                # way the metric points -- its own optimize() applies changes at
                # value > 1. The verdict is decided here so no client has to
                # rediscover that convention. Exactly -1 is GOLEM's could-not-
                # evaluate sentinel.
                worst = _worst_of(entity_result)
                value = worst.get("value") if isinstance(worst, dict) else None
                improves: bool | None = None
                severity = 0.0
                if isinstance(value, (int, float)) and value != -1.0:
                    improves = value > 1
                    severity = abs(value - 1)

                rows.append(
                    {
                        "iteration": int(iteration),
                        "entity_type": entity_type,
                        "entity": entity,
                        "operation": operation,
                        "approaches": approaches,
                        "worst": worst,
                        "improves": improves,
                        "severity": severity,
                    }
                )
    return rows


def _worst_of(entity_result: Any) -> dict[str, Any] | None:
    try:
        return entity_result.get_worst_result_with_names(metric_idx_to_optimize_by=0)
    except Exception:
        return None


ANALYSES = {"objective": objective_breakdown, "sensitivity": sensitivity}


def run(job_dir: Path) -> int:
    spec: dict[str, Any] = json.loads((job_dir / JOB_FILE).read_text(encoding="utf-8"))
    spec["job_dir"] = str(job_dir)

    analyse = ANALYSES.get(spec.get("kind", ""))
    if analyse is None:
        payload = {"error": f"Unknown analysis: {spec.get('kind')}"}
    else:
        try:
            payload = {"result": analyse(spec)}
        except Exception as exc:
            payload = {"error": f"{type(exc).__name__}: {exc}", "traceback": traceback.format_exc()}

    (job_dir / RESULT_FILE).write_text(
        json.dumps(payload, ensure_ascii=False, allow_nan=False, default=str), encoding="utf-8"
    )
    return 0 if "result" in payload else 1


def main() -> int:
    if len(sys.argv) < 2:
        print("usage: python -m fedotweb.analysis.worker <job_directory>", file=sys.stderr)
        return 2
    return run(Path(sys.argv[1]))


if __name__ == "__main__":
    raise SystemExit(main())

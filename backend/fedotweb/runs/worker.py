"""Subprocess entry point that runs one FEDOT AutoML job.

Composition is CPU-bound and blocking, and FEDOT may fan out to worker processes
of its own, so a run gets its own process: that keeps the API responsive and
makes cancellation a matter of killing a process tree.

Progress is reported by appending JSON lines to ``events.jsonl`` in the run
directory.  Per-generation events come from GOLEM's iteration callback, which
fires every time a new population is recorded -- so the UI sees the evolution as
it happens instead of waiting for the final ``OptHistory``.

Run as::

    python -m fedotweb.runs.worker <run_directory>
"""

from __future__ import annotations

import json
import os
import sys
import time
import traceback
from pathlib import Path
from typing import Any

EVENTS_FILE = "events.jsonl"
CONFIG_FILE = "config.json"
RESULT_FILE = "result.json"
HISTORY_FILE = "history.json"


class EventWriter:
    """Append-only JSONL sink shared with the parent process."""

    def __init__(self, path: Path) -> None:
        self._path = path
        self._started = time.monotonic()

    def emit(self, kind: str, **payload: Any) -> None:
        record = {
            "kind": kind,
            "elapsed": round(time.monotonic() - self._started, 3),
            "payload": payload,
        }
        line = json.dumps(record, ensure_ascii=False, default=str)
        # Opening per event keeps the file consistent for a reader that tails it
        # while we write, which matters because the reader is a different process.
        with self._path.open("a", encoding="utf-8") as handle:
            handle.write(line + "\n")
            handle.flush()
            os.fsync(handle.fileno())


def _fitness_value(individual: Any) -> float | None:
    """Fitness as a plain number, oriented so that *larger is better*.

    GOLEM minimises internally and stores metrics negated for maximisation
    objectives; ``Fitness.value`` gives the raw comparable number.
    """
    fitness = getattr(individual, "fitness", None)
    if fitness is None:
        return None
    value = getattr(fitness, "value", None)
    if value is None:
        return None
    try:
        number = float(value)
    except (TypeError, ValueError):
        return None
    if number != number or number in (float("inf"), float("-inf")):  # NaN / inf
        return None
    return number


def summarise_population(population: list[Any]) -> dict[str, Any]:
    values = [v for v in (_fitness_value(ind) for ind in population) if v is not None]
    summary: dict[str, Any] = {
        "size": len(population),
        "fitness": values,
    }
    if values:
        summary["best_fitness"] = min(values)
        summary["worst_fitness"] = max(values)
        summary["mean_fitness"] = sum(values) / len(values)
    return summary


#: Keyword arguments the stdlib logger accepts; everything else must be dropped.
_LOGGING_KWARGS = frozenset({"exc_info", "stack_info", "stacklevel", "extra"})


def _patch_logger_kwargs() -> bool:
    """Guard against an upstream logging mismatch killing a run.

    The released FEDOT 0.7.5 calls ``log.warning(..., raise_if_test=True, exc=error)``
    in several error paths -- invalid fitness during evaluation, cache read
    failures. Neither GOLEM 0.4.1 (which that wheel pins) nor 0.4.2 accepts those
    keywords, so they reach ``logging.Logger._log`` and raise ``TypeError``. A
    composition then dies at the first pipeline that scores badly, which is a
    normal event during evolution rather than a fatal one.

    FEDOT master has removed those calls, so against master this wrapper never has
    anything to strip. It stays as a safety net for anyone who installs the PyPI
    release instead, and can be deleted once a release ships the fix.

    ``raise_if_test`` asks to re-raise only inside FEDOT's own test session, so
    dropping it yields exactly the warning that was intended.
    """
    try:
        from golem.core.log import LoggerAdapter
    except ImportError:
        return False

    if getattr(LoggerAdapter, "_fedotweb_kwargs_patched", False):
        return False

    original_log = LoggerAdapter.log

    def log(self, level, msg, *args, **kwargs):
        unsupported = set(kwargs) - _LOGGING_KWARGS
        if unsupported:
            details = ", ".join(f"{key}={kwargs.pop(key)!r}" for key in sorted(unsupported))
            msg = f"{msg} [{details}]"
        return original_log(self, level, msg, *args, **kwargs)

    LoggerAdapter.log = log
    LoggerAdapter._fedotweb_kwargs_patched = True
    return True


def _build_task(problem: str, config: dict[str, Any]):
    from fedot.core.repository.tasks import TsForecastingParams

    if problem == "ts_forecasting":
        return TsForecastingParams(forecast_length=int(config.get("forecast_length") or 30))
    return None


def _compact_graph(individual: Any) -> dict[str, Any] | None:
    """An individual's pipeline as bare structure: operations and their wiring."""
    graph = getattr(individual, "graph", None)
    nodes = getattr(graph, "nodes", None) if graph is not None else None
    if not nodes:
        return None

    index_of = {id(node): f"n{position}" for position, node in enumerate(nodes)}
    described_nodes = []
    edges = []
    for position, node in enumerate(nodes):
        node_id = f"n{position}"
        parameters = getattr(node, "parameters", None)
        described_nodes.append(
            {
                "id": node_id,
                "operation": str(getattr(node, "name", "") or ""),
                "params": parameters if isinstance(parameters, dict) else {},
            }
        )
        for parent in getattr(node, "nodes_from", None) or []:
            parent_id = index_of.get(id(parent))
            if parent_id is not None:
                edges.append({"source": parent_id, "target": node_id})

    return {"nodes": described_nodes, "edges": edges}


def describe_lineage(population: list[Any]) -> list[dict[str, Any]]:
    """Ancestry of one population, compact enough to stream every generation.

    This is what lets the genealogy be drawn while the run is still going: the
    saved ``OptHistory`` only exists once FEDOT finishes, so waiting for it would
    mean no ancestry until the end.
    """
    from ..history.lineage import fitness_value, operations_of, operator_label

    described: list[dict[str, Any]] = []
    for individual in population:
        entry: dict[str, Any] = {
            "uid": str(individual.uid),
            "fitness": fitness_value(individual),
            "operations": operations_of(individual),
            "native_generation": individual.native_generation,
            # Structure and chosen parameters, so a node in the live genealogy can
            # be opened the same way a finished one can. Operation defaults are
            # left out; the client already has them from the catalogue.
            "graph": _compact_graph(individual),
        }

        # Ancestry is sent for every individual; the graph builder decides which
        # generation draws it, from where the individual first appears. Deciding
        # here would mean comparing GOLEM's live generation counter against the
        # value stored on the individual, and the two are offset by one.
        try:
            operators = list(individual.operators_from_prev_generation)
        except ValueError:
            # GOLEM raises when inheritance data is inconsistent.
            operators = []
        entry["operators"] = [
            {
                "uid": str(operator.uid),
                "type": str(operator.type_),
                "label": operator_label(operator),
                "parents": [str(parent.uid) for parent in (operator.parent_individuals or ())],
            }
            for operator in operators
        ]

        described.append(entry)
    return described


def _make_progress_optimizer(events: EventWriter, state: dict[str, Any], run_dir: Path):
    """An ``EvoGraphOptimizer`` that reports each generation and obeys live controls."""
    from golem.core.optimisers.genetic.gp_optimizer import EvoGraphOptimizer

    from .control import apply_controls, describe_effective, install_overrides, read_controls

    def on_iteration(population, optimizer) -> None:
        try:
            generation = int(getattr(optimizer, "current_generation_num", 0))
            members = list(population)
            summary = summarise_population(members)

            best_individuals = list(getattr(optimizer, "best_individuals", None) or [])
            best = serialise_individual(best_individuals[0]) if best_individuals else None

            state["last_generation"] = generation
            events.emit("generation", generation=generation, best_pipeline=best, **summary)

            # Ancestry goes in its own event: it is an order of magnitude larger
            # than the summary, and a client that only wants the fitness curve
            # should not have to parse it.
            events.emit(
                "population",
                generation=generation,
                individuals=describe_lineage(members),
                best_uids=[str(individual.uid) for individual in best_individuals],
            )
        except Exception as exc:  # a reporting failure must never abort the run
            events.emit("log", level="warning", message=f"progress callback failed: {exc}")

        # Controls are applied between generations, never mid-flight.
        try:
            changes = apply_controls(optimizer, read_controls(run_dir))
            if changes:
                events.emit("control_applied", generation=generation, changes=changes)
            # ``describe_effective`` already reports the generation.
            events.emit("effective_params", **describe_effective(optimizer))
        except Exception as exc:
            events.emit("log", level="warning", message=f"could not apply controls: {exc}")

    class ProgressReportingOptimizer(EvoGraphOptimizer):
        def __init__(self, *args, **kwargs):
            super().__init__(*args, **kwargs)
            install_overrides(self)
            self.set_iteration_callback(on_iteration)
            # Anything already requested before the first generation applies now.
            try:
                apply_controls(self, read_controls(run_dir))
            except Exception:
                pass

    return ProgressReportingOptimizer


def serialise_individual(individual: Any) -> dict[str, Any] | None:
    """Turn a GOLEM individual into the editor graph format."""
    try:
        from fedot.core.pipelines.adapters import PipelineAdapter

        from ..pipelines.convert import pipeline_to_graph

        graph = getattr(individual, "graph", None)
        if graph is None:
            return None
        pipeline = PipelineAdapter().restore(graph)
        described = pipeline_to_graph(pipeline)
        described["fitness"] = _fitness_value(individual)
        described["uid"] = str(getattr(individual, "uid", "") or "")
        return described
    except Exception:
        return None


def _load_dataset(config: dict[str, Any]):
    """Load the configured CSV and split it into fit and holdout parts.

    Metrics are reported on data the composer never saw, which is what makes the
    number on the results screen mean something.  FEDOT's own
    ``train_test_data_setup`` is used so that stratification (classification) and
    temporal ordering (forecasting) are handled the way the framework expects.
    """
    from fedot.core.data.data import InputData
    from fedot.core.data.data_split import train_test_data_setup
    from fedot.core.repository.tasks import Task, TaskTypesEnum

    path = config.get("dataset_path")
    if not path:
        raise ValueError("No dataset was supplied for the run")
    dataset_path = Path(path)
    if not dataset_path.exists():
        raise ValueError(f"The dataset file is missing: {dataset_path}")

    problem = config["problem"]
    target = config.get("target") or "target"
    task = Task(TaskTypesEnum(problem), _build_task(problem, config))

    if problem == "ts_forecasting":
        data = InputData.from_csv_time_series(
            file_path=dataset_path, task=task, target_column=target
        )
        validation_blocks = int(config.get("validation_blocks") or 2)
        train, test = train_test_data_setup(data, validation_blocks=validation_blocks)
        return train, test, validation_blocks

    data = InputData.from_csv(file_path=dataset_path, task=task, target_columns=target)
    split_ratio = 1.0 - float(config.get("holdout_fraction") or 0.2)
    # ``seed or 42`` would turn a legitimate seed of 0 into 42; the analysis
    # worker mirrors this split, so both derive the seed the same way.
    seed = config.get("seed")
    train, test = train_test_data_setup(
        data,
        split_ratio=split_ratio,
        shuffle=True,
        stratify=problem == "classification",
        random_seed=42 if seed is None else int(seed),
    )
    return train, test, None


def run(run_dir: Path) -> int:
    config: dict[str, Any] = json.loads((run_dir / CONFIG_FILE).read_text(encoding="utf-8"))
    events = EventWriter(run_dir / EVENTS_FILE)
    state: dict[str, Any] = {"last_generation": 0}

    events.emit("status", status="starting", pid=os.getpid())

    try:
        _patch_logger_kwargs()

        from fedot.api.main import Fedot

        problem = config["problem"]
        events.emit("status", status="loading_data", dataset=str(config.get("dataset_path")))
        train_data, test_data, validation_blocks = _load_dataset(config)
        events.emit(
            "log",
            level="info",
            message=f"fit on {len(train_data.idx)} rows, holdout {len(test_data.idx)} rows",
        )

        composer_params: dict[str, Any] = {
            "pop_size": int(config.get("pop_size") or 20),
            "num_of_generations": int(config.get("num_of_generations") or 20),
            "max_depth": int(config.get("max_depth") or 6),
            "max_arity": int(config.get("max_arity") or 4),
            "with_tuning": bool(config.get("with_tuning", True)),
            "cv_folds": int(config.get("cv_folds") or 5),
            "early_stopping_iterations": config.get("early_stopping_iterations"),
        }
        if config.get("metric"):
            composer_params["metric"] = config["metric"]
        if config.get("available_operations"):
            composer_params["available_operations"] = list(config["available_operations"])
        if config.get("initial_pipeline"):
            from ..pipelines.convert import graph_to_pipeline

            composer_params["initial_assumption"] = graph_to_pipeline(config["initial_pipeline"])

        composer_params = {k: v for k, v in composer_params.items() if v is not None}

        model = Fedot(
            problem=problem,
            timeout=float(config.get("timeout") or 5.0),
            seed=config.get("seed"),
            n_jobs=int(config.get("n_jobs") or 1),
            logging_level=int(config.get("logging_level") or 20),
            task_params=_build_task(problem, config),
            preset=config.get("preset") or "auto",
            optimizer=_make_progress_optimizer(events, state, run_dir),
            **composer_params,
        )

        events.emit("status", status="composing")
        model.fit(features=train_data)

        if state["last_generation"] == 0:
            # FEDOT skips evolution when the budget is too small for even one
            # generation, and reports it only in the log; without this the UI
            # would show an empty evolution chart and no reason for it.
            events.emit(
                "log",
                level="warning",
                message=(
                    "Evolution was skipped: the time budget is too small for a generation "
                    "on this dataset. The result is FEDOT's initial assumption"
                    f"{' with tuned hyperparameters' if config.get('with_tuning', True) else ''}. "
                    "Raise the time budget to let the composer search."
                ),
            )

        events.emit("status", status="finalising")

        result: dict[str, Any] = {"generations": state["last_generation"]}

        from ..pipelines.convert import pipeline_to_graph

        best_graph = pipeline_to_graph(model.current_pipeline)
        result["best_pipeline"] = best_graph
        (run_dir / "best_pipeline.json").write_text(
            json.dumps(best_graph, ensure_ascii=False, allow_nan=False), encoding="utf-8"
        )

        # ``get_metrics`` scores whatever ``predict`` last ran on, so the holdout
        # has to go through the pipeline before the metrics are asked for.
        try:
            if validation_blocks is not None:
                model.predict(features=test_data, in_sample=True, validation_blocks=validation_blocks)
                metrics = model.get_metrics(in_sample=True, validation_blocks=validation_blocks)
            else:
                model.predict(features=test_data)
                metrics = model.get_metrics()
            result["metrics"] = {
                str(name): float(value)
                for name, value in dict(metrics).items()
                if isinstance(value, (int, float)) and value == value
            }
            result["metrics_source"] = "holdout"
        except Exception as exc:
            result["metrics"] = None
            events.emit("log", level="warning", message=f"metrics unavailable: {exc}")

        history = getattr(model, "history", None)
        if history is not None:
            try:
                (run_dir / HISTORY_FILE).write_text(history.save(), encoding="utf-8")
                result["generations"] = history.generations_count
            except Exception as exc:
                events.emit("log", level="warning", message=f"history not saved: {exc}")

        (run_dir / RESULT_FILE).write_text(
            json.dumps(result, ensure_ascii=False, allow_nan=False, default=str), encoding="utf-8"
        )
        events.emit("finished", **{k: v for k, v in result.items() if k != "best_pipeline"})
        return 0

    except KeyboardInterrupt:
        events.emit("cancelled", message="Run cancelled")
        return 130
    except Exception as exc:
        events.emit("error", message=str(exc), traceback=traceback.format_exc())
        return 1


def main() -> int:
    if len(sys.argv) < 2:
        print("usage: python -m fedotweb.runs.worker <run_directory>", file=sys.stderr)
        return 2
    return run(Path(sys.argv[1]))


if __name__ == "__main__":
    raise SystemExit(main())

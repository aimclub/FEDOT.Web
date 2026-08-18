"""Subprocess entry point that runs one EPDE equation search.

A search is CPU-bound and blocking, EPDE keeps global state (its token caches
live in module globals), and importing it drags in torch and scikit-learn. All
three say the same thing: give a run its own process. The API server then never
imports the framework, cancellation is a process kill, and two runs cannot
corrupt each other through the shared cache.

Progress is reported by appending JSON lines to ``events.jsonl`` in the run
directory. The per-generation events come from
:mod:`epdeweb.adapters.observer`, which installs the callback EPDE does not
provide, so the genealogy is drawn while the search is still going rather than
only at the end.

Run as::

    python -m epdeweb.runs.worker <run_directory>
"""

from __future__ import annotations

import json
import os
import random
import sys
import time
import traceback
from pathlib import Path
from typing import Any

CONFIG_FILE = "config.json"
EVENTS_FILE = "events.jsonl"
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
        # Opening per event keeps the file consistent for a reader tailing it
        # while we write, which matters because the reader is another process.
        with self._path.open("a", encoding="utf-8") as handle:
            handle.write(line + "\n")
            handle.flush()
            os.fsync(handle.fileno())


def _seed_everything(seed: int | None) -> None:
    if seed is None:
        return
    import numpy as np

    random.seed(seed)
    np.random.seed(seed)
    try:
        import torch

        torch.manual_seed(seed)
    except Exception:  # noqa: BLE001 - torch is optional for some EPDE builds
        pass


def _objective_names(config: dict[str, Any], variables: list[str], report: Any) -> list[str]:
    """Predicted names for the entries of the objective vector.

    EPDE lays it out as one quality value per equation followed by one
    second-axis value per equation. The prediction is checked against the first
    real vector by the observer, which falls back to positional names if it does
    not fit -- a confidently wrong axis label is worse than an honest index.
    """
    from ..adapters.objectives import default_objective_names
    from ..adapters.search import second_axis_name

    if not config.get("multiobjective", True):
        return [f"quality: {name}" for name in variables]
    return default_objective_names(variables, second_axis_name(config, report))


def _final_population(optimizer: Any) -> tuple[list[Any], list[Any]]:
    """The population and the leading front, whichever optimiser was used."""
    levels = getattr(optimizer, "pareto_levels", None)
    if levels is not None:
        population = list(getattr(levels, "population", None) or [])
        front_levels = getattr(levels, "levels", None) or []
        front = list(front_levels[0]) if front_levels else []
        return population, front

    holder = getattr(optimizer, "population", None)
    population = list(getattr(holder, "population", None) or holder or [])
    return population, []


def run(run_dir: Path) -> int:
    config: dict[str, Any] = json.loads((run_dir / CONFIG_FILE).read_text(encoding="utf-8"))
    events = EventWriter(run_dir / EVENTS_FILE)

    events.emit("status", status="starting", pid=os.getpid())

    observer = None
    try:
        import numpy as np

        from ..adapters import search as search_adapter
        from ..adapters.ablation import system_ablation
        from ..adapters.objectives import clean_objectives, pareto_front_indices
        from ..adapters.observer import EvolutionObserver, FinishRequested
        from ..adapters.structures import describe_system
        from ..datasets.fields import grids_for_epde, read_dataset
        from ..history.service import write_history

        _seed_everything(config.get("seed"))

        events.emit("status", status="loading_data", dataset=str(config.get("dataset_path")))
        dataset = read_dataset(Path(config["dataset_path"]))
        variables = [
            name for name in (config.get("variables") or list(dataset.variables)) if name in dataset.variables
        ]
        if not variables:
            raise ValueError("None of the requested variables are present in the dataset")

        data = [np.asarray(dataset.variables[name], dtype=float) for name in variables]
        grids = grids_for_epde(dataset)
        non_uniform = [
            name
            for name, axis in zip(dataset.axis_names, dataset.axes, strict=True)
            if len(axis) > 2 and float(np.max(np.diff(axis)) - np.min(np.diff(axis))) > 1e-6 * abs(
                float(np.mean(np.diff(axis))) or 1.0
            )
        ]
        if non_uniform:
            events.emit(
                "log",
                level="warning",
                message=(
                    "Axes " + ", ".join(non_uniform) + " are not evenly spaced. EPDE's derivative "
                    "preprocessors assume an even grid, so the derivatives -- and every coefficient "
                    "derived from them -- will be biased."
                ),
            )

        events.emit(
            "log",
            level="info",
            message=(
                f"field {dataset.shape} on axes {', '.join(dataset.axis_names)}; "
                f"describing {', '.join(variables)}"
            ),
        )

        report = search_adapter.BuildReport()
        events.emit("status", status="building_pool")
        epde_search = search_adapter.build_search(config, grids, report)
        tokens = search_adapter.build_tokens(
            config, max(len(grids) - 1, 0), variables, report
        )
        fit_arguments = search_adapter.fit_kwargs(
            epde_search, config, data, variables, tokens, report
        )
        for message in report.messages():
            events.emit("log", level="warning", message=message)

        multiobjective = bool(config.get("multiobjective", True))
        objective_names = _objective_names(config, variables, report)

        observer = EvolutionObserver(
            multiobjective=multiobjective,
            emit=events.emit,
            objective_names=objective_names,
            axis_names=list(dataset.axis_names),
            run_dir=run_dir,
        ).install()
        observer.set_epoch_limit(int(config["epochs"]) if config.get("epochs") else None)
        observer.set_time_budget(config.get("timeout"))

        events.emit("status", status="searching")
        finished_early: str | None = None
        try:
            epde_search.fit(**fit_arguments)
        except FinishRequested as stop:
            # Not a failure: the search was asked to end at a generation
            # boundary, and the optimiser still holds its population.
            finished_early = str(stop)
            events.emit("log", level="info", message=finished_early)

        events.emit("status", status="collecting")
        optimizer = getattr(epde_search, "optimizer", None)
        if optimizer is None:
            raise RuntimeError("EPDE finished without producing an optimiser")

        population, front = _final_population(optimizer)
        if not population:
            raise RuntimeError("The search produced no candidate systems")

        # The observer has seen real objective vectors by now, so its names are
        # the checked ones rather than the prediction made before the run.
        objective_names = observer.objective_names or objective_names

        registry = observer.registry
        described: list[dict[str, Any]] = []
        for system in front or population:
            uid = registry.uid_of(system)
            objectives = clean_objectives(_objectives_of(system))
            described.append(
                {
                    "uid": uid,
                    "objectives": objectives,
                    "system": describe_system(
                        system,
                        uid=uid,
                        objectives=objectives,
                        objective_names=objective_names,
                        axis_names=list(dataset.axis_names),
                    ),
                    "ablation": system_ablation(system),
                }
            )

        for entry in described:
            entry["system"]["objective_names"] = objective_names

        if not front:
            # The single-objective optimiser has no front of its own; the
            # non-dominated set of a one-element vector is just the best.
            keep = pareto_front_indices([entry["objectives"] for entry in described])
            front_entries = [described[index] for index in keep] or described[:1]
        else:
            front_entries = described

        front_entries.sort(key=lambda entry: (entry["objectives"] or [float("inf")])[0])
        best = front_entries[0] if front_entries else None

        history_payload = {
            "run": {
                "multiobjective": multiobjective,
                "variables": variables,
                "epochs_requested": config.get("epochs"),
                "finished_early": finished_early,
            },
            "objective_names": objective_names,
            "generations": [
                {
                    "generation": record.index,
                    "label": record.label,
                    "elapsed": record.elapsed,
                    "front_uids": record.front_uids,
                    "individuals": record.individuals,
                }
                for record in observer.generations
            ],
            "final_front": [entry["uid"] for entry in front_entries],
        }
        write_history(run_dir / HISTORY_FILE, history_payload)

        result = {
            "generations": len(observer.generations),
            "objective_names": objective_names,
            "finished_early": finished_early,
            "front": [
                {
                    "uid": entry["uid"],
                    "objectives": entry["objectives"],
                    "text": entry["system"]["text"],
                    "latex": entry["system"]["latex"],
                    "complexity": entry["system"]["complexity"],
                    "active_terms": entry["system"]["active_terms"],
                    "ablation": entry["ablation"],
                }
                for entry in front_entries
            ],
            "best_system": best["system"] if best else None,
            "warnings": report.messages(),
        }
        (run_dir / RESULT_FILE).write_text(
            json.dumps(result, ensure_ascii=False, allow_nan=False, default=str), encoding="utf-8"
        )
        events.emit(
            "finished",
            generations=result["generations"],
            front_size=len(front_entries),
            objective_names=objective_names,
            best=result["best_system"],
        )
        return 0

    except KeyboardInterrupt:
        events.emit("cancelled", message="Run cancelled")
        return 130
    except Exception as exc:  # noqa: BLE001 - reported to the user, not swallowed
        events.emit("error", message=str(exc), traceback=traceback.format_exc())
        return 1
    finally:
        if observer is not None:
            try:
                observer.uninstall()
            except Exception:  # noqa: BLE001
                pass


def _objectives_of(system: Any) -> list[float] | None:
    try:
        return [float(value) for value in system.obj_fun]
    except Exception:  # noqa: BLE001 - a candidate that never evaluated
        return None


def main() -> int:
    if len(sys.argv) < 2:
        print("usage: python -m epdeweb.runs.worker <run_directory>", file=sys.stderr)
        return 2
    return run(Path(sys.argv[1]))


if __name__ == "__main__":
    raise SystemExit(main())

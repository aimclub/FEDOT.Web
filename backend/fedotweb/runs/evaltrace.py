"""What the evaluator is doing right now, pipeline by pipeline, fold by fold.

A generation of AutoML is minutes of silence: the optimiser only reports when a
whole population is done, while the actual time goes into fitting individual
pipelines fold after fold. This module opens that box. The objective evaluator
is wrapped so that every evaluation writes what it is doing -- which pipeline,
which fold, which node is fitting at this moment -- and the server aggregates
those notes into a live picture.

The notes travel by file, not by socket, because with ``n_jobs > 1`` GOLEM
evaluates pipelines in separate processes (joblib): the wrapper object is
pickled into each of them, and each process appends to its own
``<run_dir>/evals/<pid>.jsonl``. One writer per file means no locking, and the
server merges the files on request.
"""

from __future__ import annotations

import json
import os
import time
from pathlib import Path
from typing import Any

#: Subdirectory of a run's directory where the trace files live.
TRACE_DIR_NAME = "evals"

#: An "active" evaluation with no end event and older than this is presumed
#: dead (its process was killed) and is not shown.
STALE_AFTER_SECONDS = 3600.0

#: How much of each trace file's tail the server reads. Enough for hundreds of
#: recent events; older history is only needed for totals, which are counted
#: from what is read.
TAIL_BYTES = 512 * 1024


class _TraceWriter:
    """Appends one JSON line per event to this process's own trace files.

    Node fits go to a separate file: they outnumber evaluation events by an
    order of magnitude, and keeping them apart lets the reader tail the small
    file far enough back to count every evaluation of a long run.
    """

    def __init__(self, directory: str) -> None:
        self._directory = directory
        self._files: dict[str, Any] = {}

    def emit(self, kind: str, **payload: Any) -> None:
        # Tracing must never break an evaluation, whatever the failure.
        try:
            suffix = "-nodes" if kind == "node" else ""
            handle = self._files.get(suffix)
            if handle is None:
                Path(self._directory).mkdir(parents=True, exist_ok=True)
                path = Path(self._directory) / f"{os.getpid()}{suffix}.jsonl"
                handle = open(path, "a", encoding="utf-8")
                self._files[suffix] = handle
            record = {"ts": time.time(), "kind": kind, **payload}
            handle.write(json.dumps(record, ensure_ascii=False, default=str) + "\n")
            handle.flush()
        except Exception:
            pass


#: Per-process singletons: the writer, and the context node-level events attach
#: to. Evaluations within one process are sequential, so a plain dict is safe.
_writers: dict[str, _TraceWriter] = {}
_current: dict[str, Any] = {}
_node_patch_installed = False


def _writer_for(directory: str) -> _TraceWriter:
    writer = _writers.get(directory)
    if writer is None:
        writer = _TraceWriter(directory)
        _writers[directory] = writer
    return writer


def _operations_of(graph: Any) -> list[str]:
    names = []
    for node in getattr(graph, "nodes", None) or []:
        name = getattr(node, "name", None)
        if name is None:
            name = getattr(node, "content", {}).get("name")
        names.append(str(name))
    return names


def _install_node_patch() -> None:
    """Report every node fit of this process, with the current evaluation's context.

    Installed lazily in whichever process evaluates, so it follows the wrapper
    into joblib workers without any start-up hook.
    """
    global _node_patch_installed
    if _node_patch_installed:
        return
    try:
        from fedot.core.pipelines.node import PipelineNode
    except Exception:
        return

    original = PipelineNode.fit

    def traced_fit(self: Any, *args: Any, **kwargs: Any) -> Any:
        writer = _current.get("writer")
        if writer is None:
            return original(self, *args, **kwargs)
        operation = str(
            getattr(getattr(self, "operation", None), "operation_type", None)
            or getattr(self, "name", "node")
        )
        info = dict(_current.get("info") or {})
        writer.emit("node", stage="fit_start", operation=operation, **info)
        started = time.monotonic()
        try:
            result = original(self, *args, **kwargs)
        except Exception as exc:
            writer.emit(
                "node",
                stage="fit_failed",
                operation=operation,
                seconds=round(time.monotonic() - started, 3),
                error=str(exc)[:200],
                **info,
            )
            raise
        writer.emit(
            "node",
            stage="fit_done",
            operation=operation,
            seconds=round(time.monotonic() - started, 3),
            **info,
        )
        return result

    PipelineNode.fit = traced_fit
    _node_patch_installed = True


def begin_main_process_trace(run_dir: Path) -> None:
    """Trace node fits that happen outside evolution, in the worker itself.

    The initial assumptions are fitted before the optimiser starts and the
    winning pipeline is refitted after it returns; both can take minutes and
    both used to be silent. Evaluations overwrite this context while they run.
    """
    _install_node_patch()
    _current["writer"] = _writer_for(str(run_dir / TRACE_DIR_NAME))
    _current["info"] = {"phase": "preparation"}


class _TracingDataProducer:
    """Wraps the fold producer so entering each fold leaves a note."""

    def __init__(self, inner: Any) -> None:
        self._inner = inner

    def __getattr__(self, name: str) -> Any:
        # ``evaluate_intermediate_metrics`` reaches for ``_data_producer.args``.
        return getattr(self._inner, name)

    def __call__(self, *args: Any, **kwargs: Any) -> Any:
        for fold_id, fold in enumerate(self._inner(*args, **kwargs)):
            info = _current.get("info")
            if info is not None:
                info["fold"] = fold_id
                writer = _current.get("writer")
                if writer is not None:
                    writer.emit("fold", **info)
            yield fold


class TracingObjectiveEvaluate:
    """An ``ObjectiveEvaluate`` that reports what it is doing while it works.

    Behaves exactly like the wrapped evaluator; the only addition is the trail
    of events. Picklable, and meant to be: joblib carries it into the worker
    processes, where the trace file is recreated lazily per process.
    """

    def __init__(self, inner: Any, trace_dir: str) -> None:
        self._inner = inner
        self._trace_dir = trace_dir

    @classmethod
    def wrap(cls, objective: Any, run_dir: Path) -> "TracingObjectiveEvaluate":
        if isinstance(objective, cls):
            return objective
        return cls(objective, str(Path(run_dir) / TRACE_DIR_NAME))

    def __getstate__(self) -> dict[str, Any]:
        return {"inner": self._inner, "trace_dir": self._trace_dir}

    def __setstate__(self, state: dict[str, Any]) -> None:
        self._inner = state["inner"]
        self._trace_dir = state["trace_dir"]

    def __getattr__(self, name: str) -> Any:
        # ``self.__dict__`` directly: during unpickling ``_inner`` does not
        # exist yet, and going through ``self._inner`` would recurse forever.
        inner = self.__dict__.get("_inner")
        if inner is None:
            raise AttributeError(name)
        try:
            return getattr(inner, name)
        except AttributeError:
            # The composer passes the evaluator's *bound method*, so requests
            # for the evaluator's own attributes go to the object behind it.
            target = getattr(inner, "__self__", None)
            if target is None:
                raise
            return getattr(target, name)

    def __call__(self, graph: Any) -> Any:
        return self.evaluate(graph)

    def _ensure_fold_tracing(self) -> None:
        # ``inner`` is either an ``ObjectiveEvaluate`` or its bound
        # ``evaluate`` method; the fold producer lives on the object.
        target = getattr(self._inner, "__self__", self._inner)
        producer = getattr(target, "_data_producer", None)
        if producer is not None and not isinstance(producer, _TracingDataProducer):
            target._data_producer = _TracingDataProducer(producer)

    def evaluate(self, graph: Any) -> Any:
        writer = _writer_for(self._trace_dir)
        self._ensure_fold_tracing()
        _install_node_patch()

        info = {
            "eval_id": f"{os.getpid()}-{time.monotonic_ns()}",
            "ops": _operations_of(graph),
        }
        _current["writer"] = writer
        _current["info"] = info
        writer.emit("evaluation", stage="start", **info)
        started = time.monotonic()
        inner = self._inner
        call = inner.evaluate if hasattr(inner, "evaluate") else inner
        try:
            fitness = call(graph)
        except Exception as exc:
            writer.emit(
                "evaluation",
                stage="failed",
                seconds=round(time.monotonic() - started, 3),
                error=str(exc)[:200],
                **info,
            )
            _current.pop("writer", None)
            _current.pop("info", None)
            raise
        values = list(getattr(fitness, "values", None) or [])
        valid = bool(getattr(fitness, "valid", False))
        writer.emit(
            "evaluation",
            stage="done" if valid else "invalid",
            seconds=round(time.monotonic() - started, 3),
            fitness=values[0] if valid and values else None,
            **info,
        )
        _current.pop("writer", None)
        _current.pop("info", None)
        return fitness


# --------------------------------------------------------------------- reading


def _tail_lines(path: Path) -> list[dict[str, Any]]:
    try:
        size = path.stat().st_size
        with open(path, "rb") as handle:
            if size > TAIL_BYTES:
                handle.seek(size - TAIL_BYTES)
                handle.readline()  # drop the line that was cut in half
            raw = handle.read().decode("utf-8", errors="replace")
    except OSError:
        return []
    events = []
    for line in raw.splitlines():
        try:
            events.append(json.loads(line))
        except json.JSONDecodeError:
            continue
    return events


def read_evaluation_state(run_dir: Path) -> dict[str, Any]:
    """Merge the trace files into one picture of the evaluator's work."""
    directory = Path(run_dir) / TRACE_DIR_NAME
    events: list[dict[str, Any]] = []
    if directory.is_dir():
        for path in directory.glob("*.jsonl"):
            events.extend(_tail_lines(path))
    events.sort(key=lambda event: event.get("ts") or 0)

    now = time.time()
    active: dict[str, dict[str, Any]] = {}
    recent: list[dict[str, Any]] = []
    done = failed = 0
    durations: list[float] = []
    preparing: dict[str, Any] | None = None

    for event in events:
        kind = event.get("kind")
        eval_id = event.get("eval_id")

        if kind == "evaluation":
            stage = event.get("stage")
            if stage == "start" and eval_id:
                active[eval_id] = {
                    "ops": event.get("ops") or [],
                    "fold": None,
                    "node": None,
                    "started": event.get("ts") or now,
                }
            elif eval_id:
                entry = active.pop(eval_id, None)
                seconds = event.get("seconds")
                if stage == "done":
                    done += 1
                    if isinstance(seconds, (int, float)):
                        durations.append(float(seconds))
                else:
                    failed += 1
                recent.append(
                    {
                        "ops": event.get("ops") or (entry or {}).get("ops") or [],
                        "seconds": seconds,
                        "fitness": event.get("fitness"),
                        "failed": stage != "done",
                        "error": event.get("error"),
                        "finished": event.get("ts"),
                    }
                )
        elif kind == "fold" and eval_id and eval_id in active:
            active[eval_id]["fold"] = event.get("fold")
        elif kind == "node":
            stage = event.get("stage")
            if eval_id and eval_id in active:
                active[eval_id]["node"] = (
                    event.get("operation") if stage == "fit_start" else None
                )
            elif event.get("phase") == "preparation":
                if stage == "fit_start":
                    preparing = {"node": event.get("operation"), "since": event.get("ts")}
                else:
                    preparing = None

    active_list = [
        {
            "ops": entry["ops"],
            "fold": entry["fold"],
            "node": entry["node"],
            "seconds": round(max(0.0, now - float(entry["started"])), 1),
        }
        for entry in active.values()
        if now - float(entry["started"]) < STALE_AFTER_SECONDS
    ]
    active_list.sort(key=lambda entry: -entry["seconds"])

    if preparing is not None and active_list:
        # Evolution has taken over; the preparation note is history.
        preparing = None

    return {
        "active": active_list,
        "preparing": (
            {
                "node": preparing["node"],
                "seconds": round(max(0.0, now - float(preparing["since"] or now)), 1),
            }
            if preparing
            else None
        ),
        "recent": list(reversed(recent[-20:])),
        "totals": {
            "done": done,
            "failed": failed,
            "active": len(active_list),
            "mean_seconds": round(sum(durations) / len(durations), 2) if durations else None,
        },
    }

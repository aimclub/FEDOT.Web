"""Loading saved optimisation histories and answering questions about them."""

from __future__ import annotations

import threading
from collections import OrderedDict
from pathlib import Path
from typing import Any

from golem.core.optimisers.opt_history_objects.opt_history import OptHistory

from .lineage import history_to_lineage
from .live import individual_pipeline_from_events, lineage_from_events

#: Deserialising a history costs seconds for a long run, and every click on the
#: lineage graph needs the same object, so a few are kept in memory.
_CACHE_SIZE = 4


class HistoryUnavailable(FileNotFoundError):
    """Raised when a run has no saved history."""


class _HistoryCache:
    """Small LRU of parsed histories, keyed by file path and modification time."""

    def __init__(self, size: int = _CACHE_SIZE) -> None:
        self._entries: OrderedDict[tuple[str, float], OptHistory] = OrderedDict()
        self._size = size
        self._lock = threading.Lock()

    def get(self, path: Path) -> OptHistory:
        if not path.exists():
            raise HistoryUnavailable(f"No history was saved at {path}")

        key = (str(path), path.stat().st_mtime)
        with self._lock:
            cached = self._entries.get(key)
            if cached is not None:
                self._entries.move_to_end(key)
                return cached

        # Parsing outside the lock: it is slow, and a duplicate parse is cheaper
        # than blocking every other request while one runs.
        history = OptHistory.load(path.read_text(encoding="utf-8"))

        with self._lock:
            self._entries[key] = history
            self._entries.move_to_end(key)
            while len(self._entries) > self._size:
                self._entries.popitem(last=False)
        return history


_cache = _HistoryCache()


def load_history(path: Path) -> OptHistory:
    return _cache.get(path)


def lineage_graph(path: Path, *, only_winning_path: bool = True) -> dict[str, Any]:
    """The genealogy of a finished run, ready for the browser."""
    history = load_history(path)
    graph = history_to_lineage(history, only_winning_path=only_winning_path)
    graph["only_winning_path"] = only_winning_path
    graph["metric_names"] = _metric_names(history)
    graph["source"] = "history"
    graph["is_live"] = False
    return graph


def live_lineage_graph(
    events: list[dict[str, Any]], *, only_winning_path: bool = True
) -> dict[str, Any] | None:
    """The genealogy of a run still in progress, built from its progress events."""
    graph = lineage_from_events(events, only_winning_path=only_winning_path)
    if graph is None:
        return None
    graph["only_winning_path"] = only_winning_path
    graph["metric_names"] = []
    graph["source"] = "live"
    graph["is_live"] = True
    return graph


def _metric_names(history: OptHistory) -> list[str]:
    names = getattr(history, "metric_names", None)
    if names:
        return [str(name) for name in names]
    objective = getattr(history, "objective", None)
    names = getattr(objective, "metric_names", None)
    return [str(name) for name in names] if names else []


def individual_pipeline(path: Path, individual_uid: str) -> dict[str, Any] | None:
    """The pipeline of one individual, in the editor's graph format.

    This is what makes the lineage graph explorable: clicking a node in the
    genealogy shows the actual pipeline that node stands for.
    """
    from fedot.core.pipelines.adapters import PipelineAdapter

    from ..pipelines.convert import pipeline_to_graph

    history = load_history(path)
    for generation_index, population in enumerate(history.generations or []):
        for individual in population:
            if str(individual.uid) != individual_uid:
                continue
            pipeline = PipelineAdapter().restore(individual.graph)
            described = pipeline_to_graph(pipeline, uid=individual_uid)
            fitness = getattr(individual.fitness, "value", None)
            described["fitness"] = float(fitness) if isinstance(fitness, (int, float)) else None
            described["generation"] = generation_index
            return described
    return None


def live_individual_pipeline(
    events: list[dict[str, Any]], individual_uid: str
) -> dict[str, Any] | None:
    """The pipeline of one individual in a run that is still going."""
    return individual_pipeline_from_events(events, individual_uid)

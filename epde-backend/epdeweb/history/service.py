"""The saved history of a finished run.

EPDE keeps nothing after a search: ``MOEADDOptimizer`` holds its final
``ParetoLevels`` and the single-objective one its final ``Population``, and both
are gone with the process. There is no ``OptHistory`` to load, so the worker
writes one -- the same per-generation payloads it streamed, collected into a
file -- and this module reads it back.

The format is deliberately the same shape as the live events. It means the
lineage builder has one input, the file can be inspected by hand, and a run can
be re-read on a machine where EPDE is not installed at all.
"""

from __future__ import annotations

import json
import threading
from collections import OrderedDict
from pathlib import Path
from typing import Any

from .live import normalise_generations
from .model import DEFAULT_MAX_INDIVIDUALS, build_lineage

HISTORY_FILE = "history.json"
HISTORY_VERSION = 1

#: Parsing a long run's history costs real time, and every click on the
#: genealogy needs the same object, so a few are kept in memory.
_CACHE_SIZE = 4


class HistoryUnavailable(FileNotFoundError):
    """Raised when a run has no saved history."""


class _HistoryCache:
    """A small LRU of parsed histories, keyed by path and modification time."""

    def __init__(self, size: int = _CACHE_SIZE) -> None:
        self._entries: OrderedDict[tuple[str, float], dict[str, Any]] = OrderedDict()
        self._size = size
        self._lock = threading.Lock()

    def get(self, path: Path) -> dict[str, Any]:
        if not path.exists():
            raise HistoryUnavailable(f"No history was saved at {path}")

        key = (str(path), path.stat().st_mtime)
        with self._lock:
            cached = self._entries.get(key)
            if cached is not None:
                self._entries.move_to_end(key)
                return cached

        # Parsed outside the lock: it is slow, and a duplicate parse is cheaper
        # than blocking every other request while one runs.
        payload = json.loads(path.read_text(encoding="utf-8"))

        with self._lock:
            self._entries[key] = payload
            self._entries.move_to_end(key)
            while len(self._entries) > self._size:
                self._entries.popitem(last=False)
        return payload


_cache = _HistoryCache()


def write_history(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = {"version": HISTORY_VERSION, **payload}
    path.write_text(
        json.dumps(payload, ensure_ascii=False, allow_nan=False, default=str), encoding="utf-8"
    )


def load_history(path: Path) -> dict[str, Any]:
    return _cache.get(path)


def saved_lineage_graph(
    path: Path,
    *,
    only_winning_path: bool = True,
    max_individuals: int = DEFAULT_MAX_INDIVIDUALS,
) -> dict[str, Any]:
    """The genealogy of a finished run, ready for the browser."""
    history = load_history(path)
    generations = normalise_generations(history.get("generations") or [])
    final = {str(uid) for uid in history.get("final_front") or []}
    if not final and generations:
        final = set(generations[-1].front_uids)

    graph = build_lineage(
        generations,
        final_uids=final,
        only_winning_path=only_winning_path,
        max_individuals=max_individuals,
    )
    graph["only_winning_path"] = only_winning_path
    graph["objective_names"] = [str(name) for name in history.get("objective_names") or []]
    graph["source"] = "history"
    graph["is_live"] = False
    return graph


def saved_system(path: Path, individual_uid: str) -> dict[str, Any] | None:
    """The system one candidate stands for, from the saved history."""
    history = load_history(path)
    found: dict[str, Any] | None = None
    generation: int | None = None
    for entry in history.get("generations") or []:
        for individual in entry.get("individuals") or []:
            if str(individual.get("uid")) != individual_uid:
                continue
            if individual.get("system"):
                found = individual["system"]
                generation = entry.get("generation", entry.get("index"))

    if found is None:
        return None
    described = dict(found)
    described.setdefault("uid", individual_uid)
    if generation is not None:
        described["generation"] = generation
    return described


def history_generations(path: Path) -> list[dict[str, Any]]:
    """Raw generation payloads, for callers that want the numbers unbuilt."""
    return list(load_history(path).get("generations") or [])

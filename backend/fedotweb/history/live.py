"""The genealogy of a run that is still going.

The saved ``OptHistory`` only exists once FEDOT finishes, so a run in progress
has no history file to read. What it does have is the stream of ``population``
events the worker emits from GOLEM's iteration callback -- one per generation,
carrying the same ancestry facts.

Those events are replayed here into the normalised form
:mod:`fedotweb.history.model` builds from, so the genealogy shown during a run
and the one shown afterwards are the same drawing.
"""

from __future__ import annotations

from typing import Any

from .model import (
    DEFAULT_MAX_INDIVIDUALS,
    LineageGeneration,
    LineageIndividual,
    LineageOperator,
    build_lineage,
)


def _coerce_fitness(value: Any) -> float | None:
    if value is None:
        return None
    try:
        number = float(value)
    except (TypeError, ValueError):
        return None
    return number if number == number and abs(number) != float("inf") else None


def _individual_from_payload(payload: dict[str, Any]) -> LineageIndividual:
    operators = [
        LineageOperator(
            uid=str(operator.get("uid", "")),
            type_=str(operator.get("type", "operator")),
            label=str(operator.get("label", "")),
            parent_uids=[str(uid) for uid in (operator.get("parents") or [])],
        )
        for operator in (payload.get("operators") or [])
    ]
    return LineageIndividual(
        uid=str(payload.get("uid", "")),
        fitness=_coerce_fitness(payload.get("fitness")),
        operations=[str(name) for name in (payload.get("operations") or [])],
        # Carried through for display only; the builder decides what is new from
        # where an individual first appears, not from this counter.
        native_generation=payload.get("native_generation"),
        operators=operators,
    )


def individual_pipeline_from_events(
    events: list[dict[str, Any]], individual_uid: str
) -> dict[str, Any] | None:
    """The pipeline of one individual, from the live event stream.

    The worker sends bare structure -- operations, wiring and chosen parameters --
    so what comes back here is enriched with the catalogue metadata the editor
    canvas expects, rather than round-tripped through FEDOT.
    """
    from ..catalog import get_catalog

    latest: dict[str, Any] | None = None
    generation: int | None = None
    for event in events:
        if event.get("kind") != "population":
            continue
        payload = event.get("payload") or {}
        for entry in payload.get("individuals") or []:
            if str(entry.get("uid")) == individual_uid and entry.get("graph"):
                latest = entry
                generation = payload.get("generation")

    if latest is None:
        return None

    catalog = get_catalog()
    raw = latest["graph"]
    nodes = []
    parents: dict[str, list[str]] = {node["id"]: [] for node in raw["nodes"]}
    children: dict[str, list[str]] = {node["id"]: [] for node in raw["nodes"]}
    for edge in raw.get("edges") or []:
        parents.setdefault(edge["target"], []).append(edge["source"])
        children.setdefault(edge["source"], []).append(edge["target"])

    for node in raw["nodes"]:
        described = catalog.get(node["operation"]) or {}
        nodes.append(
            {
                "id": node["id"],
                "operation": node["operation"],
                "label": node["operation"],
                "kind": described.get("kind", "model"),
                "group": described.get("group", "model"),
                "description": described.get("description"),
                "tags": described.get("tags", []),
                "params": node.get("params") or {},
                "defaults": described.get("defaults", {}),
                "parents": parents.get(node["id"], []),
                "children": children.get(node["id"], []),
                "is_primary": not parents.get(node["id"]),
                "is_root": not children.get(node["id"]),
            }
        )

    edges = [
        {"id": f"{edge['source']}->{edge['target']}", "source": edge["source"], "target": edge["target"]}
        for edge in (raw.get("edges") or [])
    ]

    return {
        "uid": individual_uid,
        "nodes": nodes,
        "edges": edges,
        "length": len(nodes),
        "depth": _depth_of(parents),
        "fitness": _coerce_fitness(latest.get("fitness")),
        "generation": generation,
    }


def _depth_of(parents: dict[str, list[str]]) -> int:
    """Longest chain from a primary node to a sink."""
    memo: dict[str, int] = {}

    def depth(node_id: str, seen: frozenset[str]) -> int:
        if node_id in memo:
            return memo[node_id]
        if node_id in seen:  # defensive: a cycle should not hang the request
            return 0
        chain = [depth(parent, seen | {node_id}) for parent in parents.get(node_id, [])]
        result = 1 + max(chain, default=0)
        memo[node_id] = result
        return result

    return max((depth(node_id, frozenset()) for node_id in parents), default=0)


def normalise_events(events: list[dict[str, Any]]) -> tuple[list[LineageGeneration], set[str]]:
    """Replay stored ``population`` events into generations and the current best.

    The worker numbers generations from one, matching GOLEM's own counter; the
    graph indexes them from zero, so the offset is removed here. A generation
    reported more than once -- which a reconnect or a replay can cause -- keeps
    only its latest payload.
    """
    raw: dict[int, list[dict[str, Any]]] = {}
    best_uids: set[str] = set()

    for event in events:
        if event.get("kind") != "population":
            continue
        payload = event.get("payload") or {}
        try:
            generation = int(payload.get("generation", 0))
        except (TypeError, ValueError):
            continue

        raw[generation] = list(payload.get("individuals") or [])
        reported_best = payload.get("best_uids") or []
        if reported_best:
            best_uids = {str(uid) for uid in reported_best}

    if not raw:
        return [], set()

    ordered = sorted(raw)
    offset = ordered[0]
    generations = [
        LineageGeneration(
            index=generation - offset,
            # A live run has no labelled seed or result populations; every event
            # is a real generation.
            raw_label="",
            individuals=[_individual_from_payload(entry) for entry in raw[generation]],
        )
        for generation in ordered
    ]
    return generations, best_uids


def lineage_from_events(
    events: list[dict[str, Any]],
    *,
    only_winning_path: bool = True,
    max_individuals: int = DEFAULT_MAX_INDIVIDUALS,
) -> dict[str, Any] | None:
    """Genealogy of a run in progress, or ``None`` when nothing was reported yet."""
    generations, best_uids = normalise_events(events)
    if not generations:
        return None

    if not best_uids:
        # Before the archive reports anything, treat the best-scoring individual
        # seen so far as the tip of the lineage.
        scored = [
            individual
            for generation in generations
            for individual in generation.individuals
            if individual.fitness is not None
        ]
        if scored:
            best_uids = {min(scored, key=lambda individual: individual.fitness).uid}

    graph = build_lineage(
        generations,
        final_uids=best_uids,
        only_winning_path=only_winning_path,
        max_individuals=max_individuals,
    )
    # Nothing is final while the run is going; the marker means "best so far".
    for node in graph["nodes"]:
        if node["kind"] == "individual" and node.get("is_final_choice"):
            node["is_current_best"] = True
            node["is_final_choice"] = False
    return graph

"""The genealogy of a run that is still going.

A finished run has a history file; a running one has only the ``population``
events the worker has emitted so far. Both carry the same per-generation
payload, so both are replayed through the same normaliser here and end up in
the same builder -- which is what keeps the graph watched during a run and the
one read afterwards from being two drawings that drift apart.
"""

from __future__ import annotations

from typing import Any

from ..adapters.objectives import clean_objectives
from .model import (
    DEFAULT_MAX_INDIVIDUALS,
    SEED_LABEL,
    LineageGeneration,
    LineageIndividual,
    LineageOperator,
    build_lineage,
)


def individual_from_payload(payload: dict[str, Any]) -> LineageIndividual:
    operators = [
        LineageOperator(
            uid=str(entry.get("uid", "")),
            type_=str(entry.get("type", "operator")),
            label=str(entry.get("label", "")),
            parent_uids=[str(uid) for uid in entry.get("parents") or []],
        )
        for entry in payload.get("operators") or []
    ]
    rank = payload.get("pareto_rank")
    return LineageIndividual(
        uid=str(payload.get("uid", "")),
        objectives=clean_objectives(payload.get("objectives")),
        pareto_rank=int(rank) if isinstance(rank, (int, float)) else None,
        terms=[str(term) for term in payload.get("terms") or []],
        born_generation=payload.get("born_generation"),
        operators=operators,
    )


def normalise_generations(payloads: list[dict[str, Any]]) -> list[LineageGeneration]:
    """Turn per-generation payloads into the builder's input.

    A generation reported more than once -- which a reconnect or a replay can
    cause -- keeps only its latest payload, and the indices are re-based so the
    first reported generation is zero however the run numbered them.
    """
    latest: dict[int, dict[str, Any]] = {}
    for payload in payloads:
        try:
            index = int(payload.get("generation", 0))
        except (TypeError, ValueError):
            continue
        latest[index] = payload

    if not latest:
        return []

    ordered = sorted(latest)
    offset = ordered[0]
    generations: list[LineageGeneration] = []
    for index in ordered:
        payload = latest[index]
        generations.append(
            LineageGeneration(
                index=index - offset,
                label=str(payload.get("label") or ""),
                individuals=[
                    individual_from_payload(entry) for entry in payload.get("individuals") or []
                ],
                front_uids=[str(uid) for uid in payload.get("front_uids") or []],
            )
        )
    return generations


def _population_payloads(events: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return [
        event.get("payload") or {}
        for event in events
        if event.get("kind") == "population"
    ]


def lineage_from_events(
    events: list[dict[str, Any]],
    *,
    only_winning_path: bool = True,
    max_individuals: int = DEFAULT_MAX_INDIVIDUALS,
) -> dict[str, Any] | None:
    """Genealogy of a run in progress, or ``None`` if nothing was reported yet."""
    generations = normalise_generations(_population_payloads(events))
    if not generations:
        return None

    final_uids = _leading_uids(generations)
    graph = build_lineage(
        generations,
        final_uids=final_uids,
        only_winning_path=only_winning_path,
        max_individuals=max_individuals,
    )
    # Nothing is final while the run is going; the marker means "leading now".
    for node in graph["nodes"]:
        if node["kind"] == "individual" and node.get("is_final_choice"):
            node["is_current_best"] = True
            node["is_final_choice"] = False
    return graph


def _leading_uids(generations: list[LineageGeneration]) -> set[str]:
    """The front of the most recent generation that reported one."""
    for generation in reversed(generations):
        if generation.front_uids:
            return set(generation.front_uids)
    # No front was reported; fall back to the best first objective seen.
    scored = [
        individual
        for generation in generations
        for individual in generation.individuals
        if individual.objectives
    ]
    if not scored:
        return set()
    best = min(scored, key=lambda individual: individual.objectives[0])  # type: ignore[index]
    return {best.uid}


def system_from_events(events: list[dict[str, Any]], individual_uid: str) -> dict[str, Any] | None:
    """The system one candidate stands for, from the live event stream.

    The latest report wins: a candidate present in several generations has the
    same structure in each, but the later report carries the coefficients as
    they stood after further fitting.
    """
    found: dict[str, Any] | None = None
    generation: int | None = None
    for payload in _population_payloads(events):
        for entry in payload.get("individuals") or []:
            if str(entry.get("uid")) != individual_uid:
                continue
            if entry.get("system"):
                found = entry["system"]
                generation = payload.get("generation")

    if found is None:
        return None
    described = dict(found)
    described.setdefault("uid", individual_uid)
    if generation is not None:
        described["generation"] = generation
    return described


def seed_generation_indices(generations: list[LineageGeneration]) -> list[int]:
    return [generation.index for generation in generations if generation.label == SEED_LABEL]

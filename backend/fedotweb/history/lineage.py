"""The evolution history as a graph, from a finished run's ``OptHistory``.

A fitness curve says *that* the population improved; it does not say *how*. This
module turns a GOLEM ``OptHistory`` into a genealogy: which pipeline was crossed
with which, what mutated into what, and which of those lines actually led to the
pipeline that won.

The graph is bipartite by layer:

* even layers hold **individuals** -- one pipeline evaluated in one generation
* odd layers hold **operators** -- the mutation or crossover that produced the
  individuals in the next generation

An individual that survives selection unchanged is linked straight to its copy in
the following generation, so a surviving line reads as an unbroken vertical run.

The same graph is assembled from live progress events by :mod:`fedotweb.history.live`;
both go through :func:`fedotweb.history.model.build_lineage`.
"""

from __future__ import annotations

from typing import Any

from golem.core.optimisers.opt_history_objects.individual import Individual
from golem.core.optimisers.opt_history_objects.opt_history import OptHistory

from .model import (
    DEFAULT_MAX_INDIVIDUALS,
    LineageGeneration,
    LineageIndividual,
    LineageOperator,
    build_lineage,
)


def fitness_value(individual: Individual) -> float | None:
    """Fitness as a plain comparable number, or ``None`` when it never evaluated."""
    fitness = getattr(individual, "fitness", None)
    value = getattr(fitness, "value", None)
    if value is None:
        return None
    try:
        number = float(value)
    except (TypeError, ValueError):
        return None
    # NaN and infinities mean the evaluation failed.
    return number if number == number and abs(number) != float("inf") else None


def operations_of(individual: Individual) -> list[str]:
    """Operation names in the individual's graph, for a compact node label."""
    graph = getattr(individual, "graph", None)
    nodes = getattr(graph, "nodes", None) or []
    names = []
    for node in nodes:
        name = getattr(node, "name", None) or getattr(node, "content", {}).get("name")
        names.append(str(name))
    return names


def operator_label(operator: Any) -> str:
    names = [str(name) for name in (getattr(operator, "operators", None) or [])]
    return ", ".join(names) if names else str(getattr(operator, "type_", "operator"))


def _operators_of(individual: Individual) -> list[LineageOperator]:
    try:
        operators = list(individual.operators_from_prev_generation)
    except ValueError:
        # GOLEM raises when inheritance data is inconsistent; a broken lineage
        # should not cost the whole graph.
        return []

    return [
        LineageOperator(
            uid=str(operator.uid),
            type_=str(operator.type_),
            label=operator_label(operator),
            parent_uids=[str(parent.uid) for parent in (operator.parent_individuals or ())],
        )
        for operator in operators
    ]


def normalise_history(history: OptHistory) -> list[LineageGeneration]:
    """Turn a saved ``OptHistory`` into the builder's input."""
    generations: list[LineageGeneration] = []
    for index, population in enumerate(history.generations or []):
        individuals = [
            LineageIndividual(
                uid=str(individual.uid),
                fitness=fitness_value(individual),
                operations=operations_of(individual),
                native_generation=individual.native_generation,
                operators=_operators_of(individual) if individual.native_generation == index else [],
            )
            for individual in population
        ]
        generations.append(
            LineageGeneration(
                index=index,
                raw_label=str(getattr(population, "label", None) or ""),
                individuals=individuals,
            )
        )
    return generations


def _final_uids(history: OptHistory) -> set[str]:
    finals = list(history.final_choices or [])
    if not finals:
        archive = history.archive_history or []
        if archive:
            evaluated = [ind for ind in archive[-1] if fitness_value(ind) is not None]
            if evaluated:
                finals = [min(evaluated, key=fitness_value)]
    return {str(individual.uid) for individual in finals}


def history_to_lineage(
    history: OptHistory,
    *,
    only_winning_path: bool = True,
    max_individuals: int = DEFAULT_MAX_INDIVIDUALS,
) -> dict[str, Any]:
    """Build the genealogy graph for a completed optimisation.

    Args:
        history: the history saved by the run worker.
        only_winning_path: keep just the individuals that led to the final
            choice. A full population graph is available but grows as
            ``pop_size x generations``.
        max_individuals: safety ceiling on the payload size.
    """
    return build_lineage(
        normalise_history(history),
        final_uids=_final_uids(history),
        only_winning_path=only_winning_path,
        max_individuals=max_individuals,
    )

"""The genealogy graph, and the structures it is built from.

The shape follows FEDOT.Web's: a layered bipartite drawing where generation *g*
occupies layer ``2g`` and the operators that produced it sit on layer ``2g-1``,
so the graph reads top to bottom with each generation on its own labelled row.
A candidate carried into the next generation unchanged is joined to its copy
with a survival edge, so an unbroken vertical run means a system that survived.

One thing genuinely differs, and it is not cosmetic. FEDOT compares individuals
by a single fitness, so "the best of this generation" is one node and "the
winner" is one pipeline. EPDE minimises a *vector* -- discrepancy against
complexity, or against coefficient stability -- so the leaders of a generation
are its whole non-dominated front, and the ancestry worth drawing is the
ancestry of that front. Every place FEDOT.Web takes a minimum, this takes a
Pareto front instead.

The builder is fed from two sources -- the events streamed while a run is going
and the history file written when it ends -- and both are normalised into the
structures here first, so the graph watched live and the one read afterwards are
the same drawing rather than two implementations that drift.
"""

from __future__ import annotations

from dataclasses import dataclass, field, replace
from typing import Any

#: Copies are bookkeeping rather than a transformation; drawing them would put
#: an operator node on every survival edge EPDE happens to implement by copying.
HIDDEN_OPERATOR_TYPES = frozenset({"copy"})

#: Ceiling on how many candidates to describe, so a long run cannot produce a
#: payload the browser chokes on.
DEFAULT_MAX_INDIVIDUALS = 1500

#: Generations that are not rounds of evolution.
SEED_LABEL = "initial population"


@dataclass(frozen=True)
class LineageOperator:
    """A mutation or crossover that produced a candidate."""

    uid: str
    type_: str
    label: str
    parent_uids: list[str]


@dataclass(frozen=True)
class LineageIndividual:
    """One candidate system as recorded in one generation."""

    uid: str
    #: The objective vector; ``None`` when the candidate never evaluated.
    objectives: list[float] | None
    #: Non-domination level within its generation; 0 is the front.
    pareto_rank: int | None
    #: Short labels for the card -- the active terms of the system.
    terms: list[str]
    born_generation: int | None = None
    #: Only meaningful for the generation that first showed this candidate.
    operators: list[LineageOperator] = field(default_factory=list)


@dataclass(frozen=True)
class LineageGeneration:
    """One reported population."""

    index: int
    label: str
    individuals: list[LineageIndividual]
    #: The non-dominated candidates, as the optimiser itself saw them.
    front_uids: list[str] = field(default_factory=list)


def generation_metadata(generations: list[LineageGeneration]) -> list[dict[str, Any]]:
    """Describe each generation, separating evolution from the seed population."""
    metadata: list[dict[str, Any]] = []
    evolutionary_index = 0
    for generation in generations:
        is_evolutionary = generation.label != SEED_LABEL
        if is_evolutionary:
            evolutionary_index += 1
            label = f"gen {evolutionary_index}"
        else:
            label = SEED_LABEL
        metadata.append(
            {
                "index": generation.index,
                "label": label,
                "raw_label": generation.label,
                "size": len(generation.individuals),
                "front_size": len(generation.front_uids),
                "is_evolutionary": is_evolutionary,
            }
        )
    return metadata


class LineageBuilder:
    """Assembles the genealogy from normalised generations."""

    def __init__(
        self,
        generations: list[LineageGeneration],
        *,
        final_uids: set[str],
        max_individuals: int = DEFAULT_MAX_INDIVIDUALS,
    ) -> None:
        self._generations = generations
        self._final_uids = final_uids
        self._max_individuals = max_individuals
        self._nodes: list[dict[str, Any]] = []
        self._edges: list[dict[str, str]] = []
        #: (generation, uid) -> node id, so a candidate present in several
        #: generations is a distinct node in each of them.
        self._individual_nodes: dict[tuple[int, str], str] = {}
        self._edge_ids: set[str] = set()
        self._truncated = False

    # ------------------------------------------------------------------ helpers

    def _add_edge(self, source: str, target: str, kind: str) -> None:
        if source == target:
            return
        edge_id = f"{source}->{target}"
        if edge_id in self._edge_ids:
            return
        self._edge_ids.add(edge_id)
        self._edges.append({"id": edge_id, "source": source, "target": target, "kind": kind})

    def _latest_node_before(self, uid: str, generation: int) -> str | None:
        """The most recent node for ``uid`` in a generation earlier than this one.

        A candidate can leave a population and come back -- MOEA/D keeps an
        archive and reintroduces from it -- so a parent is not always in the
        generation immediately before its child. Looking only one step back
        leaves those nodes with no incoming edge, which reads as a system that
        appeared from nowhere.
        """
        for candidate in range(generation - 1, -1, -1):
            node_id = self._individual_nodes.get((candidate, uid))
            if node_id is not None:
                return node_id
        return None

    # ----------------------------------------------------------------- ancestry

    def _winning_uids(self) -> set[str]:
        """Every candidate on a line of descent leading to the final front.

        Without this the graph shows every system ever evaluated, which for a
        realistic run is thousands of nodes and no story. The difference from
        FEDOT.Web is that the tip is a set: the whole Pareto front is "the
        answer", and a user comparing a simple equation against an accurate one
        wants both lines drawn.
        """
        parents_of: dict[str, set[str]] = {}
        for generation in self._generations:
            for individual in generation.individuals:
                known = parents_of.setdefault(individual.uid, set())
                for operator in individual.operators:
                    known.update(operator.parent_uids)

        winning: set[str] = set()
        frontier = list(self._final_uids)
        # Ancestry is a DAG; a visited set keeps a diamond from being walked twice.
        while frontier:
            uid = frontier.pop()
            if uid in winning:
                continue
            winning.add(uid)
            frontier.extend(parents_of.get(uid, ()))
        return winning

    # -------------------------------------------------------------------- build

    def build(self, *, only_winning_path: bool) -> dict[str, Any]:
        winning = self._winning_uids()
        described = 0

        for generation in self._generations:
            front = set(generation.front_uids)
            for position, individual in enumerate(generation.individuals):
                if only_winning_path and individual.uid not in winning:
                    continue
                if described >= self._max_individuals:
                    self._truncated = True
                    break

                node_id = f"ind:{generation.index}:{individual.uid}"
                self._nodes.append(
                    {
                        "id": node_id,
                        "kind": "individual",
                        "uid": individual.uid,
                        "generation": generation.index,
                        "index": position,
                        "layer": generation.index * 2,
                        "objectives": individual.objectives,
                        "pareto_rank": individual.pareto_rank,
                        "terms": individual.terms,
                        "length": len(individual.terms),
                        "born_generation": individual.born_generation,
                        # The multi-objective replacement for "best of this
                        # generation": membership of its non-dominated front.
                        "is_on_front": individual.uid in front,
                        "is_final_choice": individual.uid in self._final_uids,
                        "is_current_best": False,
                        "on_winning_path": individual.uid in winning,
                    }
                )
                self._individual_nodes[(generation.index, individual.uid)] = node_id
                described += 1

                # A candidate carried over unchanged keeps its uid, so linking
                # the two copies shows survival as a continuous line.
                previous = self._latest_node_before(individual.uid, generation.index)
                if previous is not None:
                    self._add_edge(previous, node_id, "survival")

        self._link_operators(winning, only_winning_path)

        metadata = generation_metadata(self._generations)
        return {
            "nodes": self._nodes,
            "edges": self._edges,
            "generations": len(self._generations),
            "evolution_generations": sum(1 for entry in metadata if entry["is_evolutionary"]),
            "generation_meta": metadata,
            "truncated": self._truncated,
        }

    def _link_operators(self, winning: set[str], only_winning_path: bool) -> None:
        """Insert the mutation and crossover nodes between generations."""
        seen_operators: dict[tuple[int, str], str] = {}

        for generation in self._generations:
            if generation.index == 0:
                continue

            for individual in generation.individuals:
                if only_winning_path and individual.uid not in winning:
                    continue
                child_node_id = self._individual_nodes.get((generation.index, individual.uid))
                if child_node_id is None:
                    continue
                # Only the generation that first shows a candidate draws the
                # operators that made it; later copies are survivors and are
                # linked as such.
                if self._latest_node_before(individual.uid, generation.index) is not None:
                    continue

                previous_node_id: str | None = None
                for operator in individual.operators:
                    if operator.type_ in HIDDEN_OPERATOR_TYPES:
                        continue
                    if not operator.parent_uids and previous_node_id is None:
                        # The first link of a chain with no parents recorded is
                        # an individual of the seed population, not an operator.
                        continue

                    key = (generation.index, operator.uid)
                    operator_node_id = seen_operators.get(key)
                    if operator_node_id is None:
                        operator_node_id = f"op:{generation.index}:{operator.uid}"
                        seen_operators[key] = operator_node_id
                        self._nodes.append(
                            {
                                "id": operator_node_id,
                                "kind": "operator",
                                "uid": operator.uid,
                                "generation": generation.index,
                                "layer": generation.index * 2 - 1,
                                "operator_type": operator.type_,
                                "label": operator.label,
                                "on_winning_path": individual.uid in winning,
                            }
                        )

                    if previous_node_id is not None:
                        # Operators applied in sequence: crossover, then mutation
                        # of the offspring before it was ever reported.
                        self._add_edge(previous_node_id, operator_node_id, "chain")
                    else:
                        for parent_uid in operator.parent_uids:
                            parent_node_id = self._latest_node_before(parent_uid, generation.index)
                            if parent_node_id is not None:
                                self._add_edge(parent_node_id, operator_node_id, operator.type_)

                    previous_node_id = operator_node_id

                if previous_node_id is not None:
                    self._add_edge(previous_node_id, child_node_id, "produces")


def _without_plateau_tail(
    generations: list[LineageGeneration],
) -> tuple[list[LineageGeneration], int]:
    """Drop the generations after the front last changed.

    In the winning-path view those only repeat the same front as a chain of
    survival edges, which reads as content while saying nothing. FEDOT.Web cuts
    at the last improvement in fitness; the multi-objective equivalent is the
    last generation whose non-dominated set is not exactly the previous one.
    The kept generations are re-indexed to stay contiguous, because the layout
    draws a placeholder row for every missing generation number.
    """
    last_change: int | None = None
    previous: set[str] | None = None
    for generation in generations:
        current = set(generation.front_uids)
        if generation.label == SEED_LABEL:
            # The seed is the baseline the first evolutionary generation is
            # compared against. Skipping it entirely would make that generation
            # look like a change even when evolution did nothing at all, which
            # is exactly the case this trimming exists to expose.
            previous = current
            continue
        if previous is None or current != previous:
            last_change = generation.index
        previous = current

    if last_change is None:
        # The front never moved. Keep the baseline row -- the seed population,
        # or the first generation when a run reported none -- so the graph still
        # shows what the search started from rather than coming back empty.
        kept = [
            generation for generation in generations if generation.label == SEED_LABEL
        ] or generations[:1]
    else:
        kept = [
            generation
            for generation in generations
            if generation.label == SEED_LABEL or generation.index <= last_change
        ]
    hidden = len(generations) - len(kept)
    if hidden == 0:
        return generations, 0
    return [replace(generation, index=index) for index, generation in enumerate(kept)], hidden


def build_lineage(
    generations: list[LineageGeneration],
    *,
    final_uids: set[str],
    only_winning_path: bool = True,
    max_individuals: int = DEFAULT_MAX_INDIVIDUALS,
) -> dict[str, Any]:
    """Build the genealogy graph from normalised generations."""
    hidden_plateau = 0
    if only_winning_path:
        generations, hidden_plateau = _without_plateau_tail(generations)
    payload = LineageBuilder(
        generations, final_uids=final_uids, max_individuals=max_individuals
    ).build(only_winning_path=only_winning_path)
    payload["hidden_plateau_generations"] = hidden_plateau
    return payload

"""The shape a genealogy is built from, and the builder itself.

A run's ancestry can come from two places: the ``OptHistory`` saved when the run
finishes, or the population events the worker streams while it is still going.
Both are normalised into the structures here so a single builder produces the
graph -- a live genealogy and a finished one are then the same drawing, not two
implementations that drift apart.
"""

from __future__ import annotations

from dataclasses import dataclass, field, replace
from typing import Any

#: Selection is bookkeeping rather than a transformation, so it is not drawn.
HIDDEN_OPERATOR_TYPES = frozenset({"selection"})

#: Ceiling on how many individuals to describe, so a long run cannot produce a
#: payload the browser chokes on.
DEFAULT_MAX_INDIVIDUALS = 1500

#: GOLEM stores the seed populations and the result alongside the real
#: generations, so a run of seven generations reports ten. Labelling them keeps
#: the graph honest about how much evolution actually happened.
GENERATION_LABELS = {
    "initial_assumptions": "initial assumptions",
    "extended_initial_assumptions": "extended assumptions",
    "final_choices": "final choice",
}


@dataclass(frozen=True)
class LineageOperator:
    """A mutation or crossover that produced an individual."""

    uid: str
    type_: str
    label: str
    parent_uids: list[str]


@dataclass(frozen=True)
class LineageIndividual:
    """One pipeline as recorded in one generation."""

    uid: str
    fitness: float | None
    operations: list[str]
    native_generation: int | None
    #: Only meaningful for the generation that created this individual.
    operators: list[LineageOperator] = field(default_factory=list)


@dataclass(frozen=True)
class LineageGeneration:
    """One stored population, which may be evolution or bookkeeping."""

    index: int
    raw_label: str
    individuals: list[LineageIndividual]


def generation_metadata(generations: list[LineageGeneration]) -> list[dict[str, Any]]:
    """Describe each stored generation, separating evolution from bookkeeping."""
    metadata: list[dict[str, Any]] = []
    evolutionary_index = 0

    for generation in generations:
        is_evolutionary = generation.raw_label not in GENERATION_LABELS
        if is_evolutionary:
            evolutionary_index += 1
            label = f"gen {evolutionary_index}"
        else:
            label = GENERATION_LABELS[generation.raw_label]

        metadata.append(
            {
                "index": generation.index,
                "label": label,
                "raw_label": generation.raw_label,
                "size": len(generation.individuals),
                "is_evolutionary": is_evolutionary,
            }
        )
    return metadata


class LineageBuilder:
    """Assembles the genealogy graph from normalised generations."""

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
        #: (generation, individual uid) -> node id, so an individual that appears
        #: in several generations is a distinct node in each of them.
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
        """The most recent node for ``uid`` in a generation earlier than ``generation``.

        An individual can drop out of one population and come back in a later one
        -- elitism reintroduces archived graphs -- and a parent is not always
        recorded in the generation immediately before its child. Looking only one
        step back leaves those nodes with no incoming edge, which reads as a
        pipeline that appeared from nowhere.
        """
        for candidate in range(generation - 1, -1, -1):
            node_id = self._individual_nodes.get((candidate, uid))
            if node_id is not None:
                return node_id
        return None

    # ----------------------------------------------------------------- ancestry

    def _winning_uids(self) -> set[str]:
        """Every individual on a line of descent leading to the current best.

        Without this the graph shows every pipeline ever evaluated, which for a
        realistic run is thousands of nodes and no story.
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
            best_value: float | None = None
            best_node_id: str | None = None

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
                        "fitness": individual.fitness,
                        "operations": individual.operations,
                        "length": len(individual.operations),
                        "native_generation": individual.native_generation,
                        "is_best_in_generation": False,
                        "is_final_choice": individual.uid in self._final_uids,
                        "on_winning_path": individual.uid in winning,
                    }
                )
                self._individual_nodes[(generation.index, individual.uid)] = node_id
                described += 1

                if individual.fitness is not None and (
                    best_value is None or individual.fitness < best_value
                ):
                    best_value, best_node_id = individual.fitness, node_id

                # An individual carried over unchanged keeps its uid, so linking
                # the two copies shows survival as a continuous line.
                previous = self._latest_node_before(individual.uid, generation.index)
                if previous is not None:
                    self._add_edge(previous, node_id, "survival")

            if best_node_id is not None:
                next(n for n in self._nodes if n["id"] == best_node_id)["is_best_in_generation"] = True

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
        """Insert the mutation/crossover nodes between consecutive generations."""
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
                # Only the generation that first shows an individual draws the
                # operators that made it; later copies are survivors and are
                # linked as such. First appearance is used rather than
                # `native_generation` because the two sources number generations
                # differently -- GOLEM's live counter starts at one, the value
                # stored on an individual starts at zero -- and comparing the
                # wrong pair silently drops every operator.
                if self._latest_node_before(individual.uid, generation.index) is not None:
                    continue

                previous_node_id: str | None = None
                for operator in individual.operators:
                    if operator.type_ in HIDDEN_OPERATOR_TYPES or not operator.parent_uids:
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
                        # Operators applied in sequence, e.g. crossover then mutation.
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
    """Drop the evolutionary generations after the best fitness last improved.

    In the winning-path view those generations only repeat the same leader as a
    chain of survival edges, which reads as content while saying nothing. The
    bookkeeping generations (seeds and the final choice) always stay, and the
    kept generations are re-indexed to stay contiguous because the layout draws
    a placeholder row for every missing generation number.
    """
    best: float | None = None
    last_improvement: int | None = None
    for generation in generations:
        values = [ind.fitness for ind in generation.individuals if ind.fitness is not None]
        if not values:
            continue
        generation_best = min(values)
        if best is None or generation_best < best:
            best = generation_best
            if generation.raw_label not in GENERATION_LABELS:
                last_improvement = generation.index

    kept = [
        generation
        for generation in generations
        if generation.raw_label in GENERATION_LABELS
        or (last_improvement is not None and generation.index <= last_improvement)
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

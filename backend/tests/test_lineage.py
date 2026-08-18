"""Building the evolution genealogy from a GOLEM history."""

from __future__ import annotations

import pytest
from golem.core.optimisers.fitness.fitness import SingleObjFitness
from golem.core.optimisers.graph import OptGraph, OptNode
from golem.core.optimisers.opt_history_objects.individual import Individual
from golem.core.optimisers.opt_history_objects.opt_history import OptHistory
from golem.core.optimisers.opt_history_objects.parent_operator import ParentOperator

from fedotweb.history.lineage import history_to_lineage


def make_individual(operation: str, fitness: float, *, generation: int) -> Individual:
    individual = Individual(graph=OptGraph(OptNode(operation)), fitness=SingleObjFitness(fitness))
    individual.set_native_generation(generation)
    return individual


def descend(
    child_operation: str,
    fitness: float,
    *,
    parents: list[Individual],
    operator: str,
    generation: int,
) -> Individual:
    individual = Individual(
        graph=OptGraph(OptNode(child_operation)),
        fitness=SingleObjFitness(fitness),
        parent_operator=ParentOperator(
            type_=operator, operators=[f"{operator}_op"], parent_individuals=parents
        ),
    )
    individual.set_native_generation(generation)
    return individual


@pytest.fixture()
def history() -> OptHistory:
    """A three-generation run: two founders, a crossover, then a mutation.

        gen 0:  rf(-0.5)      logit(-0.6)
                     \\        /
        gen 1:        crossover -> child(-0.7),  logit survives
                          |
        gen 2:        mutation  -> winner(-0.9)
    """
    built = OptHistory()

    founder_a = make_individual("rf", -0.5, generation=0)
    founder_b = make_individual("logit", -0.6, generation=0)
    built.add_to_history([founder_a, founder_b])

    child = descend("dt", -0.7, parents=[founder_a, founder_b], operator="crossover", generation=1)
    # `founder_b` survives selection into generation 1 unchanged.
    built.add_to_history([child, founder_b])

    winner = descend("knn", -0.9, parents=[child], operator="mutation", generation=2)
    built.add_to_history([winner, child])

    built.add_to_history([winner], "final_choices")
    return built


def nodes_of(graph: dict, kind: str) -> list[dict]:
    return [node for node in graph["nodes"] if node["kind"] == kind]


def test_winning_path_keeps_only_the_ancestry(history: OptHistory) -> None:
    graph = history_to_lineage(history, only_winning_path=True)

    individuals = nodes_of(graph, "individual")
    uids = {node["uid"] for node in individuals}

    # Both founders are ancestors of the winner, so all four individuals appear.
    assert len(uids) == 4
    assert all(node["on_winning_path"] for node in individuals)


def test_operators_sit_between_the_generations_they_join(history: OptHistory) -> None:
    graph = history_to_lineage(history, only_winning_path=True)
    operators = nodes_of(graph, "operator")

    types = {node["operator_type"] for node in operators}
    assert types == {"crossover", "mutation"}

    for operator in operators:
        # Odd layers are reserved for operators; individuals occupy even ones.
        assert operator["layer"] % 2 == 1
        assert operator["layer"] == operator["generation"] * 2 - 1


def test_crossover_is_linked_to_both_parents(history: OptHistory) -> None:
    graph = history_to_lineage(history, only_winning_path=True)
    crossover = next(n for n in nodes_of(graph, "operator") if n["operator_type"] == "crossover")

    incoming = [edge for edge in graph["edges"] if edge["target"] == crossover["id"]]
    assert len(incoming) == 2, "a crossover must show where both parents came from"

    outgoing = [edge for edge in graph["edges"] if edge["source"] == crossover["id"]]
    assert len(outgoing) == 1
    assert outgoing[0]["kind"] == "produces"


def test_a_surviving_individual_is_linked_across_generations(history: OptHistory) -> None:
    graph = history_to_lineage(history, only_winning_path=True)
    survival = [edge for edge in graph["edges"] if edge["kind"] == "survival"]

    assert survival, "an individual carried into the next generation must stay connected"
    for edge in survival:
        source = next(n for n in graph["nodes"] if n["id"] == edge["source"])
        target = next(n for n in graph["nodes"] if n["id"] == edge["target"])
        assert source["uid"] == target["uid"]
        assert target["generation"] == source["generation"] + 1


def test_final_choice_and_generation_best_are_marked(history: OptHistory) -> None:
    graph = history_to_lineage(history, only_winning_path=True)
    individuals = nodes_of(graph, "individual")

    finals = [node for node in individuals if node["is_final_choice"]]
    assert finals and all(node["fitness"] == pytest.approx(-0.9) for node in finals)

    # The lowest fitness in generation 0 is the founder scoring -0.6.
    generation_zero = [node for node in individuals if node["generation"] == 0]
    best = [node for node in generation_zero if node["is_best_in_generation"]]
    assert len(best) == 1
    assert best[0]["fitness"] == pytest.approx(-0.6)


def test_full_mode_is_a_superset(history: OptHistory) -> None:
    winning = history_to_lineage(history, only_winning_path=True)
    full = history_to_lineage(history, only_winning_path=False)

    assert len(full["nodes"]) >= len(winning["nodes"])
    assert {node["id"] for node in winning["nodes"]} <= {node["id"] for node in full["nodes"]}


def test_edges_never_reference_a_missing_node(history: OptHistory) -> None:
    for only_winning in (True, False):
        graph = history_to_lineage(history, only_winning_path=only_winning)
        known = {node["id"] for node in graph["nodes"]}
        for edge in graph["edges"]:
            assert edge["source"] in known, edge
            assert edge["target"] in known, edge


def test_individual_cap_is_reported(history: OptHistory) -> None:
    graph = history_to_lineage(history, only_winning_path=False, max_individuals=2)
    assert graph["truncated"] is True
    assert len(nodes_of(graph, "individual")) <= 2


def test_an_empty_history_yields_an_empty_graph() -> None:
    graph = history_to_lineage(OptHistory(), only_winning_path=True)
    assert graph["nodes"] == []
    assert graph["edges"] == []
    assert graph["generations"] == 0


def test_an_individual_that_skips_a_generation_stays_connected() -> None:
    """Elitism can reintroduce a pipeline after it left the population.

    Linking only to the immediately preceding generation leaves the returning
    node with no incoming edge, which reads as a pipeline out of nowhere.
    """
    built = OptHistory()

    founder = make_individual("rf", -0.5, generation=0)
    other = make_individual("logit", -0.4, generation=0)
    built.add_to_history([founder, other])

    # `founder` is absent from generation 1 entirely.
    built.add_to_history([other])
    # ...and comes back in generation 2.
    built.add_to_history([founder, other])

    child = descend("dt", -0.9, parents=[founder], operator="mutation", generation=3)
    built.add_to_history([child])
    built.add_to_history([child], "final_choices")

    graph = history_to_lineage(built, only_winning_path=False)

    incoming = {edge["target"] for edge in graph["edges"]}
    first_layer = min(node["layer"] for node in graph["nodes"])
    orphans = [
        node for node in graph["nodes"] if node["layer"] > first_layer and node["id"] not in incoming
    ]
    assert orphans == [], f"nodes with no way in: {[node['id'] for node in orphans]}"

    # The survival edge must bridge the gap rather than be dropped.
    returning = next(
        node
        for node in graph["nodes"]
        if node["kind"] == "individual"
        and node["generation"] == 2
        and node["uid"] == str(founder.uid)
    )
    bridging = [
        edge for edge in graph["edges"] if edge["target"] == returning["id"] and edge["kind"] == "survival"
    ]
    assert len(bridging) == 1
    source = next(node for node in graph["nodes"] if node["id"] == bridging[0]["source"])
    assert source["generation"] == 0


def test_seed_and_result_rows_are_not_counted_as_evolution() -> None:
    """GOLEM stores the assumptions and the result as generations of their own.

    A run reporting ten stored generations may have evolved only seven times, and
    the graph must not claim otherwise.
    """
    built = OptHistory()
    founder = make_individual("rf", -0.5, generation=0)
    built.add_to_history([founder], "initial_assumptions")

    evolved = descend("dt", -0.8, parents=[founder], operator="mutation", generation=1)
    built.add_to_history([evolved])
    built.add_to_history([evolved], "final_choices")

    graph = history_to_lineage(built, only_winning_path=False)

    assert graph["generations"] == 3
    assert graph["evolution_generations"] == 1

    labels = {entry["index"]: entry["label"] for entry in graph["generation_meta"]}
    assert labels[0] == "initial assumptions"
    assert labels[1] == "gen 1"
    assert labels[2] == "final choice"

    flags = {entry["index"]: entry["is_evolutionary"] for entry in graph["generation_meta"]}
    assert flags == {0: False, 1: True, 2: False}

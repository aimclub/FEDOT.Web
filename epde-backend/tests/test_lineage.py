"""The genealogy graph."""

from __future__ import annotations

from epdeweb.history.live import lineage_from_events, normalise_generations, system_from_events
from epdeweb.history.model import (
    LineageGeneration,
    LineageIndividual,
    LineageOperator,
    build_lineage,
)


def individual(uid, *, objectives=(1.0, 2.0), rank=0, operators=(), terms=("du/dt",)):
    return LineageIndividual(
        uid=uid,
        objectives=list(objectives) if objectives else None,
        pareto_rank=rank,
        terms=list(terms),
        operators=list(operators),
    )


def crossover(uid, parents):
    return LineageOperator(uid=uid, type_="crossover", label="crossover", parent_uids=list(parents))


def mutation(uid, parents=()):
    return LineageOperator(uid=uid, type_="mutation", label="mutation", parent_uids=list(parents))


def test_a_surviving_candidate_is_joined_to_its_copy_in_the_next_generation():
    generations = [
        LineageGeneration(0, "initial population", [individual("a")], front_uids=["a"]),
        LineageGeneration(1, "gen 1", [individual("a")], front_uids=["a"]),
    ]
    graph = build_lineage(generations, final_uids={"a"}, only_winning_path=False)

    assert [edge["kind"] for edge in graph["edges"]] == ["survival"]
    assert len([node for node in graph["nodes"] if node["kind"] == "individual"]) == 2


def test_operators_are_drawn_between_the_generations_they_bridge():
    generations = [
        LineageGeneration(0, "initial population", [individual("a"), individual("b")], front_uids=["a"]),
        LineageGeneration(
            1,
            "gen 1",
            [individual("c", operators=[crossover("op1", ["a", "b"])])],
            front_uids=["c"],
        ),
    ]
    graph = build_lineage(generations, final_uids={"c"}, only_winning_path=False)

    operators = [node for node in graph["nodes"] if node["kind"] == "operator"]
    assert len(operators) == 1
    assert operators[0]["layer"] == 1  # between generation 0 (layer 0) and 1 (layer 2)

    kinds = sorted(edge["kind"] for edge in graph["edges"])
    assert kinds == ["crossover", "crossover", "produces"]


def test_a_chain_of_operators_reads_as_a_chain():
    generations = [
        LineageGeneration(0, "initial population", [individual("a"), individual("b")], front_uids=["a"]),
        LineageGeneration(
            1,
            "gen 1",
            [individual("c", operators=[crossover("op1", ["a", "b"]), mutation("op2")])],
            front_uids=["c"],
        ),
    ]
    graph = build_lineage(generations, final_uids={"c"}, only_winning_path=False)

    assert sum(1 for edge in graph["edges"] if edge["kind"] == "chain") == 1
    assert sum(1 for node in graph["nodes"] if node["kind"] == "operator") == 2


def test_the_winning_path_keeps_the_ancestry_of_the_whole_front():
    """A multi-objective run has no single winner.

    The tip of the lineage is the Pareto front, so both an accurate candidate
    and a simple one keep their ancestors -- which is the comparison a user is
    actually making.
    """
    generations = [
        LineageGeneration(
            0,
            "initial population",
            [individual("a"), individual("b"), individual("noise")],
            front_uids=["a", "b"],
        ),
        LineageGeneration(
            1,
            "gen 1",
            [
                individual("c", operators=[mutation("op1", ["a"])]),
                individual("d", operators=[mutation("op2", ["b"])]),
                individual("e", operators=[mutation("op3", ["noise"])]),
            ],
            front_uids=["c", "d"],
        ),
    ]
    graph = build_lineage(generations, final_uids={"c", "d"}, only_winning_path=True)

    shown = {node["uid"] for node in graph["nodes"] if node["kind"] == "individual"}
    assert shown == {"a", "b", "c", "d"}
    assert "noise" not in shown and "e" not in shown


def test_a_parent_from_two_generations_back_is_still_linked():
    """A candidate can leave a population and come back.

    Looking only one generation back would leave the returning node with no
    incoming edge, which reads as a system that appeared from nowhere.
    """
    generations = [
        LineageGeneration(0, "initial population", [individual("a")], front_uids=["a"]),
        LineageGeneration(1, "gen 1", [individual("b", operators=[mutation("op1", ["a"])])], front_uids=["b"]),
        LineageGeneration(
            2, "gen 2", [individual("c", operators=[mutation("op2", ["a"])])], front_uids=["c"]
        ),
    ]
    graph = build_lineage(generations, final_uids={"c"}, only_winning_path=False)

    incoming = [edge for edge in graph["edges"] if edge["target"].startswith("op:2:")]
    assert incoming, "the operator in generation 2 has no parent edge"


def test_generations_after_the_front_stops_changing_are_hidden():
    front = ["a"]
    generations = [
        LineageGeneration(0, "initial population", [individual("a")], front_uids=front),
        LineageGeneration(1, "gen 1", [individual("a")], front_uids=front),
        LineageGeneration(2, "gen 2", [individual("a")], front_uids=front),
    ]
    graph = build_lineage(generations, final_uids={"a"}, only_winning_path=True)

    assert graph["hidden_plateau_generations"] == 2
    assert graph["generations"] == 1


def test_the_seed_population_is_not_counted_as_a_generation_of_evolution():
    generations = [
        LineageGeneration(0, "initial population", [individual("a")], front_uids=["a"]),
        LineageGeneration(1, "gen 1", [individual("b", operators=[mutation("op1", ["a"])])], front_uids=["b"]),
    ]
    graph = build_lineage(generations, final_uids={"b"}, only_winning_path=False)

    assert graph["generations"] == 2
    assert graph["evolution_generations"] == 1
    assert [entry["label"] for entry in graph["generation_meta"]] == ["initial population", "gen 1"]


# ------------------------------------------------------------------ live events


def event(generation, individuals, front, label="gen 1"):
    return {
        "kind": "population",
        "payload": {
            "generation": generation,
            "label": label,
            "individuals": individuals,
            "front_uids": front,
        },
    }


def test_live_events_replay_into_the_same_graph():
    events = [
        event(0, [{"uid": "a", "objectives": [1.0, 2.0], "pareto_rank": 0, "terms": ["du/dt"]}], ["a"],
              label="initial population"),
        event(
            1,
            [
                {
                    "uid": "b",
                    "objectives": [0.5, 2.0],
                    "pareto_rank": 0,
                    "terms": ["du/dt"],
                    "operators": [{"uid": "op1", "type": "mutation", "label": "mutation", "parents": ["a"]}],
                }
            ],
            ["b"],
        ),
    ]
    graph = lineage_from_events(events, only_winning_path=True)

    assert graph is not None
    assert {node["uid"] for node in graph["nodes"] if node["kind"] == "individual"} == {"a", "b"}
    # Nothing is final while a run is going; the marker means "leading now".
    individuals = [node for node in graph["nodes"] if node["kind"] == "individual"]
    assert any(node["is_current_best"] for node in individuals)
    assert not any(node["is_final_choice"] for node in individuals)


def test_a_generation_reported_twice_keeps_only_its_latest_payload():
    first = event(3, [{"uid": "a", "objectives": [1.0], "terms": []}], ["a"])
    second = event(3, [{"uid": "a", "objectives": [0.1], "terms": []}], ["a"])
    generations = normalise_generations([first["payload"], second["payload"]])

    assert len(generations) == 1
    assert generations[0].individuals[0].objectives == [0.1]
    # Indices are re-based, so a replay starting at generation 3 still draws
    # from the top row.
    assert generations[0].index == 0


def test_the_system_of_a_candidate_comes_from_its_latest_report():
    events = [
        event(0, [{"uid": "a", "terms": [], "system": {"text": "old"}}], ["a"]),
        event(1, [{"uid": "a", "terms": [], "system": {"text": "new"}}], ["a"]),
    ]
    described = system_from_events(events, "a")

    assert described["text"] == "new"
    assert described["generation"] == 1

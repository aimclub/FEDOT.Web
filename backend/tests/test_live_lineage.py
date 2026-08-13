"""Building the genealogy from progress events, while a run is still going."""

from __future__ import annotations

from typing import Any

import pytest

from fedotweb.history.live import individual_pipeline_from_events, lineage_from_events


def population_event(
    generation: int,
    individuals: list[dict[str, Any]],
    best_uids: list[str] | None = None,
) -> dict[str, Any]:
    return {
        "kind": "population",
        "payload": {
            "generation": generation,
            "individuals": individuals,
            "best_uids": best_uids or [],
        },
    }


def individual(
    uid: str,
    fitness: float,
    operations: list[str],
    *,
    native: int,
    operators: list[dict[str, Any]] | None = None,
    graph: dict[str, Any] | None = None,
) -> dict[str, Any]:
    entry: dict[str, Any] = {
        "uid": uid,
        "fitness": fitness,
        "operations": operations,
        "native_generation": native,
    }
    if operators is not None:
        entry["operators"] = operators
    if graph is not None:
        entry["graph"] = graph
    return entry


@pytest.fixture()
def events() -> list[dict[str, Any]]:
    """Two generations: a founder pair, then a mutation of one of them."""
    return [
        {"kind": "status", "payload": {"status": "composing"}},
        population_event(
            1,
            [
                individual("a", -0.5, ["rf"], native=1),
                individual("b", -0.6, ["logit"], native=1),
            ],
            best_uids=["b"],
        ),
        population_event(
            2,
            [
                individual(
                    "c",
                    -0.8,
                    ["dt"],
                    native=2,
                    operators=[
                        {"uid": "op1", "type": "mutation", "label": "single_edge", "parents": ["b"]}
                    ],
                ),
                # `b` survives selection unchanged.
                individual("b", -0.6, ["logit"], native=1),
            ],
            best_uids=["c"],
        ),
    ]


def nodes_of(graph: dict, kind: str) -> list[dict]:
    return [node for node in graph["nodes"] if node["kind"] == kind]


def test_no_population_events_yields_nothing() -> None:
    assert lineage_from_events([{"kind": "status", "payload": {}}]) is None


def test_generations_are_reindexed_from_zero(events) -> None:
    """GOLEM counts generations from one; the graph's layers count from zero."""
    graph = lineage_from_events(events, only_winning_path=False)

    generations = sorted({node["generation"] for node in nodes_of(graph, "individual")})
    assert generations == [0, 1]
    assert graph["generations"] == 2
    assert graph["evolution_generations"] == 2


def test_operator_links_parent_to_child(events) -> None:
    graph = lineage_from_events(events, only_winning_path=False)

    operators = nodes_of(graph, "operator")
    assert len(operators) == 1
    assert operators[0]["operator_type"] == "mutation"
    assert operators[0]["label"] == "single_edge"

    incoming = [edge for edge in graph["edges"] if edge["target"] == operators[0]["id"]]
    outgoing = [edge for edge in graph["edges"] if edge["source"] == operators[0]["id"]]
    assert len(incoming) == 1 and incoming[0]["kind"] == "mutation"
    assert len(outgoing) == 1 and outgoing[0]["kind"] == "produces"


def test_survivors_are_linked_across_generations(events) -> None:
    graph = lineage_from_events(events, only_winning_path=False)
    survival = [edge for edge in graph["edges"] if edge["kind"] == "survival"]
    assert len(survival) == 1


def test_the_leader_is_marked_as_current_best_not_final(events) -> None:
    """Nothing is final while the run is going."""
    graph = lineage_from_events(events, only_winning_path=False)

    leaders = [node for node in nodes_of(graph, "individual") if node.get("is_current_best")]
    assert leaders and all(node["uid"] == "c" for node in leaders)
    assert not any(node["is_final_choice"] for node in nodes_of(graph, "individual"))


def test_winning_path_keeps_the_leader_ancestry(events) -> None:
    graph = lineage_from_events(events, only_winning_path=True)
    uids = {node["uid"] for node in nodes_of(graph, "individual")}
    # `c` descends from `b`; `a` is unrelated and must be dropped.
    assert uids == {"b", "c"}


def test_a_repeated_generation_keeps_the_latest_payload() -> None:
    """A replayed or resent generation must not double its population."""
    duplicated = [
        population_event(1, [individual("a", -0.5, ["rf"], native=1)]),
        population_event(1, [individual("a", -0.55, ["rf"], native=1)], best_uids=["a"]),
    ]
    graph = lineage_from_events(duplicated, only_winning_path=False)

    individuals = nodes_of(graph, "individual")
    assert len(individuals) == 1
    assert individuals[0]["fitness"] == pytest.approx(-0.55)


def test_leader_falls_back_to_the_best_scored_individual() -> None:
    """Before the archive reports anything, the lineage still needs a tip."""
    without_best = [
        population_event(
            1,
            [
                individual("a", -0.2, ["rf"], native=1),
                individual("b", -0.9, ["logit"], native=1),
            ],
        )
    ]
    graph = lineage_from_events(without_best, only_winning_path=True)
    assert {node["uid"] for node in nodes_of(graph, "individual")} == {"b"}


def test_edges_never_reference_a_missing_node(events) -> None:
    for only_winning in (True, False):
        graph = lineage_from_events(events, only_winning_path=only_winning)
        known = {node["id"] for node in graph["nodes"]}
        for edge in graph["edges"]:
            assert edge["source"] in known and edge["target"] in known


def test_individual_pipeline_is_reconstructed_from_the_stream() -> None:
    """Clicking a node during a run must open the pipeline it stands for."""
    streamed = [
        population_event(
            1,
            [
                individual(
                    "a",
                    -0.7,
                    ["scaling", "rf"],
                    native=1,
                    graph={
                        "nodes": [
                            {"id": "n0", "operation": "scaling", "params": {}},
                            {"id": "n1", "operation": "rf", "params": {"n_jobs": 2}},
                        ],
                        "edges": [{"source": "n0", "target": "n1"}],
                    },
                )
            ],
        )
    ]

    pipeline = individual_pipeline_from_events(streamed, "a")
    assert pipeline is not None
    assert [node["operation"] for node in pipeline["nodes"]] == ["scaling", "rf"]
    assert pipeline["depth"] == 2
    assert pipeline["fitness"] == pytest.approx(-0.7)

    root = next(node for node in pipeline["nodes"] if node["operation"] == "rf")
    assert root["params"] == {"n_jobs": 2}
    assert root["is_root"] is True
    # Catalogue metadata must be filled in so the editor canvas can draw it.
    assert root["group"] and root["defaults"]

    source = next(node for node in pipeline["nodes"] if node["operation"] == "scaling")
    assert source["is_primary"] is True


def test_unknown_individual_has_no_pipeline() -> None:
    assert individual_pipeline_from_events([], "nope") is None


def test_operators_survive_golems_offset_generation_counters() -> None:
    """The two counters GOLEM exposes are offset by one, and the graph must cope.

    A live population event carries the optimiser's ``current_generation_num``,
    which starts at one, while each individual carries ``native_generation``,
    which starts at zero. Deciding which generation "owns" an individual by
    comparing those two silently drops every operator, leaving a genealogy of
    nothing but survival edges.
    """
    offset_events = [
        population_event(
            1,  # optimiser counts from one...
            [individual("a", -0.5, ["rf"], native=0)],  # ...individuals from zero
        ),
        population_event(
            2,
            [
                individual(
                    "b",
                    -0.9,
                    ["dt"],
                    native=1,
                    operators=[
                        {"uid": "op1", "type": "mutation", "label": "single_edge", "parents": ["a"]}
                    ],
                ),
                individual("a", -0.5, ["rf"], native=0),
            ],
            best_uids=["b"],
        ),
    ]

    graph = lineage_from_events(offset_events, only_winning_path=True)

    operators = nodes_of(graph, "operator")
    assert operators, "the mutation that produced the leader was dropped"
    assert operators[0]["operator_type"] == "mutation"

    kinds = {edge["kind"] for edge in graph["edges"]}
    assert "mutation" in kinds and "produces" in kinds


def test_a_survivor_does_not_redraw_its_operators() -> None:
    """An individual carried forward is linked as a survivor, not re-created."""
    carried = [
        population_event(1, [individual("a", -0.5, ["rf"], native=0)]),
        population_event(
            2,
            [
                individual(
                    "b",
                    -0.9,
                    ["dt"],
                    native=1,
                    operators=[
                        {"uid": "op1", "type": "mutation", "label": "m", "parents": ["a"]}
                    ],
                ),
            ],
            best_uids=["b"],
        ),
        # `b` survives; the worker resends its operators, which must be ignored here.
        population_event(
            3,
            [
                individual(
                    "b",
                    -0.9,
                    ["dt"],
                    native=1,
                    operators=[
                        {"uid": "op1", "type": "mutation", "label": "m", "parents": ["a"]}
                    ],
                ),
            ],
            best_uids=["b"],
        ),
    ]

    graph = lineage_from_events(carried, only_winning_path=False)

    operators = nodes_of(graph, "operator")
    assert len(operators) == 1, "the operator must be drawn once, in the generation that used it"
    assert operators[0]["generation"] == 1

    survival = [edge for edge in graph["edges"] if edge["kind"] == "survival"]
    assert len(survival) == 1

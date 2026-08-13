"""Round-tripping between FEDOT pipelines and the editor's graph format."""

from __future__ import annotations

import pytest
from fedot.core.pipelines.node import PipelineNode
from fedot.core.pipelines.pipeline import Pipeline

from fedotweb.pipelines.convert import (
    PipelineConversionError,
    graph_to_pipeline,
    pipeline_to_graph,
    validate_graph,
)


def edges_of(graph) -> set:
    return {(edge["source"], edge["target"]) for edge in graph["edges"]}


def test_chain_round_trips() -> None:
    scaling = PipelineNode("scaling")
    root = PipelineNode("rf", nodes_from=[scaling])
    graph = pipeline_to_graph(Pipeline([scaling, root]))

    assert [node["operation"] for node in graph["nodes"]] == ["scaling", "rf"]
    assert graph["depth"] == 2 and graph["length"] == 2

    rebuilt = pipeline_to_graph(graph_to_pipeline(graph))
    assert edges_of(rebuilt) == edges_of(graph)


def test_diamond_topology_survives() -> None:
    scaling = PipelineNode("scaling")
    left = PipelineNode("rf", nodes_from=[scaling])
    right = PipelineNode("logit", nodes_from=[scaling])
    root = PipelineNode("xgboost", nodes_from=[left, right])

    graph = pipeline_to_graph(Pipeline([scaling, left, right, root]))
    assert len(graph["nodes"]) == 4
    assert len(graph["edges"]) == 4

    rebuilt = pipeline_to_graph(graph_to_pipeline(graph))
    assert edges_of(rebuilt) == edges_of(graph)


def test_identical_parallel_branches_are_not_merged() -> None:
    """Two structurally identical branches are distinct nodes, not one.

    De-duplicating by descriptive id — as the previous implementation did —
    silently collapses this pipeline into a three-node chain.
    """
    graph = {
        "nodes": [
            {"id": "s", "operation": "scaling", "params": {}},
            {"id": "a", "operation": "rf", "params": {}},
            {"id": "b", "operation": "rf", "params": {}},
            {"id": "r", "operation": "logit", "params": {}},
        ],
        "edges": [
            {"source": "s", "target": "a"},
            {"source": "s", "target": "b"},
            {"source": "a", "target": "r"},
            {"source": "b", "target": "r"},
        ],
    }
    pipeline = graph_to_pipeline(graph)
    assert pipeline.length == 4


def test_parameters_round_trip() -> None:
    graph = {
        "nodes": [
            {"id": "s", "operation": "scaling", "params": {}},
            {"id": "r", "operation": "rf", "params": {"n_jobs": 1, "criterion": "entropy"}},
        ],
        "edges": [{"source": "s", "target": "r"}],
    }
    described = pipeline_to_graph(graph_to_pipeline(graph))
    root = next(node for node in described["nodes"] if node["operation"] == "rf")
    assert root["params"]["criterion"] == "entropy"


def test_integer_node_ids_are_accepted() -> None:
    """The legacy frontend numbered its nodes; those payloads must still load."""
    graph = {
        "nodes": [
            {"id": 0, "operation": "scaling", "params": {}},
            {"id": 1, "operation": "rf", "params": {}},
        ],
        "edges": [{"source": 0, "target": 1}],
    }
    assert graph_to_pipeline(graph).length == 2


def test_cycles_are_rejected() -> None:
    graph = {
        "nodes": [
            {"id": "a", "operation": "scaling", "params": {}},
            {"id": "b", "operation": "rf", "params": {}},
        ],
        "edges": [{"source": "a", "target": "b"}, {"source": "b", "target": "a"}],
    }
    with pytest.raises(PipelineConversionError, match="cycle"):
        graph_to_pipeline(graph)

    is_valid, problems = validate_graph(graph, task="classification")
    assert not is_valid
    assert any("cycle" in problem for problem in problems)


def test_empty_graph_is_rejected() -> None:
    with pytest.raises(PipelineConversionError, match="empty"):
        graph_to_pipeline({"nodes": [], "edges": []})


def test_edge_to_unknown_node_is_rejected() -> None:
    graph = {
        "nodes": [{"id": "a", "operation": "rf", "params": {}}],
        "edges": [{"source": "a", "target": "ghost"}],
    }
    with pytest.raises(PipelineConversionError, match="unknown target"):
        graph_to_pipeline(graph)


def test_unknown_operation_is_reported() -> None:
    graph = {"nodes": [{"id": "a", "operation": "not_a_model", "params": {}}], "edges": []}
    is_valid, problems = validate_graph(graph)
    assert not is_valid
    assert any("Unknown operation" in problem for problem in problems)


def test_validation_is_task_aware() -> None:
    """A table model alone is fine for classification but not for forecasting."""
    graph = {"nodes": [{"id": "a", "operation": "rf", "params": {}}], "edges": []}

    assert validate_graph(graph, task="classification")[0] is True

    is_valid, problems = validate_graph(graph, task="ts_forecasting")
    assert is_valid is False
    # The message must be readable rather than FEDOT's raw rule repr.
    assert problems and "0x" not in problems[0]
    assert "rule:" in problems[0]


def test_multi_root_pipeline_can_still_be_described() -> None:
    """The editor must be able to draw an invalid graph so it can be fixed."""
    first = PipelineNode("rf")
    second = PipelineNode("logit")
    graph = pipeline_to_graph(Pipeline([first, second]))

    assert len(graph["nodes"]) == 2
    assert all(node["is_root"] is False for node in graph["nodes"])

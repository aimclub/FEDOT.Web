"""Conversion between FEDOT pipelines and the graph format the editor speaks.

The legacy implementation rebuilt parent nodes recursively and de-duplicated them
by ``descriptive_id``, which silently merged distinct nodes that happened to have
identical operations and parameters -- a diamond-shaped pipeline could come back
with the wrong topology.  Here the graph is built in topological order instead,
so every editor node maps to exactly one pipeline node.
"""

from __future__ import annotations

import re
from collections import deque
from collections.abc import Iterable, Sequence
from typing import Any

from fedot.core.pipelines.node import PipelineNode
from fedot.core.pipelines.pipeline import Pipeline
from fedot.core.pipelines.verification import verify_pipeline
from fedot.core.repository.tasks import Task, TaskTypesEnum

from ..catalog import get_catalog
from ..catalog.hyperparams import _json_safe

#: FEDOT writes this sentinel instead of an empty parameter dict.
DEFAULT_PARAMS_STUB = "default_params"


class PipelineConversionError(ValueError):
    """Raised when an editor graph cannot be expressed as a FEDOT pipeline."""


def _normalise_params(params: Any) -> dict[str, Any]:
    """Coerce whatever FEDOT stored in ``node.parameters`` into a plain dict."""
    if not params or params == DEFAULT_PARAMS_STUB:
        return {}
    if isinstance(params, dict):
        return _json_safe(params)
    return {}


def pipeline_to_graph(pipeline: Pipeline, *, uid: str | None = None) -> dict[str, Any]:
    """Describe a fitted or unfitted pipeline as an editor graph.

    Node ids are positional (``n0``, ``n1``, ...) and stable for a given pipeline
    object, which is what lets the UI diff two graphs.
    """
    catalog = get_catalog()
    index_of: dict[int, str] = {}
    nodes: list[dict[str, Any]] = []

    for position, node in enumerate(pipeline.nodes):
        node_id = f"n{position}"
        index_of[id(node)] = node_id

        operation_id = node.operation.operation_type
        described = catalog.get(operation_id) or {}
        nodes.append(
            {
                "id": node_id,
                "operation": operation_id,
                "label": operation_id,
                "kind": described.get("kind", "model"),
                "group": described.get("group", "model"),
                "description": described.get("description"),
                "tags": described.get("tags", []),
                "params": _normalise_params(node.parameters),
                "defaults": described.get("defaults", {}),
                "parents": [],
                "children": [],
                "is_primary": not node.nodes_from,
                "is_root": False,
            }
        )

    by_id = {node["id"]: node for node in nodes}
    edges: list[dict[str, str]] = []

    for position, node in enumerate(pipeline.nodes):
        node_id = f"n{position}"
        for parent in node.nodes_from or []:
            parent_id = index_of.get(id(parent))
            if parent_id is None:
                # A parent outside ``pipeline.nodes`` means the pipeline is malformed.
                continue
            edges.append({"id": f"{parent_id}->{node_id}", "source": parent_id, "target": node_id})
            by_id[node_id]["parents"].append(parent_id)
            by_id[parent_id]["children"].append(node_id)

    # ``root_node`` raises when a pipeline has more than one sink; the editor must
    # still be able to display such a graph so the user can fix it.
    try:
        root = pipeline.root_node if pipeline.nodes else None
    except ValueError:
        root = None
    if root is not None:
        root_id = index_of.get(id(root))
        if root_id in by_id:
            by_id[root_id]["is_root"] = True

    return {
        "uid": uid or "",
        "nodes": nodes,
        "edges": edges,
        "depth": pipeline.depth if pipeline.nodes else 0,
        "length": pipeline.length if pipeline.nodes else 0,
    }


def _topological_order(node_ids: Sequence[str], parents_of: dict[str, list[str]]) -> list[str]:
    """Kahn's algorithm; raises when the editor graph contains a cycle."""
    remaining = {node_id: len(parents_of.get(node_id, [])) for node_id in node_ids}
    children_of: dict[str, list[str]] = {node_id: [] for node_id in node_ids}
    for node_id, parents in parents_of.items():
        for parent in parents:
            if parent in children_of:
                children_of[parent].append(node_id)

    queue = deque(sorted(node_id for node_id, degree in remaining.items() if degree == 0))
    order: list[str] = []
    while queue:
        current = queue.popleft()
        order.append(current)
        for child in children_of[current]:
            remaining[child] -= 1
            if remaining[child] == 0:
                queue.append(child)

    if len(order) != len(node_ids):
        raise PipelineConversionError("The pipeline graph contains a cycle")
    return order


def graph_to_pipeline(graph: dict[str, Any]) -> Pipeline:
    """Build a FEDOT pipeline from an editor graph.

    Accepts both the string ids this backend emits and the integer ids the legacy
    frontend used.
    """
    raw_nodes: Iterable[dict[str, Any]] = graph.get("nodes") or []
    nodes_by_id: dict[str, dict[str, Any]] = {}
    for raw in raw_nodes:
        if "id" not in raw:
            raise PipelineConversionError("Every node must carry an id")
        node_id = str(raw["id"])
        if node_id in nodes_by_id:
            raise PipelineConversionError(f"Duplicate node id: {node_id}")
        nodes_by_id[node_id] = raw

    if not nodes_by_id:
        raise PipelineConversionError("The pipeline is empty")

    parents_of: dict[str, list[str]] = {node_id: [] for node_id in nodes_by_id}
    for edge in graph.get("edges") or []:
        source, target = str(edge.get("source")), str(edge.get("target"))
        if source not in nodes_by_id:
            raise PipelineConversionError(f"Edge refers to an unknown source node: {source}")
        if target not in nodes_by_id:
            raise PipelineConversionError(f"Edge refers to an unknown target node: {target}")
        if source == target:
            raise PipelineConversionError(f"Node {source} cannot be its own parent")
        if source not in parents_of[target]:
            parents_of[target].append(source)

    built: dict[str, PipelineNode] = {}
    for node_id in _topological_order(list(nodes_by_id), parents_of):
        raw = nodes_by_id[node_id]
        operation = raw.get("operation") or raw.get("model_name") or raw.get("display_name")
        if not operation:
            raise PipelineConversionError(f"Node {node_id} has no operation")

        parents = [built[parent] for parent in parents_of[node_id]]
        node = PipelineNode(str(operation), nodes_from=parents or None)

        params = raw.get("params")
        if isinstance(params, dict) and params:
            node.parameters = _json_safe(params)

        built[node_id] = node

    pipeline = Pipeline(list(built.values()))
    return pipeline


#: FEDOT reports rule failures as one long string that embeds the rule's ``repr``
#: and the whole graph.  Only the bracketed reason and the rule name are useful.
_VERIFICATION_REASON = re.compile(r"<([^>]+)>")
_RULE_NAME = re.compile(r"function (\w+) at 0x")


def _readable_verification_error(message: str) -> str:
    """Turn FEDOT's verification message into something worth showing a user."""
    reason_match = _VERIFICATION_REASON.search(message)
    if not reason_match:
        return message.split(" on graph=")[0].strip()

    reason = reason_match.group(1)
    # Strip the "Invalid pipeline configuration:" prefix FEDOT adds to every rule.
    reason = reason.split(":", 1)[-1].strip() if ":" in reason else reason

    rule_match = _RULE_NAME.search(message)
    if rule_match:
        rule = rule_match.group(1).replace("_", " ")
        return f"{reason} (rule: {rule})"
    return reason


def validate_graph(graph: dict[str, Any], task: str | None = None) -> tuple[bool, list[str]]:
    """Check a graph both structurally and against FEDOT's own pipeline rules.

    Unlike the legacy endpoint, the task type is taken into account, so
    time-series-specific rules (a lagged transform before a table model, and so
    on) are actually applied.
    """
    problems: list[str] = []
    catalog = get_catalog()

    for raw in graph.get("nodes") or []:
        operation = raw.get("operation") or raw.get("model_name")
        if operation and not catalog.exists(str(operation)):
            problems.append(f"Unknown operation: {operation}")

    try:
        pipeline = graph_to_pipeline(graph)
    except PipelineConversionError as exc:
        problems.append(str(exc))
        return False, problems

    task_obj = None
    if task:
        try:
            task_obj = Task(TaskTypesEnum(task))
        except ValueError:
            problems.append(f"Unknown task type: {task}")

    try:
        verify_pipeline(pipeline, task_type=task_obj.task_type if task_obj else None, raise_on_failure=True)
    except Exception as exc:  # FEDOT raises ValueError subclasses with rule-specific messages
        problems.append(_readable_verification_error(str(exc)))

    return not problems, problems

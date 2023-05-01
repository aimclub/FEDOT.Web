import json
from typing import Dict, List, Optional, Union

from fedot.core.pipelines.node import PipelineNode, PrimaryNode, SecondaryNode
from fedot.core.pipelines.pipeline import Pipeline
from fedot.core.repository.operation_types_repository import \
    OperationTypesRepository
from golem.core.optimisers.opt_history_objects.individual import Individual

from .models import PipelineGraph


def graph_to_pipeline(graph: dict) -> Pipeline:
    graph_nodes = graph['nodes']

    pipeline_nodes: List[PipelineNode] = []

    # all parents should be taken from edges dict
    for graph_node in graph_nodes:
        graph_node['parents'] = []
        graph_node['children'] = []

    for edge in graph['edges']:
        parent_id = edge['source']
        child_id = edge['target']

        for graph_node in graph_nodes:
            if graph_node['id'] == child_id:
                graph_node['parents'].append(parent_id)
            elif graph_node['id'] == parent_id:
                graph_node['children'].append(child_id)

    for graph_node in graph_nodes:
        pipeline_node = _graph_node_to_pipeline_node(graph_node, graph_nodes, pipeline_nodes)
        pipeline_nodes = _add_to_pipeline_if_necessary(pipeline_node, pipeline_nodes)

    pipeline = Pipeline(pipeline_nodes)

    return pipeline


def pipeline_to_graph(pipeline: Pipeline) -> PipelineGraph:
    nodes = []
    edges = []

    local_id = 0
    for pipeline_node in pipeline.nodes:
        node = replace_deprecated_values({
            'id': local_id,
            'display_name': pipeline_node.operation.operation_type,
            'model_name': str(pipeline_node.operation),
            'params': pipeline_node.parameters
        })
        pipeline_node.tmp_id = local_id
        node['pipeline_node'] = pipeline_node
        node['type'] = _get_node_type_for_model(pipeline_node.operation.operation_type)

        nodes.append(node)
        local_id += 1

    for node in nodes:
        node['parents'] = []
        node['children'] = []
        nodes_from_pipeline = node['pipeline_node'].nodes_from
        if nodes_from_pipeline is not None:
            for pipeline_node_parent in nodes_from_pipeline:
                # fill parents field
                node['parents'].append(pipeline_node_parent.tmp_id)

                # create edge
                edges.append({
                    'source': pipeline_node_parent.tmp_id,
                    'target': node['id']
                })

            children = pipeline._operator.node_children(node['pipeline_node']) if hasattr(pipeline, '_operator') \
                else pipeline.node_children(node['pipeline_node'])  # TODO Temporary solution until FEDOT is updated
            if children is not None:
                # fill children field
                for pipeline_node_child in children:
                    node['children'].append(pipeline_node_child.tmp_id)
        del node['pipeline_node']

    output_graph = PipelineGraph(uid='', nodes=nodes, edges=edges)

    return output_graph


def golem_to_graph(graph_individual: Individual) -> PipelineGraph:
    nodes = []
    edges = []

    local_id = 0
    for graph_node in graph_individual.graph.nodes:
        node = replace_deprecated_values({
            'id': local_id,
            'display_name': graph_node.name,
            'model_name': str(graph_node.name),
            'params': graph_node.description()
        })
        graph_node.tmp_id = local_id
        node['pipeline_node'] = graph_node
        node['type'] = 'graph_node'

        nodes.append(node)
        local_id += 1

    for node in nodes:
        node['parents'] = []
        node['children'] = []
        nodes_from_pipeline = node['pipeline_node'].nodes_from
        if nodes_from_pipeline is not None:
            for pipeline_node_parent in nodes_from_pipeline:
                # fill parents field
                node['parents'].append(pipeline_node_parent.tmp_id)

                # create edge
                edges.append({
                    'source': pipeline_node_parent.tmp_id,
                    'target': node['id']
                })
        del node['pipeline_node']

    output_graph = PipelineGraph(uid='', nodes=nodes, edges=edges)

    return output_graph


def replace_deprecated_values(graph_node: dict, depr_values: tuple = ('Infinity', 'NaN')) -> dict:
    txt = json.dumps(graph_node)
    for val in depr_values:
        txt = txt.replace(val, 'null')
    graph_node = json.loads(txt)
    return graph_node


def _graph_node_to_pipeline_node(
        graph_node: dict, existing_graph_nodes: List[Dict], pipeline_nodes: List[PipelineNode]
) -> Union[PrimaryNode, SecondaryNode]:
    if not graph_node['parents']:
        pipeline_node = PrimaryNode(graph_node['model_name'])
    else:
        parent_pipeline_nodes = []
        for parent_id in graph_node['parents']:
            parent_node = next((n for n in existing_graph_nodes if n['id'] == parent_id), None)

            if parent_node is None:
                continue

            parent_pipeline_node = _graph_node_to_pipeline_node(parent_node, existing_graph_nodes, pipeline_nodes)

            # check is parent node already created
            existing_pipeline_node = _get_identical_pipeline_node(parent_pipeline_node, pipeline_nodes)
            if existing_pipeline_node is not None:
                parent_pipeline_node = existing_pipeline_node

            parent_pipeline_nodes.append(parent_pipeline_node)
            pipeline_nodes = _add_to_pipeline_if_necessary(parent_pipeline_node, pipeline_nodes)

        pipeline_node = SecondaryNode(graph_node['model_name'], nodes_from=parent_pipeline_nodes)

    if graph_node['params'] != 'default_params':
        pipeline_node.parameters = graph_node['params']

    return pipeline_node


def _add_to_pipeline_if_necessary(new_node: PipelineNode, pipeline_nodes: List[PipelineNode]) -> List[PipelineNode]:
    if new_node.descriptive_id not in [_.descriptive_id for _ in pipeline_nodes]:
        pipeline_nodes.append(new_node)
    return pipeline_nodes


def _get_identical_pipeline_node(node: PipelineNode, pipeline_nodes: List[PipelineNode]) -> Optional[PipelineNode]:
    return next((_ for _ in pipeline_nodes if _.descriptive_id == node.descriptive_id), None)


def _get_node_type_for_model(model_type: str) -> str:
    data_operations = OperationTypesRepository(operation_type='data_operation').operations

    if model_type in [op.id for op in data_operations]:
        return 'data_operation'
    return 'model'

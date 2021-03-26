from fedot.core.chains.chain import Chain
from fedot.core.chains.node import PrimaryNode, SecondaryNode
from fedot.core.repository.operation_types_repository import OperationTypesRepository

from .models import ChainGraph


def graph_to_chain(graph: dict):
    graph_nodes = graph['nodes']

    chain_nodes = []
    for graph_node in graph_nodes:
        chain_node = _graph_node_to_chain_node(graph_node, graph_nodes, chain_nodes)
        chain_nodes = _add_to_chain_if_necessary(chain_node, chain_nodes)

    chain = Chain(chain_nodes)

    return chain


def chain_to_graph(chain):
    nodes = []
    edges = []

    local_id = 0
    for chain_node in chain.nodes:
        node = dict()

        node['id'] = local_id
        chain_node.tmp_id = local_id
        node['display_name'] = chain_node.operation.operation_type
        node['model_name'] = chain_node.operation.operation_type
        node['params'] = chain_node.custom_params
        node['chain_node'] = chain_node
        node['type'] = _get_node_type_for_model(chain_node.operation.operation_type)

        nodes.append(node)
        local_id += 1

    for node in nodes:
        node['parents'] = []
        node['children'] = []
        if node['chain_node'].nodes_from is not None:
            for chain_node_parent in node['chain_node'].nodes_from:
                # fill parents field
                node['parents'].append(chain_node_parent.tmp_id)

                # create edge
                edge = dict()
                edge['source'] = chain_node_parent.tmp_id
                edge['target'] = node['id']
                edges.append(edge)

            childs = chain.node_childs(node['chain_node'])
            if childs is not None:
                # fill childs field
                for chain_node_child in childs:
                    node['children'].append(chain_node_child.tmp_id)
        del node['chain_node']

    output_graph = ChainGraph(uid='', nodes=nodes, edges=edges)

    return output_graph


def _graph_node_to_chain_node(graph_node: dict, existing_graph_nodes: dict, chain_nodes):
    is_primary = len(graph_node['parents']) == 0

    if is_primary:
        chain_node = PrimaryNode(graph_node['model_name'])
    else:
        parent_chain_nodes = []
        for parent_id in graph_node['parents']:
            parent_node = existing_graph_nodes[parent_id]
            parent_chain_node = _graph_node_to_chain_node(parent_node, existing_graph_nodes, chain_nodes)

            # check is parent node already created
            existing_chain_node = _get_identical_chain_node(parent_chain_node, chain_nodes)
            if existing_chain_node is not None:
                parent_chain_node = existing_chain_node

            parent_chain_nodes.append(parent_chain_node)
            chain_nodes = _add_to_chain_if_necessary(parent_chain_node, chain_nodes)

        chain_node = SecondaryNode(graph_node['model_name'], nodes_from=parent_chain_nodes)

    if graph_node['params'] != 'default_params':
        chain_node.custom_params = graph_node['params']

    return chain_node


def _add_to_chain_if_necessary(new_node, chain_nodes):
    chain_nodes_ids = [_.descriptive_id for _ in chain_nodes]
    if new_node.descriptive_id not in chain_nodes_ids:
        chain_nodes.append(new_node)
    return chain_nodes


def _get_identical_chain_node(node, chain_nodes):
    try:
        return [_ for _ in chain_nodes if _.descriptive_id == node.descriptive_id][0]
    except IndexError:
        return None


def _get_node_type_for_model(model_type: str):
    # TODO refactor after new preprocessing release

    data_operations = OperationTypesRepository(repository_name='data_operation_repository.json').operations

    if model_type in [op.id for op in data_operations]:
        return 'data_operation'
    else:
        return 'model'

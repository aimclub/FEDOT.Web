import json
import warnings

from fedot.core.chains.chain import Chain

from utils import project_root


def chain_by_uid(uid: str) -> dict:
    chain = Chain()
    chain.load_chain(f'{project_root()}/data/mocked_jsons/chain.json')
    graph_json = _chain_to_graph_info(chain)
    graph_json['uid'] = uid
    return graph_json


def create_chain_from_graph(graph: dict):
    # TODO convert graph to Chain

    # TODO search chain with same structure and data in database
    is_new = True

    existing_uid = 'test_chain'
    if graph['uid'] == existing_uid:
        is_new = False

    with open(f'{project_root()}/data/mocked_jsons/chain.json') as f:
        chain = json.load(f)
        uid = chain['uid']

    if not is_new:
        uid = existing_uid
    else:
        # TODO save chain to database
        warnings.warn('Cannot create new chain')

    return uid, is_new


def _chain_to_graph_info(chain):
    output_graph = {}
    nodes = []
    links = []

    local_id = 0
    for chain_node in chain.nodes:
        node = dict()

        node['id'] = local_id
        chain_node.tmp_id = local_id
        node['display_name'] = chain_node.model.model_type
        node['model_name'] = chain_node.model.model_type
        node['class'] = 'model'
        node['params'] = chain_node.custom_params
        node['chain_node'] = chain_node

        nodes.append(node)
        local_id += 1

    for node in nodes:
        node['parents'] = []
        if node['chain_node'].nodes_from is not None:
            for chain_node_parent in node['chain_node'].nodes_from:
                node['parents'].append(chain_node_parent.tmp_id)
                link = dict()
                link['source'] = chain_node_parent.tmp_id
                link['target'] = node['id']
                links.append(link)
        else:
            node['class'] = 'preprocessing'  # TODO remove later
        del node['chain_node']

    output_graph['nodes'] = nodes
    output_graph['links'] = links

    return output_graph

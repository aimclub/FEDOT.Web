from fedot.core.chains.chain import Chain

from app.api.chains.chain_convert_utils import chain_to_graph, graph_to_chain
from utils import project_root


def test_get_chain_conversion():
    initial_chain = Chain()
    initial_chain.load(f'{project_root()}/data/mocked_jsons/chain.json')
    graph_from_chain = chain_to_graph(initial_chain)

    graph_json = {'uid': graph_from_chain.uid, 'nodes': graph_from_chain.nodes, 'edges': graph_from_chain.edges}
    chain_from_graph = graph_to_chain(graph_json)

    assert initial_chain.root_node.descriptive_id == chain_from_graph.root_node.descriptive_id

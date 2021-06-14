from app.api.chains.chain_convert_utils import chain_to_graph, graph_to_chain
from app.api.chains.service import chain_mock


def test_get_chain_conversion():
    initial_chain = chain_mock()
    graph_from_chain = chain_to_graph(initial_chain)

    graph_json = {'uid': graph_from_chain.uid, 'nodes': graph_from_chain.nodes, 'edges': graph_from_chain.edges}
    chain_from_graph = graph_to_chain(graph_json)

    assert initial_chain.root_node.descriptive_id == chain_from_graph.root_node.descriptive_id

import json
import os

from app.api.chains.chain_convert_utils import chain_to_graph, graph_to_chain, replace_deprecated_values
from init.init_chains import chain_mock
from utils import project_root


def test_get_chain_conversion():
    initial_chain = chain_mock()
    graph_from_chain = chain_to_graph(initial_chain)

    graph_json = {'uid': graph_from_chain.uid, 'nodes': graph_from_chain.nodes, 'edges': graph_from_chain.edges}
    chain_from_graph = graph_to_chain(graph_json)

    assert initial_chain.root_node.descriptive_id == chain_from_graph.root_node.descriptive_id


def test_replace_deprecated_values():
    with open(os.path.join(project_root(), "test", "data", "graph_example.json")) as f:
        graph = json.load(f)
        dumped_graph = json.dumps(graph)

        assert dumped_graph.find('Infinity') != -1
        assert dumped_graph.find('NaN') != -1

        dumped_graph = replace_deprecated_values(dumped_graph)

        assert dumped_graph.find('Infinity') == -1
        assert dumped_graph.find('NaN') == -1

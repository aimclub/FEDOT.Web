import json
import os

from app.api.pipelines.pipeline_convert_utils import pipeline_to_graph, graph_to_pipeline, \
    replace_deprecated_values
from init.init_pipelines import pipeline_mock
from utils import project_root


def test_get_pipeline_conversion():
    initial_pipeline = pipeline_mock()
    graph_from_pipeline = pipeline_to_graph(initial_pipeline)

    graph_json = {'uid': graph_from_pipeline.uid, 'nodes': graph_from_pipeline.nodes,
                  'edges': graph_from_pipeline.edges}
    pipeline_from_graph = graph_to_pipeline(graph_json)

    assert initial_pipeline.root_node.descriptive_id == \
           pipeline_from_graph.root_node.descriptive_id


def test_replace_deprecated_values():
    with open(os.path.join(project_root(), "test", "data", "graph_example.json")) as f:
        graph = json.load(f)
        dumped_graph = json.dumps(graph)

        assert dumped_graph.find('Infinity') != -1
        assert dumped_graph.find('NaN') != -1

        dumped_graph = replace_deprecated_values(dumped_graph)

        assert dumped_graph.find('Infinity') == -1
        assert dumped_graph.find('NaN') == -1

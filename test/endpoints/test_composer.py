import random

import numpy as np

random.seed(1)
np.random.seed(1)


def test_composer_endpoint(client):
    case_id = 'scoring'
    history_json = client.get(f'api/composer/{case_id}').json
    nodes = history_json['nodes']
    nodes_ids = [n['uid'] for n in nodes]
    edges = history_json['edges']

    targets = [e['target'] for e in history_json['edges']]
    sources = [e['source'] for e in history_json['edges']]

    assert len(nodes) > 0
    assert len(edges) > 0

    assert len(nodes_ids) == len(set(nodes_ids))

    for node_id in nodes_ids:
        assert node_id in targets or node_id in sources or 'ind_' in node_id

    for edge in edges:
        assert edge['source'] in nodes_ids
        assert edge['target'] in nodes_ids
        assert edge['source'] != edge['target']
        reverse_edge = {
            'source': edge['target'],
            'target': edge['source']
        }
        assert reverse_edge not in edges

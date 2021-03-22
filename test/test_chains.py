import json

from fedot.core.chains.chain import Chain

from app.api.chains.chain_convert_utils import chain_to_graph
from utils import project_root


def test_get_chain_endpoint(client):
    uid = 'test_chain'
    history_json = client.get(f'api/chains/{uid}').json
    assert history_json['uid'] == uid
    assert len(history_json['nodes']) > 0
    assert len(history_json['edges']) > 0

    knn_node = [node for node in history_json['nodes'] if node['model_name'] == 'knn'][0]
    assert knn_node['type'] == 'model'

    pca_node = [node for node in history_json['nodes'] if node['model_name'] == 'pca_data_model'][0]
    assert pca_node['type'] == 'data_operation'


def test_validate_chain_endpoint(client):
    initial_chain = Chain()
    initial_chain.load_chain(f'{project_root()}/data/mocked_jsons/chain.json')
    graph = chain_to_graph(initial_chain)
    validation_results = client.get(f'api/chains/validate/{json.dumps(graph)}').json
    assert validation_results['is_valid'] is True


def test_add_chain_endpoint(client):
    non_existing_uid = 'new_chain'
    graph = {
        'uid': non_existing_uid,
        'nodes': {}
    }
    response = client.post(f'api/chains/add', json=graph).json
    assert response['is_new'] is True
    assert response['uid'] != non_existing_uid

    existing_uid = 'test_chain'
    graph = {
        'uid': existing_uid,
        'nodes': {}
    }
    response = client.post(f'api/chains/add', json=graph).json
    assert response['is_new'] is False
    assert response['uid'] == existing_uid

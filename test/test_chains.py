import json

from utils import project_root


def test_get_chain_endpoint(client):
    uid = 'test_chain'
    chain_json = client.get(f'api/chains/{uid}').json
    assert chain_json['uid'] == uid
    assert len(chain_json['nodes']) > 0
    assert len(chain_json['edges']) > 0

    knn_node = [node for node in chain_json['nodes'] if node['model_name'] == 'knn'][0]
    assert knn_node['type'] == 'model'

    pca_node = [node for node in chain_json['nodes'] if node['model_name'] == 'pca'][0]
    assert pca_node['type'] == 'data_operation'


def test_validate_chain_endpoint(client):
    with open(f'{project_root()}/test/data/graph_example.json', 'r') as f:
        graph = json.load(f)
    validation_results = client.post('api/chains/validate', json=graph).json
    assert validation_results['is_valid'] is True


def test_add_chain_endpoint(client):
    non_existing_uid = 'new_chain'
    graph = {
        'uid': non_existing_uid,
        'nodes': []
    }
    response = client.post('api/chains/add', json=graph).json
    assert response['is_new'] is True
    assert response['uid'] != non_existing_uid

    existing_uid = 'test_chain'
    graph = {
        'uid': existing_uid,
        'nodes': []
    }
    response = client.post(f'api/chains/add', json=graph).json
    assert response['is_new'] is False
    assert response['uid'] == existing_uid

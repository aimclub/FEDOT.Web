from pathlib import Path

from app.api.chains.chain_convert_utils import chain_to_graph
from app.api.showcase.service import get_image_url
from init.init_chains import chain_mock
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
    chain = chain_mock()
    graph = chain_to_graph(chain)

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
    assert response['uid'] == non_existing_uid

    existing_uid = 'test_chain'
    graph = {
        'uid': existing_uid,
        'nodes': []
    }
    response = client.post(f'api/chains/add', json=graph).json
    assert response['is_new'] is False
    assert response['uid'] == existing_uid


def test_chain_image_endpoint(client):
    uid = 'test_chain'
    response = client.get(f'api/chains/image/{uid}').json
    test_chain = chain_mock()
    filename = f'{uid}.png'
    image_url = get_image_url(filename, test_chain)
    assert Path(f'{project_root()}/app/web/static/generated_images/{filename}').exists()
    assert image_url == response['image_url']

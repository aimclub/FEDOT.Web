def test_get_chain_endpoint(client):
    uid = 'test_chain'
    history_json = client.get(f'api/chains/{uid}').json
    assert history_json['uid'] == uid
    assert len(history_json['nodes']) > 0
    assert len(history_json['edges']) > 0
    # TODO more detailed test


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

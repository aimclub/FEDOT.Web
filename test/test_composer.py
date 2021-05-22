def test_composer_endpoint(client):
    case_id = 'case1'
    history_json = client.get(f'api/composer/{case_id}').json

    assert len(history_json['nodes']) > 0

def test_composer_endpoint(client):
    dataset_name = 'scoring'
    history_json = client.get(f'api/composer/{dataset_name}').json
    assert history_json['dataset_name'] == dataset_name
    assert len(history_json['populations']) > 0
    assert len(history_json['populations']['population_1']['individuals']) > 0
    assert len(history_json['populations']['population_1']
               ['individuals']['ind_1']['objs']) > 0

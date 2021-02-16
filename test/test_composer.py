def test_composer_endpoint(client):
    dataset_name = 'scoring'
    history_json = client.get(f'api/composer/{dataset_name}').json

    assert history_json['dataset_name'] == dataset_name

    populations = history_json['populations']
    assert len(populations) > 0

    individuals_from_population = populations['population_1']['individuals']
    assert len(individuals_from_population) > 0

    objectives_from_individual = individuals_from_population['ind_1']['objs']
    assert len(objectives_from_individual) > 0

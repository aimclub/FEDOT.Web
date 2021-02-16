def test_data_names_endpoint(client):
    datasets_json = client.get(f'api/data/datasets').json
    datasets = [dataset['dataset_name'] for dataset in datasets_json]
    assert 'scoring' in datasets

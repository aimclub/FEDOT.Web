def test_epochs_mapping(client):
    case_id = 'scoring'
    epochs_mapping_json = client.get(f'api/sandbox/epoch/{case_id}').json

    assert epochs_mapping_json[0]['epoch_num'] == 1
    assert epochs_mapping_json[1]['pipeline_id'] is not None
    assert epochs_mapping_json[1]['epoch_num'] == 2


def test_case_params(client):
    case_id = 'scoring'
    case_params_json = client.get(f'api/sandbox/params/{case_id}').json

    assert case_params_json['dataset_name'] == 'scoring'
    assert case_params_json['metric_id'] == 'roc_auc'
    assert case_params_json['task_id'] == 'classification'

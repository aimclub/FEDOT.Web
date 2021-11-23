import json

from app.api.composer.service import run_composer
from app.api.showcase.service import all_showcase_items_ids
from fedot.core.serializers import json_helpers


def test_get_showcase_item_endpoint(client):
    case_id = 'scoring'
    showcase_item_json = client.get(f'api/showcase/items/{case_id}').json

    assert showcase_item_json['case_id'] == case_id
    assert case_id in showcase_item_json['description']
    assert 'png' in showcase_item_json['icon_path']


def test_get_showcase_endpoint(client):
    showcase_json = client.get(f'api/showcase/').json
    ids = [showcase['case_id'] for showcase in showcase_json]
    assert 'scoring' in ids
    assert 'metocean' in ids


def test_add_case_endpoint(client):
    history = run_composer('classification', 'roc_auc', dataset_name='scoring', time=0.01)

    history_json = json.dumps(history, default=json_helpers.encoder)

    existing_ids = all_showcase_items_ids(with_custom=True)
    assert 'new_case' not in existing_ids

    new_case = {
        'case': {
            'case_id': 'new_case',
            'task': 'classification',
            'metric_name': 'roc_auc',
            'dataset_name': 'scoring'
        },
        'history': json.loads(history_json)
    }

    response = client.post('api/showcase/add', json=new_case).json
    assert response is True

    updated_ids = all_showcase_items_ids(with_custom=True)
    assert 'custom_new_case' in updated_ids

import pickle
from pathlib import Path

import pandas as pd

from app.api.data.service import get_datasets_names
from utils import project_root


def test_data_names_endpoint(client):
    datasets_json = client.get(f'api/data/datasets').json
    datasets = [dataset['dataset_name'] for dataset in datasets_json]
    assert 'scoring' in datasets


def test_add_data_endpoint(client):
    data = pd.read_csv(Path(project_root(), 'data', 'scoring', 'scoring_train'))

    data_bytes = str(pickle.dumps(data))

    new_data = {
        'data': {
            'dataset_name': 'new_dataset',
            'data_type': 'table',
            'content_train': data_bytes,
            'content_test': data_bytes
        },
    }

    response = client.post('api/data/add', json=new_data).json
    assert response is True

    updated_ids = get_datasets_names()
    assert 'new_data' in updated_ids

import json
import pickle
from pathlib import Path

import pandas as pd
from fedot.core.serializers import json_helpers

from app.api.composer.service import run_composer
from utils import project_root


def test_new_case_with_new_data(client):
    # add new data
    data = pd.read_csv(Path(project_root(), 'data', 'scoring', 'scoring_train.csv'))

    data_bytes = str(pickle.dumps(data), encoding='latin1')

    new_data = {
        'dataset_name': 'new_dataset',
        'data_type': 'table',
        'content_train': data_bytes,
        'content_test': data_bytes
    }

    response = client.post('api/data/add', json=new_data).json
    assert response is True

    # add new case with new data

    history = run_composer('classification', 'roc_auc', dataset_name='new_dataset', time=0.01)

    history_json = json.dumps(history, default=json_helpers.encoder)

    new_case = {
        'case': {
            'case_id': 'new_case',
            'task': 'classification',
            'metric_name': 'roc_auc',
            'dataset_name': 'new_dataset'
        },
        'history': json.loads(history_json)
    }

    response = client.post('api/showcase/add', json=new_case).json
    assert response is True

    # check pipeline from new case history exists

    uid = str(history.individuals[0][0].graph.uid)
    pipeline_json = client.get(f'api/pipelines/{uid}').json
    assert pipeline_json['uid'] == uid

    # check pipeline from new case history fitted

    results_plot = client.get(f'api/analytics/results/custom_new_case/{uid}').json

    assert len(results_plot['series'][0]['data']) > 0

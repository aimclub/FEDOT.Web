import os
import pickle

import gridfs
import pymongo
from bson import json_util
from fedot.core.pipelines.pipeline import Pipeline
from pymongo.errors import CollectionInvalid

from app.api.composer.service import run_composer
from app.api.data.service import get_input_data
from app.api.pipelines.service import create_pipeline, is_pipeline_exists
from init.init_pipelines import _extract_pipeline_with_fitted_operations
from utils import project_root


def create_default_history(db=None):
    mock_list = []

    _init_composer_history_for_case(db=db, history_id='scoring', dataset_name='scoring',
                                    metric='roc_auc',
                                    task='classification', time=1.5, mock_list=mock_list)

    _init_composer_history_for_case(db=db, history_id='metocean', dataset_name='metocean',
                                    metric='rmse',
                                    task='ts_forecasting', time=0.01, mock_list=mock_list)

    _init_composer_history_for_case(db=db, history_id='oil', dataset_name='oil',
                                    metric='rmse',
                                    task='regression', time=0.7, mock_list=mock_list)

    if len(mock_list) > 0:
        history = [i['history'] for i in mock_list]
        with open(os.path.join(project_root(), 'test/fixtures/history.json'), 'w') as f:
            f.write(json_util.dumps(history))
            print('history are mocked')

        pipelines = [i['pipeline_dict'] for i in mock_list]
        if len(pipelines) > 0:
            with open(os.path.join(project_root(), 'test/fixtures/pipelines.json'), 'r') as f:
                data = json_util.loads(f.read())
                data.extend(pipelines)
            with open(os.path.join(project_root(), 'test/fixtures/pipelines.json'), 'w') as f:
                f.write(json_util.dumps(data))
                print('history pipelines are mocked')

        dict_fitted_operations = [i['dict_fitted_operations'] for i in mock_list]
        if len(dict_fitted_operations) > 0:
            with open(os.path.join(project_root(), 'test/fixtures/dict_fitted_operations.json'), 'r') as f:
                data = json_util.loads(f.read())
                data.extend(pipelines)
            with open(os.path.join(project_root(), 'test/fixtures/dict_fitted_operations.json'), 'w') as f:
                f.write(json_util.dumps(data))
                print('history dict_fitted_operations are mocked')


def _init_composer_history_for_case(db, history_id, task, metric, dataset_name, time, mock_list):
    if db:
        history = run_composer(task, metric, dataset_name, time)
        history_obj = pickle.dumps(history)
        add_to_db(db, history_id, history_obj)
    else:
        history = run_composer(task, metric, dataset_name, 0.1)
        history_obj = {
            'history_id': history_id,
            'history_pkl': pickle.dumps(history)
        }

    data = get_input_data(dataset_name=dataset_name, sample_type='train')
    for i, pipeline_template in enumerate(history.historical_pipelines):
        struct_id = pipeline_template.unique_pipeline_id
        existing_pipeline = False
        if db:
            existing_pipeline = is_pipeline_exists(db, struct_id)
        if not existing_pipeline:
            print(i)
            pipeline = Pipeline()
            pipeline_template.convert_to_pipeline(pipeline)
            pipeline.fit(data)
            if db:
                create_pipeline(db, struct_id, pipeline)
            else:
                pipeline_dict, dict_fitted_operations = _extract_pipeline_with_fitted_operations(pipeline, struct_id)
                mock_list.append({'history': history_obj, 'pipeline_dict': pipeline_dict,
                                  'dict_fitted_operations': dict_fitted_operations})


def add_to_db(db, id_value, obj_to_add):
    fs = gridfs.GridFS(db)
    file = fs.find_one({'filename': id_value, 'type': 'history'})
    if file:
        fs.delete(file._id)
    fs.put(json_util.dumps(obj_to_add), filename=id_value, type='history', encoding='utf-8')

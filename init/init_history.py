import os
import pickle

import gridfs
from bson import json_util
from fedot.core.pipelines.pipeline import Pipeline

from app.api.composer.service import run_composer
from app.api.data.service import get_input_data
from app.api.pipelines.service import create_pipeline, is_pipeline_exists
from init.init_pipelines import _extract_pipeline_with_fitted_operations
from utils import project_root


def create_default_history(db=None, opt_times=None):
    mock_list = []

    if opt_times is None:
        opt_times = [1.5, 0.1, 0.7]

    mock_list.append(
        _init_composer_history_for_case(db=db, history_id='scoring', dataset_name='scoring',
                                        metric='roc_auc',
                                        task='classification', time=opt_times[0]))

    mock_list.append(
        _init_composer_history_for_case(db=db, history_id='metocean', dataset_name='metocean',
                                        metric='rmse',
                                        task='ts_forecasting', time=opt_times[1]))

    mock_list.append(
        _init_composer_history_for_case(db=db, history_id='oil', dataset_name='oil',
                                        metric='rmse',
                                        task='regression', time=opt_times[2]))

    if db is None:
        mockup_history(mock_list)


def mockup_history(mock_list):
    if len(mock_list) > 0:
        history = [i['history'] for i in mock_list]
        with open(os.path.join(project_root(), 'test/fixtures/history.json'), 'w') as f:
            f.write(json_util.dumps(history))
            print('history are mocked')

        pipelines = [j for i in mock_list for j in i['pipelines_dict']]

        if len(pipelines) > 0:
            with open(os.path.join(project_root(), 'test/fixtures/pipelines.json'), 'r+') as f:
                data = json_util.loads(f.read())
                data.extend(pipelines)
                f.seek(0)
                f.write(json_util.dumps(data))
                print('history pipelines are mocked')

        dicts_fitted_operations = [j for i in mock_list for j in i['dicts_fitted_operations']]
        if len(dicts_fitted_operations) > 0:
            with open(os.path.join(project_root(), 'test/fixtures/dict_fitted_operations.json'), 'r+') as f:
                data = json_util.loads(f.read())
                data.extend(dicts_fitted_operations)
                f.seek(0)
                f.write(json_util.dumps(data))
                print('history dict_fitted_operations are mocked')


def _init_composer_history_for_case(db, history_id, task, metric, dataset_name, time):
    mock_dct = {}

    if db:
        history = run_composer(task, metric, dataset_name, time)
        history_obj = pickle.dumps(history)
        add_to_db(db, history_id, history_obj)
    else:
        history = run_composer(task, metric, dataset_name, time)
        history_obj = {
            'history_id': history_id,
            'history_pkl': pickle.dumps(history)
        }

    mock_dct['history'] = history_obj
    mock_dct['pipelines_dict'] = []
    mock_dct['dicts_fitted_operations'] = []

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
                mock_dct['pipelines_dict'].append(pipeline_dict)
                mock_dct['dicts_fitted_operations'].append(dict_fitted_operations)

    return mock_dct


def add_to_db(db, id_value, obj_to_add):
    fs = gridfs.GridFS(db)
    file = fs.find_one({'filename': id_value, 'type': 'history'})
    if file:
        fs.delete(file._id)
    fs.put(json_util.dumps(obj_to_add), filename=id_value, type='history', encoding='utf-8')

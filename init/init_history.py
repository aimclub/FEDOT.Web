import pickle

import gridfs
import pymongo
from bson import json_util
from fedot.core.pipelines.pipeline import Pipeline
from pymongo.errors import CollectionInvalid

from app.api.composer.service import run_composer
from app.api.data.service import get_input_data
from app.api.pipelines.service import create_pipeline, is_pipeline_exists


def create_default_history(db):
    _create_collection(db, 'history', 'history_id')
    _init_composer_history_for_case(db=db, history_id='scoring', dataset_name='scoring',
                                    metric='roc_auc',
                                    task='classification', time=1.5)

    _init_composer_history_for_case(db=db, history_id='metocean', dataset_name='metocean',
                                    metric='rmse',
                                    task='ts_forecasting', time=0.01)

    _init_composer_history_for_case(db=db, history_id='oil', dataset_name='oil',
                                    metric='rmse',
                                    task='regression', time=0.7)


def _create_collection(db, name: str, id_name: str):
    try:
        db.create_collection(name)
        db.history.create_index([(id_name, pymongo.TEXT)], unique=True)
    except CollectionInvalid:
        print('History collection already exists')


def _init_composer_history_for_case(db, history_id, task, metric, dataset_name, time):
    history = run_composer(task, metric, dataset_name, time)
    history_obj = pickle.dumps(history)
    add_to_db(db, history_id, history_obj)

    data = get_input_data(dataset_name=dataset_name, sample_type='train')
    for i, pipeline_template in enumerate(history.historical_pipelines):
        struct_id = pipeline_template.unique_pipeline_id
        existing_pipeline = is_pipeline_exists(db, struct_id)
        if not existing_pipeline:
            print(i)
            pipeline = Pipeline()
            pipeline_template.convert_to_pipeline(pipeline)
            pipeline.fit(data)
            create_pipeline(db, struct_id, pipeline)


def add_to_db(db, id_value, obj_to_add):
    fs = gridfs.GridFS(db)
    file = fs.find_one({'filename': id_value, 'type': 'history'})
    if file:
        fs.delete(file._id)
    fs.put(json_util.dumps(obj_to_add), filename=id_value, type='history', encoding='utf-8')
    # db.history.remove({id_name: id_value})
    # db.history.insert_one(obj_to_add)

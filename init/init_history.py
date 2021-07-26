import pickle

import pymongo
from pymongo.errors import CollectionInvalid

from app.api.composer.service import run_composer


def create_default_history(db):
    _create_collection(db, 'history', 'history_id')
    _init_composer_history_for_case(db=db, history_id='scoring', dataset_name='scoring',
                                    metric='roc_auc',
                                    task='classification')

    _init_composer_history_for_case(db=db, history_id='metocean', dataset_name='metocean',
                                    metric='rmse',
                                    task='ts_forecasting')

    _init_composer_history_for_case(db=db, history_id='oil', dataset_name='oil',
                                    metric='rmse',
                                    task='regression')


def _create_collection(db, name: str, id_name: str):
    try:
        db.create_collection(name)
        db.history.create_index([(id_name, pymongo.TEXT)], unique=True)
    except CollectionInvalid:
        print('History collection already exists')


def _init_composer_history_for_case(db, history_id, task, metric, dataset_name):
    history = run_composer(task, metric, dataset_name)
    history_obj = {
        'history_id': history_id,
        'history_pkl': pickle.dumps(history)
    }
    add_to_db(db, 'history_id', history_id, history_obj)


def add_to_db(db, id_name, id_value, obj_to_add):
    db.history.remove({id_name: id_value})
    db.history.insert_one(obj_to_add)

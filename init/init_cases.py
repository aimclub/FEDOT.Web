import pickle

import pymongo
from pymongo.errors import CollectionInvalid

from app.api.showcase.models import Metadata
from app.api.showcase.models import ShowcaseItem


def create_default_cases(storage):
    _create_collection(storage, 'cases', 'case_id')

    scoring_case = ShowcaseItem(
        case_id='scoring',
        icon_path='./data/scoring/icon.png',
        description=('The purpose of credit scoring is to assess and '
                     'possibly reduce the risk of a bank associated with lending clients. '
                     'Risk minimization happens due to dividing potential borrowers into creditworthy '
                     'and non-creditworthy borrowers. '
                     ' Behavioural scoring involves an assessment of creditworthiness based on information '
                     'about the borrower, characterizing his behaviour and habits and '
                     'obtained from various sources.'),
        chain_id='best_scoring_chain',
        metadata=Metadata(metric_name='roc_auc', task_name='classification', dataset_name='scoring'))

    metocean_case = ShowcaseItem(
        case_id='metocean',
        icon_path='./data/metocean/icon.png',
        description=('Time series processing is widely used in engineering and scientific tasks. '
                     'One of the most common cases with time series is forecasting, '
                     'when we try to predict values in the future based on historical data. '
                     'In this application example, we will demonstrate the capabilities of '
                     'the FEDOT framework '
                     'in time series forecasting'),
        chain_id='best_metocean_chain',
        metadata=Metadata(metric_name='rmse', task_name='ts_forecasting', dataset_name='metocean')
    )

    oil_case = ShowcaseItem(
        case_id='oil',
        icon_path='./data/oil/icon.png',
        description=('The purpose of the experiment was to determine in which case the regression will more '
                     'correctly model oil production -'
                     'sklearn library models or an auto-ml model automatically selected. '
                     'In order to conduct an experiment using the'
                     'framework, we took 13 models to compare the results obtained by each of the '
                     'models and the optimal version built by AutoML.'),
        chain_id='best_oil_chain',
        metadata=Metadata(metric_name='rmse', task_name='regression', dataset_name='oil'))

    _add_case_to_db(storage, scoring_case)
    _add_case_to_db(storage, metocean_case)
    _add_case_to_db(storage, oil_case)

    return


def _create_collection(storage, name: str, id_name: str):
    try:
        storage.db.create_collection(name)
        storage.db.cases.create_index([(id_name, pymongo.TEXT)], unique=True)
    except CollectionInvalid:
        print('Cases collection already exists')


def _add_case_to_db(storage, case):
    case_dict = {
        'case_id': case.case_id,
        'icon_path': case.icon_path,
        'description': case.description,
        'chain_id': case.chain_id,
        'metadata': pickle.dumps(case.metadata)
    }

    _add_to_db(storage, 'case_id', case.case_id, case_dict)


def _add_to_db(storage, id_name, id_value, obj_to_add):
    storage.db.cases.remove({id_name: id_value})
    storage.db.cases.insert_one(obj_to_add)

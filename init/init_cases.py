import pickle

import pymongo
from pymongo.errors import CollectionInvalid

from app.api.showcase.models import Metadata, ShowcaseItem


def create_default_cases(db):
    _create_collection(db, 'cases', 'case_id')

    scoring_case = ShowcaseItem(
        case_id='scoring',
        title='Credit scoring case',
        icon_path=_get_icon_url('scoring_icon.png'),
        description=('The purpose of credit scoring is to assess and '
                     'possibly reduce the risk of a bank associated with lending clients. '
                     'Risk minimization happens due to dividing potential borrowers into creditworthy '
                     'and non-creditworthy borrowers. '
                     ' Behavioural scoring involves an assessment of creditworthiness based on information '
                     'about the borrower, characterizing his behaviour and habits and '
                     'obtained from various sources.'),
        chain_id='best_scoring_chain',
        metadata=Metadata(metric_name='roc_auc', task_name='classification', dataset_name='scoring'), )

    metocean_case = ShowcaseItem(
        case_id='metocean',
        title='Metocean forecasting case',
        icon_path=_get_icon_url('metocean_icon.png'),
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
        title='Oil production prediction',
        icon_path=_get_icon_url('oil_icon.png'),
        description=('The purpose of the experiment was to determine in which case the regression will more '
                     'correctly model oil production -'
                     'sklearn library models or an auto-ml model automatically selected. '
                     'In order to conduct an experiment using the'
                     'framework, we took 13 models to compare the results obtained by each of the '
                     'models and the optimal version built by AutoML.'),
        chain_id='best_oil_chain',
        metadata=Metadata(metric_name='rmse', task_name='regression', dataset_name='oil'))

    add_case_to_db(db, scoring_case)
    add_case_to_db(db, metocean_case)
    add_case_to_db(db, oil_case)

    return


def _create_collection(db, name: str, id_name: str):
    try:
        db.create_collection(name)
        db.cases.create_index([(id_name, pymongo.TEXT)], unique=True)
    except CollectionInvalid:
        print('Cases collection already exists')


def add_case_to_db(db, case):
    case_dict = {
        'case_id': case.case_id,
        'title': case.title,
        'icon_path': case.icon_path,
        'description': case.description,
        'chain_id': case.chain_id,
        'metadata': pickle.dumps(case.metadata),
        'details': case.details
    }

    _add_to_db(db, 'case_id', case.case_id, case_dict)


def _add_to_db(db, id_name, id_value, obj_to_add):
    db.cases.remove({id_name: id_value})
    db.cases.insert_one(obj_to_add)


def _get_icon_url(filename):
    image_path = filename
    return image_path

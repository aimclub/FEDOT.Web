import os
import pickle

from bson import json_util

from app.api.showcase.models import Metadata, ShowcaseItem
from app.singletons.db_service import DBServiceSingleton
from utils import project_root


def create_default_cases():
    db_service = DBServiceSingleton()
    db_service.try_create_collection('cases', 'case_id')

    cases = [
        ShowcaseItem(
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
            individual_id='best_scoring_pipeline',
            metadata=Metadata(metric_name='roc_auc', task_name='classification', dataset_name='scoring')
        ),
        ShowcaseItem(
            case_id='metocean',
            title='Metocean forecasting case',
            icon_path=_get_icon_url('metocean_icon.png'),
            description=('Time series processing is widely used in engineering and scientific tasks. '
                         'One of the most common cases with time series is forecasting, '
                         'when we try to predict values in the future based on historical data. '
                         'In this application example, we will demonstrate the capabilities of '
                         'the FEDOT framework '
                         'in time series forecasting'),
            individual_id='best_metocean_pipeline',
            metadata=Metadata(metric_name='rmse', task_name='ts_forecasting', dataset_name='metocean')
        ),
        ShowcaseItem(
            case_id='oil',
            title='Oil production prediction',
            icon_path=_get_icon_url('oil_icon.png'),
            description=('The purpose of the experiment was to determine in which case the regression will more '
                         'correctly model oil production -'
                         'sklearn library models or an auto-ml model automatically selected. '
                         'In order to conduct an experiment using the'
                         'framework, we took 13 models to compare the results obtained by each of the '
                         'models and the optimal version built by AutoML.'),
            individual_id='best_oil_pipeline',
            metadata=Metadata(metric_name='rmse', task_name='regression', dataset_name='oil')
        )
    ]

    mock_list = [add_case_to_db(case) for case in cases]

    if not db_service.exists():
        mockup_cases(mock_list)


def mockup_cases(mock_list):
    if len(mock_list) > 0:
        with open(os.path.join(project_root(), 'test/fixtures/cases.json'), 'w') as f:
            f.write(json_util.dumps(mock_list))
            print('cases are mocked')


def add_case_to_db(case):
    case_dict = {
        'case_id': case.case_id,
        'title': case.title,
        'icon_path': case.icon_path,
        'description': case.description,
        'individual_id': case.individual_id,
        'metadata': pickle.dumps(case.metadata),
        'details': case.details
    }

    DBServiceSingleton().try_reinsert_one('cases', {'case_id': case.case_id}, case_dict)

    return case_dict


def _get_icon_url(filename):
    image_path = filename
    return image_path

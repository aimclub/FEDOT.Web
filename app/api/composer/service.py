import os
import pickle

from fedot.api.main import Fedot
from fedot.core.composer.composing_history import ComposingHistory
from fedot.core.utils import project_root

from utils import project_root


def composer_history_for_case(case_id: str) -> ComposingHistory:
    # TODO meta with case
    dataset_name = 'scoring'
    metric = 'roc_auc'
    task = 'classification'

    # change to DB request
    saved_history = f'{project_root()}/data/history.pickle'
    if os.path.exists(saved_history):
        with open(saved_history, 'rb') as file:
            history = pickle.load(file)
    else:
        auto_model = Fedot(problem=task, seed=42, learning_time=3,
                           composer_params={'composer_metric': metric})
        auto_model.fit(features=f'{project_root()}/data/{dataset_name}/{dataset_name}_train.csv', target='target')
        history = auto_model.history
        with open(saved_history, 'wb') as file:
            pickle.dump(history, file)

    return history


def run_composing(case_id: str):
    dataset_name = 'scoring'
    metric = 'roc_aus'
    task = 'classification'

    auto_model = Fedot(problem=task, seed=42, learning_time=2,
                       composer_params={'composer_metric': metric})
    auto_model.fit(features=f'{project_root()}/data/{dataset_name}/{dataset_name}_train.csv', target='target')

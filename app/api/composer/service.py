import os
import pickle

from fedot.api.main import Fedot
from fedot.core.composer.composing_history import ComposingHistory

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
        history = run_composer(task, metric, dataset_name)
        with open(saved_history, 'wb') as file:
            pickle.dump(history, file)

    return history


def run_composer(task, metric, dataset_name):
    auto_model = Fedot(problem=task, seed=42, preset='light', verbose_level=4, learning_time=5,
                       composer_params={'composer_metric': metric,
                                        'pop_size': 10,
                                        'num_of_generations': 8,
                                        'max_arity': 3,
                                        'max_depth': 3})
    auto_model.fit(features=f'{project_root()}/data/{dataset_name}/{dataset_name}_train.csv',
                   target='target')
    history = auto_model.history
    return history

import datetime
import itertools
import json
import sys
from functools import lru_cache
from os import PathLike
from pathlib import Path
from typing import Optional

from bson import json_util
from fedot.api.main import Fedot
from fedot.core.pipelines.adapters import PipelineAdapter
from golem.core.optimisers.opt_history_objects.opt_history import OptHistory
from fedot.core.pipelines.pipeline import Pipeline
from fedot.core.pipelines.template import PipelineTemplate
from fedot.core.repository.tasks import TsForecastingParams
from flask import current_app

from app.api.data.service import get_input_data
from app.api.pipelines.service import create_pipeline, is_pipeline_exists
from app.api.showcase.showcase_utils import showcase_item_from_db
from app.singletons.db_service import DBServiceSingleton
from utils import project_root, threading_lock


# @threading_lock
# @lru_cache(maxsize=128) #CHEC
def composer_history_for_case(case_id: str, validate_history: bool = False) -> OptHistory:
    case = showcase_item_from_db(case_id)
    if case is None:
        raise ValueError(f'Showcase item for case_id={case_id} is None but should exist')

    task = case.metadata.task_name
    metric = case.metadata.metric_name
    dataset_name = case.metadata.dataset_name

    saved_history = None

    db_service = DBServiceSingleton()
    if current_app.config['CONFIG_NAME'] == 'test':
        saved_history = db_service.try_find_one('history', {'history_id': case_id})['history_json']
    else:
        file = db_service.try_find_one_file({'filename': case_id, 'type': 'history'})
        if file is not None:
            saved_history = json_util.loads(file.read())
    if not isinstance(saved_history, str):
        saved_history = json.dumps(saved_history)

    history: OptHistory
    if not saved_history:
        history = run_composer(task, metric, dataset_name, time=1.0)
        _save_to_db(case_id, history)
    else:
        print('start_des', datetime.datetime.now())
        history = OptHistory.load(saved_history)
        print('end_des', datetime.datetime.now())

    data = get_input_data(dataset_name=dataset_name, sample_type='train', task_type=task)

    if validate_history:
        # for i, pipeline_template in enumerate(history.historical_pipelines):
        global_id = 0
        adapter = PipelineAdapter()
        historical_pipelines = [
            PipelineTemplate(adapter.restore(ind))
            for ind in itertools.chain(*history.individuals)
        ]

        for pop_id in range(len(history.individuals)):
            pop = history.individuals[pop_id]
            for i, individual in enumerate(pop):
                uid = individual.uid
                existing_pipeline = is_pipeline_exists(uid)
                pipeline_template = historical_pipelines[global_id]
                if not existing_pipeline:
                    print(i)
                    pipeline = Pipeline()
                    pipeline_template.convert_to_pipeline(pipeline)
                    pipeline.fit(data)
                    create_pipeline(uid=uid, pipeline=pipeline, overwrite=True)
                global_id = True

    return history


def _save_to_db(history_id: str, history: OptHistory) -> None:
    history_obj = {
        'history_id': history_id,
        'history_json': history.save()
    }
    DBServiceSingleton().try_reinsert_one('history', {'history_id': history_id}, history_obj)


def run_composer(task: str, metric: str, dataset_name: str, time: float,
                 fitted_history_path: Optional[PathLike] = None,
                 initial_pipeline: Pipeline = None) -> OptHistory:
    checked_hist_path = Path(fitted_history_path) if fitted_history_path is not None else None
    if checked_hist_path is not None:
        if checked_hist_path.exists():
            return OptHistory.load(checked_hist_path.read_text())
        print(f'history_path={checked_hist_path} doesn\'t exist, trying to fit history from FEDOT', file=sys.stderr)
    pop_size = 10
    num_of_generations = 5
    learning_time = time

    composer_params = {'metric': metric,
                       'pop_size': pop_size,
                       'num_of_generations': num_of_generations,
                       'max_arity': 3,
                       'max_depth': 5,
                       'with_tuning': True}

    if time is None:  # test mode
        composer_params = {'metric': metric,
                           'pop_size': 3,
                           'num_of_generations': 2,
                           'max_arity': 2,
                           'max_depth': 2,
                           'with_tuning': False}

        if task == 'ts_forecasting':
            composer_params['available_operations'] = ['lagged', 'ridge', 'linear', 'scaling']
        elif task == 'classification':
            composer_params['available_operations'] = ['logit', 'dt', 'scaling']
        elif task == 'regression':
            composer_params['available_operations'] = ['ridge', 'linear', 'scaling']

        learning_time = -1

    if task == 'ts_forecasting':
        task_parameters = TsForecastingParams(forecast_length=30)
    else:
        task_parameters = None

    preset = 'fast_train'

    auto_model = Fedot(problem=task, seed=42, preset=preset, logging_level=4,
                       timeout=learning_time, task_params=task_parameters, n_jobs=1,
                       initial_assumption=initial_pipeline, **composer_params)
    auto_model.fit(features=f'{project_root()}/data/{dataset_name}/{dataset_name}_train.csv',
                   target='target')
    history: OptHistory = auto_model.history
    return history

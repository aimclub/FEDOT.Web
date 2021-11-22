import pickle

from bson import json_util
from fedot.api.main import Fedot
from fedot.core.optimisers.opt_history import OptHistory
from fedot.core.pipelines.pipeline import Pipeline
from fedot.core.repository.tasks import TsForecastingParams
from flask import current_app

from app.api.data.service import get_input_data
from app.api.pipelines.service import create_pipeline, is_pipeline_exists
from app.api.showcase.showcase_utils import showcase_item_from_db
from app.singletons.db_service import DBServiceSingleton
from utils import project_root


def composer_history_for_case(case_id: str, validate_history: bool = False) -> OptHistory:
    case = showcase_item_from_db(case_id)
    if case is None:
        raise ValueError(f'Showcase item for {case_id=} is None but should exist')

    task = case.metadata.task_name
    metric = case.metadata.metric_name
    dataset_name = case.metadata.dataset_name

    db_service = DBServiceSingleton()
    if current_app.config['CONFIG_NAME'] == 'test':
        saved_history = db_service.try_find_one('history', {'history_id': case_id})
    else:
        file = db_service.try_find_one_file({'filename': case_id, 'type': 'history'})
        if file is not None:
            saved_history = json_util.loads(file.read())

    history: OptHistory
    if not saved_history:
        history = run_composer(task, metric, dataset_name, time=1.0)
        _save_to_db(case_id, history)
    elif current_app.config['CONFIG_NAME'] == 'test':
        history = pickle.loads(saved_history['history_pkl'])
    else:
        history = pickle.loads(saved_history)

    data = get_input_data(dataset_name=dataset_name, sample_type='train')

    if validate_history:
        for i, pipeline_template in enumerate(history.historical_pipelines):
            struct_id = pipeline_template.unique_pipeline_id
            existing_pipeline = is_pipeline_exists(struct_id)
            if not existing_pipeline:
                print(i)
                pipeline = Pipeline()
                pipeline_template.convert_to_pipeline(pipeline)
                pipeline.fit(data)
                create_pipeline(struct_id, pipeline)

    return history


def _save_to_db(history_id: str, history: OptHistory) -> None:
    history_obj = {
        'history_id': history_id,
        'history_pkl': pickle.dumps(history)
    }
    DBServiceSingleton().try_reinsert_one('history', {'history_id': history_id}, history_obj)


def run_composer(task: str, metric: str, dataset_name: str, time: float) -> OptHistory:
    pop_size = 10
    num_of_generations = 5
    learning_time = time

    composer_params = {'composer_metric': metric,
                       'pop_size': pop_size,
                       'num_of_generations': num_of_generations,
                       'max_arity': 3,
                       'max_depth': 5}

    if task == 'ts_forecasting':
        task_parameters = TsForecastingParams(forecast_length=30)
        preset = 'ts_steady_state'
    else:
        task_parameters = None
        preset = 'light_steady_state'

    auto_model = Fedot(problem=task, seed=42, preset=preset, verbose_level=4,
                       timeout=learning_time,
                       composer_params=composer_params, task_params=task_parameters)
    auto_model.fit(features=f'{project_root()}/data/{dataset_name}/{dataset_name}_train.csv',
                   target='target')
    history: OptHistory = auto_model.history
    unfit_history(history)
    return history


def unfit_history(history: OptHistory) -> None:
    for pop in history.individuals:
        for ind in pop:
            ind.graph.link_to_empty_pipeline.unfit()
    for pop in history.archive_history:
        for ind in pop:
            ind.graph.link_to_empty_pipeline.unfit()

    for ops in history.parent_operators:
        for op in ops:
            for op_part in op:
                for pip in op_part.parent_objects:
                    pip.link_to_empty_pipeline.unfit()

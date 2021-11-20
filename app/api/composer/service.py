import json
from os import pipe
from typing import List

from app.api.data.service import get_input_data
from app.api.pipelines.service import create_pipeline, is_pipeline_exists
from app.api.showcase.showcase_utils import showcase_item_from_db
from app.singletons.db_service import DBServiceSingleton
from bson import json_util
from fedot.api.main import Fedot
from fedot.core.optimisers.adapters import PipelineAdapter
from fedot.core.optimisers.gp_comp.individual import Individual
from fedot.core.optimisers.graph import OptGraph
from fedot.core.optimisers.opt_history import OptHistory
from fedot.core.pipelines.pipeline import Pipeline
from fedot.core.pipelines.template import PipelineTemplate
from fedot.core.repository.tasks import TsForecastingParams
from fedot.core.serializers import json_helpers
from flask import current_app
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
        history = json.loads(saved_history['history_json'], object_hook=json_helpers.decoder)
    else:
        history = json.loads(saved_history, object_hook=json_helpers.decoder)

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
        'history_json': json.dumps(history, default=json_helpers.encoder)
    }
    DBServiceSingleton().try_reinsert_one('history', {'history_id': history_id}, history_obj)


def _convert_history_opt_graphs_to_templates(history: OptHistory) -> OptHistory:
    adapter = PipelineAdapter()
    def convert_individuals_opt_graphs_to_templates(individuals: List[Individual]) -> List[PipelineTemplate]:
        for gen in individuals:
            for ind in gen:
                if isinstance(ind.graph, OptGraph):
                    ind.graph = adapter.restore_as_template(ind.graph, ind.computation_time)
        return individuals
    history.individuals = convert_individuals_opt_graphs_to_templates(history.individuals)
    history.archive_history = convert_individuals_opt_graphs_to_templates(history.archive_history)
    return history


def run_composer(task: str, metric: str, dataset_name: str, time: float) -> OptHistory:
    pop_size = 10
    num_of_generations = 5
    learning_time = time
    task_params = None
    if task == 'ts_forecasting':
        task_params = TsForecastingParams(forecast_length=30)

    auto_model = Fedot(problem=task, seed=42, preset='light_steady_state', verbose_level=4,
                       timeout=learning_time,
                       task_params=task_params,
                       composer_params={'composer_metric': metric,
                                        'pop_size': pop_size,
                                        'num_of_generations': num_of_generations,
                                        'max_arity': 3,
                                        'max_depth': 5})
    auto_model.fit(features=f'{project_root()}/data/{dataset_name}/{dataset_name}_train.csv',
                   target='target')
    history: OptHistory = auto_model.history
    pipeline_history = _convert_history_opt_graphs_to_templates(history)
    return pipeline_history

import itertools
import json
import os
from pathlib import Path
from typing import Optional, Union

from bson import json_util
from fedot.core.pipelines.adapters import PipelineAdapter
from golem.core.optimisers.opt_history_objects.individual import Individual
from golem.core.optimisers.opt_history_objects.opt_history import OptHistory
from fedot.core.pipelines.pipeline import Pipeline
from fedot.core.pipelines.template import PipelineTemplate
from fedot.preprocessing.structure import PipelineStructureExplorer
from flask import current_app
from golem.core.optimisers.opt_history_objects.parent_operator import ParentOperator

from app.api.composer.service import run_composer
from app.api.data.service import get_input_data
from app.api.pipelines.service import create_pipeline, is_pipeline_exists
from app.singletons.db_service import DBServiceSingleton
from init.init_pipelines import _extract_pipeline_with_fitted_operations
from utils import project_root


def create_default_history(opt_times=None):
    if opt_times is None:
        opt_times = [None, None, None]

    cases = [
        {
            'history_id': 'scoring', 'dataset_name': 'scoring',
            'metric': 'roc_auc', 'task': 'classification',
            'time': opt_times[0]
        },
        {
            'history_id': 'metocean', 'dataset_name': 'metocean',
            'metric': 'rmse', 'task': 'ts_forecasting',
            'time': opt_times[1]
        },
        {
            'history_id': 'oil', 'dataset_name': 'oil',
            'metric': 'rmse', 'task': 'regression',
            'time': opt_times[2]
        }
    ]

    mock_list = []
    for case in cases:
        candidate_path = Path(f'{project_root()}/data/{case["history_id"]}/{case["history_id"]}_{case["task"]}.json')
        if candidate_path.exists():
            case['external_history'] = candidate_path
        mock_list.append(_init_composer_history_for_case(**case))

    if not DBServiceSingleton().exists():
        mockup_history(mock_list)


def mockup_history(mock_list):
    if len(mock_list) > 0:
        histories = [i['history'] for i in mock_list]
        with open(os.path.join(project_root(), 'test/fixtures/history.json'), 'w') as f:
            for history in histories:
                history['history_json'] = json_util.loads(history['history_json'])
            f.write(json_util.dumps(histories, indent=4))
            print('history is mocked')

        pipelines = [j for i in mock_list for j in i['pipelines_dict'].values()]

        if len(pipelines) > 0:
            with open(os.path.join(project_root(), 'test/fixtures/pipelines.json'), 'r+') as f:
                data = json_util.loads(f.read())
                data.extend(pipelines)
                f.seek(0)
                f.write(json_util.dumps(data, indent=4))
                print('history pipelines are mocked')

        dicts_fitted_operations = [j for i in mock_list for j in i['dicts_fitted_operations']]
        if len(dicts_fitted_operations) > 0:
            with open(os.path.join(project_root(), 'test/fixtures/dict_fitted_operations.json'), 'r+') as f:
                data = json_util.loads(f.read())
                data.extend(dicts_fitted_operations)
                f.seek(0)
                f.write(json_util.dumps(data, indent=4))
                print('history dict_fitted_operations are mocked')


def _save_history_to_path(history: OptHistory, path: Path) -> None:
    if not path.parent.exists():
        path.parent.mkdir()
    path.write_text(history.save())


def get_individual_from_history_by_uid(history: OptHistory, uid: str):
    for generation_index in range(len(history.individuals)):
        generation = history.individuals[generation_index]
        individual: Individual
        for individual in generation:
            if individual.uid == uid:
                return individual, generation_index


def merge_histories(original_history: OptHistory, new_history: OptHistory, modificated_generation_index: int,
                    original_uid: str):
    gens = {}

    mod_gen = modificated_generation_index
    gen_shift = mod_gen + 1

    for generation_index in range(len(new_history.individuals)):
        if generation_index == 0:
            continue
        ind: Individual
        for ind in new_history.individuals[generation_index]:
            if ind.uid in gens:
                pass
            else:
                object.__setattr__(ind, 'native_generation', generation_index + gen_shift)
                gens[ind.uid] = generation_index + gen_shift

    for generation_index in range(len(new_history.individuals)):
        if generation_index + gen_shift >= len(original_history.individuals):
            original_history.individuals.append(new_history.individuals[generation_index])
            original_history.individuals[-1].generation_num = len(original_history.individuals) - 1
        else:
            original_history.individuals[generation_index + gen_shift].generation_num = generation_index + gen_shift
            original_history.individuals[generation_index + gen_shift].extend(new_history.individuals[generation_index])

    parent, real_generation = get_individual_from_history_by_uid(original_history,
                                                                 original_uid)

    child: Individual = new_history.individuals[0][0]
    object.__setattr__(child, 'native_generation', gen_shift)
    object.__setattr__(child, 'parent_operator', ParentOperator('mutation', [], [parent]))
    child.parents.append(parent)
    return original_history


def _init_composer_history_for_case(history_id, task, metric, dataset_name, time,
                                    external_history: Optional[Union[dict, os.PathLike]] = None,
                                    initial_pipeline: Pipeline = None,
                                    original_history: OptHistory = None,
                                    modifed_generation_index=None,
                                    original_uid=None,
                                    is_golem_history=False):
    mock_dct = {}

    db_service = DBServiceSingleton()
    history_path = Path(f'{project_root()}/data/{history_id}/{history_id}_{task}.json')

    is_loaded_history = False
    if external_history is None or not external_history:
        # run composer in real-time
        history = run_composer(task, metric, dataset_name, time,
                               Path(project_root(), 'data', history_id, f'{history_id}_{task}.json'),
                               initial_pipeline=initial_pipeline)
        history_obj = json.loads(history.save())
    elif isinstance(external_history, dict):
        # init from dict
        history_obj = external_history
        history = OptHistory.load(json.dumps(history_obj))
    else:
        # load from path
        history_path = Path(external_history)
        history = run_composer(task, metric, dataset_name, time, history_path, initial_pipeline=initial_pipeline)
        history_obj = history.save()
        is_loaded_history = True

    if not is_loaded_history:
        _save_history_to_path(history, history_path)

    if original_history:
        history = merge_histories(original_history, history, modifed_generation_index, original_uid)
        history_obj = history.save()

    if db_service.exists():
        if current_app and current_app.config['CONFIG_NAME'] == 'test':
            db_service.try_reinsert_one('history', {'history_id': history_id}, history_obj)
        else:
            db_service.try_reinsert_file({'filename': history_id, 'type': 'history'}, history_obj)
    else:
        history_obj = {
            'history_id': history_id,
            'history_json': history_obj
        }

    mock_dct['history'] = history_obj
    mock_dct['pipelines_dict'] = {}
    mock_dct['dicts_fitted_operations'] = []

    data = get_input_data(dataset_name=dataset_name, sample_type='train', task_type=task)

    global_id = 0

    case = db_service.try_find_one('cases', {'case_id': history_id})

    if is_golem_history:
        best_individual = None
        max_fitness = -9999
        for ind in history.final_choices:
            ind: Individual
            fitness = ind.fitness.values[0]  # sp_adj
            if fitness > max_fitness:
                max_fitness = fitness
                best_individual = ind

        if best_individual and case:
            if case is not None:
                case['individual_id'] = best_individual.uid
                db_service.try_reinsert_one('cases', {'case_id': history_id}, case)

        for pop_id in range(len(history.individuals)):
            pop = history.individuals[pop_id]
            for i, individual in enumerate(pop):
                individual: Individual
                is_existing_graph = is_pipeline_exists(individual.uid)
                if not is_existing_graph:
                    if db_service.exists():
                        create_pipeline(uid=individual.uid, pipeline=individual, overwrite=True,
                                        is_graph=is_golem_history)

    if not is_golem_history:
        adapter = PipelineAdapter()
        historical_pipelines = [
            PipelineTemplate(adapter.restore(ind))
            for ind in itertools.chain(*history.individuals)
        ]

        final_choices = history.final_choices
        if final_choices is None:
            final_choices = history.individuals[-1]
        individual = final_choices[0]
        if case is not None:
            case['individual_id'] = individual.uid
            db_service.try_reinsert_one('cases', {'case_id': history_id}, case)

        for pop_id in range(len(history.individuals)):
            pop = history.individuals[pop_id]
            for i, individual in enumerate(pop):
                pipeline_template = historical_pipelines[global_id]
                is_existing_pipeline = is_pipeline_exists(individual.uid)
                if not is_existing_pipeline:
                    print(f'Pipeline №{i} with id {individual.uid} added')
                    pipeline = Pipeline()
                    pipeline_template.convert_to_pipeline(pipeline)
                    if data is not None:
                        pipeline.fit(data)
                    # workaround to reduce size
                    pipeline.preprocessor.structure_analysis = PipelineStructureExplorer()
                    if db_service.exists():
                        create_pipeline(uid=individual.uid, pipeline=pipeline, overwrite=True)
                    else:
                        pipeline_dict, dict_fitted_operations = \
                            _extract_pipeline_with_fitted_operations(pipeline, individual.uid)
                        existing_ids = mock_dct['pipelines_dict'].keys()
                        if individual.uid not in existing_ids:
                            mock_dct['pipelines_dict'][individual.uid] = pipeline_dict
                            mock_dct['dicts_fitted_operations'].append(dict_fitted_operations)
                if not is_pipeline_exists(individual.uid):
                    print(f'Critical error: pipeline for individual {individual.uid} not found after adding')
                global_id += 1

    return mock_dct

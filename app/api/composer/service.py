import pickle

from fedot.api.main import Fedot
from fedot.core.optimisers.opt_history import OptHistory
from fedot.core.pipelines.pipeline import Pipeline

from app import storage
from app.api.pipelines.service import create_pipeline, is_pipeline_exists
from app.api.showcase.models import ShowcaseItem
from app.api.showcase.showcase_utils import prepare_icon_path
from utils import project_root


def showcase_item_from_db(case_id: str) -> ShowcaseItem:
    dumped_item = storage.db.cases.find_one({'case_id': case_id})
    icon_path = prepare_icon_path(dumped_item)
    item = ShowcaseItem(case_id=dumped_item['case_id'],
                        title=dumped_item['title'],
                        icon_path=icon_path,
                        description=dumped_item['description'],
                        pipeline_id=dumped_item['pipeline_id'],
                        metadata=pickle.loads(dumped_item['metadata']))
    return item


def composer_history_for_case(case_id: str) -> OptHistory:
    case = showcase_item_from_db(case_id)
    task = case.metadata.task_name
    metric = case.metadata.metric_name
    dataset_name = case.metadata.dataset_name

    saved_history = storage.db.history.find_one({'history_id': case_id})

    if not saved_history:
        history = run_composer(task, metric, dataset_name)
        _save_to_db(storage.db, case_id, history)
    else:
        history = pickle.loads(saved_history['history_pkl'])

    for i, pipeline_template in enumerate(history.historical_pipelines):
        struct_id = pipeline_template.unique_pipeline_id
        existing_pipeline = is_pipeline_exists(storage.db, struct_id)
        if not existing_pipeline:
            print(i)
            pipeline = Pipeline()
            pipeline_template.convert_to_pipeline(pipeline)
            create_pipeline(storage.db, struct_id, pipeline)

    return history


def _save_to_db(db, history_id, history):
    history_obj = {
        'history_id': history_id,
        'history_pkl': pickle.dumps(history)
    }
    _add_to_db(db, 'history_id', history_id, history_obj)


def run_composer(task, metric, dataset_name):
    pop_size = 6
    num_of_generations = 5
    learning_time = 2

    if dataset_name == 'test':
        pop_size = 6
        num_of_generations = 3
        learning_time = 1

    auto_model = Fedot(problem=task, seed=42, preset='light_steady_state', verbose_level=4,
                       timeout=learning_time,
                       composer_params={'composer_metric': metric,
                                        'pop_size': pop_size,
                                        'num_of_generations': num_of_generations,
                                        'max_arity': 3,
                                        'max_depth': 3})
    auto_model.fit(features=f'{project_root()}/data/{dataset_name}/{dataset_name}_train.csv',
                   target='target')
    history = auto_model.history
    return history


def _add_to_db(db, id_name, id_value, obj_to_add):
    db.history.remove({id_name: id_value})
    db.history.insert_one(obj_to_add)

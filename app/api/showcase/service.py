import pickle
from typing import Any, Dict, List, Optional

from fedot.core.pipelines.pipeline import Pipeline

from app.api.data.service import get_dataset_metadata
from app.api.pipelines.service import get_pipeline_metadata, pipeline_by_uid
from app.singletons.db_service import DBServiceSingleton
from init.init_cases import add_case_to_db

from .models import ShowcaseItem, Metadata
from .showcase_utils import prepare_icon_path, showcase_item_from_db
from ..analytics.pipeline_analytics import get_metrics_for_pipeline


def showcase_full_item_by_uid(case_id: str) -> Optional[ShowcaseItem]:
    dumped_item: Optional[Dict[str, Any]] = DBServiceSingleton().try_find_one('cases', {'case_id': case_id})
    if dumped_item is None:
        return None

    icon_path = prepare_icon_path(dumped_item)

    case_metadata = pickle.loads(dumped_item['metadata'])
    individual_id = dumped_item['individual_id']

    details = dumped_item['details']
    is_updated = False
    if not details and case_metadata.dataset_name is not None:
        n_features, n_rows = get_dataset_metadata(case_metadata.dataset_name, 'train')
        n_models, n_levels = get_pipeline_metadata(individual_id)
        details = {
            'n_models': n_models,
            'n_levels': n_levels,
            'n_features': n_features,
            'n_rows': n_rows}

        case_id = dumped_item['case_id']
        pipeline, case = pipeline_by_uid(individual_id), showcase_item_from_db(case_id)

        if pipeline is None:
            raise ValueError(f'Pipeline with id {individual_id} not exists.')
        if case is None:
            raise ValueError(f'Case with id {case_id} not exists.')

        metrics = get_metrics_for_pipeline(case, pipeline)
        for metric_id, metric_val in metrics.items():
            details[metric_id] = metric_val
        is_updated = True

    item = ShowcaseItem(case_id=case_id,
                        title=dumped_item['title'],
                        icon_path=icon_path,
                        description=dumped_item['description'],
                        individual_id=individual_id,
                        metadata=case_metadata,
                        details=details)
    if is_updated:
        add_case_to_db(case=item)
    return item


def all_showcase_items_ids(with_custom: bool = False) -> List[str]:
    items = DBServiceSingleton().find_all('cases')
    ids = [item['case_id'] for item in items if 'case_id' in item]
    if not with_custom:
        ids = [ind for ind in ids if 'custom_' not in ind]
    return ids


def create_new_case(case_id, case_meta_json, opt_history_json, initial_pipeline: Pipeline = None, original_history=None,
                    modifed_generation_index=None, original_uid=None):
    from init.init_history import _init_composer_history_for_case
    case = ShowcaseItem(
        case_id=case_id,
        title=case_id,
        individual_id=None,
        description=case_id,
        icon_path='',
        details={},
        metadata=Metadata(task_name=case_meta_json.get('task'),
                          metric_name=case_meta_json.get('metric_name'),
                          dataset_name=case_meta_json.get('dataset_name'))
    )

    add_case_to_db(case)

    _init_composer_history_for_case(history_id=case_id,
                                    task=case_meta_json.get('task'),
                                    metric=case_meta_json.get('metric_name'),
                                    dataset_name=case_meta_json.get('dataset_name'),
                                    time=None,
                                    external_history=opt_history_json,
                                    initial_pipeline=initial_pipeline,
                                    original_history=original_history,
                                    modifed_generation_index=modifed_generation_index,
                                    original_uid=original_uid)


async def create_new_case_async(case_id, case_meta_json, opt_history_json, initial_pipeline: Pipeline = None,
                                original_history=None, modifed_generation_index=None, original_uid=None):
    create_new_case(case_id, case_meta_json, opt_history_json, initial_pipeline, original_history=original_history,
                    modifed_generation_index=modifed_generation_index, original_uid=original_uid)
import pickle
from typing import List, Optional

from flask import url_for

from app import storage
from app.api.analytics.service import get_metrics_for_chain
from app.api.chains.service import chain_by_uid, get_chain_metadata
from app.api.data.service import get_dataset_metadata
from .models import ShowcaseItem, ShowcaseItemFull


def showcase_item_by_uid(case_id: str) -> ShowcaseItem:
    dumped_item = storage.db.cases.find_one({'case_id': case_id})
    icon_path = url_for('static', filename=f'cases_icons/{dumped_item["icon_path"]}',
                        _external=True)
    item = ShowcaseItem(case_id=dumped_item['case_id'],
                        title=dumped_item['title'],
                        icon_path=icon_path,
                        description=dumped_item['description'],
                        chain_id=dumped_item['chain_id'],
                        metadata=pickle.loads(dumped_item['metadata']))
    return item


def showcase_full_item_by_uid(case_id: str) -> Optional[ShowcaseItemFull]:
    dumped_item = storage.db.cases.find_one({'case_id': case_id})
    if dumped_item is None:
        return None

    icon_path = url_for('static', filename=f'cases_icons/{dumped_item["icon_path"]}',
                        _external=True)

    case_metadata = pickle.loads(dumped_item['metadata'])
    chain_id = dumped_item['chain_id']
    n_features, n_rows = get_dataset_metadata(case_metadata.dataset_name, 'train')
    n_models, n_levels = get_chain_metadata(chain_id)
    details = {
        'n_models': n_models,
        'n_levels': n_levels,
        'n_features': n_features,
        'n_rows': n_rows}

    case_id = dumped_item['case_id']
    chain, case = chain_by_uid(chain_id), showcase_item_by_uid(case_id)
    metrics = get_metrics_for_chain(case, chain)
    for metric_id in metrics.keys():
        details[metric_id] = metrics[metric_id]
    item = ShowcaseItemFull(case_id=case_id,
                            title=dumped_item['title'],
                            icon_path=icon_path,
                            description=dumped_item['description'],
                            chain_id=chain_id,
                            metadata=case_metadata,
                            details=details)
    return item


def all_showcase_items_ids() -> List[str]:
    items = storage.db.cases.find()
    ids = [item['case_id'] for item in items if 'case_id' in item]
    return ids

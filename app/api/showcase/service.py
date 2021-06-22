import pickle
from typing import List

from flask import url_for

from app import storage
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


def showcase_full_item_by_uid(case_id: str) -> ShowcaseItemFull:
    dumped_item = storage.db.cases.find_one({'case_id': case_id})
    if dumped_item is None:
        return None

    icon_path = url_for('static', filename=f'cases_icons/{dumped_item["icon_path"]}',
                        _external=True)
    item = ShowcaseItemFull(case_id=dumped_item['case_id'],
                            title=dumped_item['title'],
                            icon_path=icon_path,
                            description=dumped_item['description'],
                            chain_id=dumped_item['chain_id'],
                            metadata=pickle.loads(dumped_item['metadata']),
                            metric_name='roc_auc',
                            metric_value=0.85,
                            nmodels=5,
                            nlevels=3,
                            nfeatures=10,
                            n_rows=10000)
    return item


def all_showcase_items_ids() -> List[str]:
    items = storage.db.cases.find()
    ids = [item['case_id'] for item in items if 'case_id' in item]
    return ids

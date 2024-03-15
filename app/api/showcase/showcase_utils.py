import pickle
from typing import Any, Dict, Optional

from app.singletons.db_service import DBServiceSingleton
from flask import url_for

from .models import ShowcaseItem
from ..composer.service import clean_case_id


def showcase_item_from_db(case_id: str) -> Optional[ShowcaseItem]:
    case_id = clean_case_id(case_id)

    dumped_item = DBServiceSingleton().try_find_one('cases', {'case_id': case_id})
    if dumped_item is None:
        return None

    dumped_item['metadata'] = pickle.loads(dumped_item['metadata'])
    dumped_item['icon_path'] = prepare_icon_path(dumped_item)
    item = ShowcaseItem(**{k: v for k, v in dumped_item.items() if k != '_id'})
    return item


def prepare_icon_path(dumped_item: Dict[str, Any]) -> str:
    if 'cases_icons' not in dumped_item['icon_path']:
        icon_path = url_for('static', filename=f'cases_icons/{dumped_item["icon_path"]}')
    else:
        icon_path = dumped_item['icon_path']
    return icon_path

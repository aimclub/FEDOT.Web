import pickle
from typing import Any, Dict, Optional

from app.singletons.db_service import DBServiceSingleton
from flask import url_for

from .models import ShowcaseItem


def showcase_item_from_db(case_id: str) -> Optional[ShowcaseItem]:
    dumped_item: Optional[Dict[str, Any]] = DBServiceSingleton().try_find_one('cases', {'case_id': case_id})
    if dumped_item is None:
        return None

    icon_path = prepare_icon_path(dumped_item)
    item = ShowcaseItem(case_id=dumped_item['case_id'],
                        title=dumped_item['title'],
                        icon_path=icon_path,
                        description=dumped_item['description'],
                        pipeline_id=dumped_item['pipeline_id'],
                        metadata=pickle.loads(dumped_item['metadata']))
    return item


def prepare_icon_path(dumped_item: Dict[str, Any]) -> str:
    if 'cases_icons' not in dumped_item['icon_path']:
        icon_path = url_for('static', filename=f'cases_icons/{dumped_item["icon_path"]}')
    else:
        icon_path = dumped_item['icon_path']
    return icon_path

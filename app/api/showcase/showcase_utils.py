import pickle

from flask import url_for

from app import storage
from .models import ShowcaseItem


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


def prepare_icon_path(dumped_item):
    if 'cases_icons' not in dumped_item["icon_path"]:
        icon_path = url_for('static', filename=f'cases_icons/{dumped_item["icon_path"]}',
                            _external=True)
    else:
        icon_path = dumped_item["icon_path"]
    return icon_path

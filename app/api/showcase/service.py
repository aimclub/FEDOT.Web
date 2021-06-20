import pickle
from pathlib import Path
from typing import List

from flask import url_for

from app import storage
from utils import project_root
from .models import ShowcaseItem


def showcase_item_by_uid(case_id: str) -> ShowcaseItem:
    dumped_item = storage.db.cases.find_one({'case_id': case_id})
    item = ShowcaseItem(case_id=dumped_item['case_id'],
                        icon_path=dumped_item['icon_path'],
                        description=dumped_item['description'],
                        chain_id=dumped_item['chain_id'],
                        metadata=pickle.loads(dumped_item['metadata']))
    return item


def all_showcase_items_ids() -> List[str]:
    items = storage.db.cases.find()
    ids = [item['case_id'] for item in items]
    return ids


def get_image_url(filename, chain):
    image_path = f'{project_root()}/app/web/static/generated_images/{filename}'
    image = Path(image_path)
    if not image.exists():
        dir = Path(f'{project_root()}/app/web/static/generated_images/')
        if not dir.exists():
            dir.mkdir()
        chain.show(image_path)
    return url_for('static', filename=f'generated_images/{filename}', _external=True)

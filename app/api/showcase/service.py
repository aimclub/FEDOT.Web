from typing import List

from pathlib import Path

from utils import project_root
from .models import Metadata, ShowcaseItem

from fedot.core.chains.chain import Chain

from flask import url_for

def showcase_item_by_uid(case_id: str) -> ShowcaseItem:
    metadata = Metadata(metric_name='roc_auc', task_name='classification', dataset_name='scoring')

    image_path = f"app/web/static/generated_images/{case_id}.png"
    image = Path(image_path)
    if not image.exists():
        dir = Path("app/web/static/generated_images/")
        if not dir.exists():
            dir.mkdir()

        saved_chain = Chain()
        saved_chain.load("data/mocked_jsons/chain.json")
        saved_chain.show(image_path)

    item = ShowcaseItem(case_id=case_id,
                        chain_id='ad39eb8c-6050-4734-9e0a-b9884a125a11',
                        description=f'This is a test description of the showcase item {case_id}',
                        icon_path=url_for("static", filename=f"generated_images/{case_id}.png", _external=True),
                        metadata=metadata)
    return item


def all_showcase_items_ids() -> List[str]:
    items = ['item1', 'item2', 'item3', 'item4', 'item5']
    return items

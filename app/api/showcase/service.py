from typing import List

from utils import project_root
from .models import ShowcaseItem


def showcase_item_by_uid(case_id: str) -> ShowcaseItem:
    item = ShowcaseItem(case_id=case_id,
                        chain_id='ad39eb8c-6050-4734-9e0a-b9884a125a11',
                        description=f'This is a test description of the showcase item {case_id}',
                        icon_path=f'{project_root()}/data/mocked_images/showcase.png')
    return item


def all_showcase_items_ids() -> List[str]:
    items = ['item1', 'item2', 'item3', 'item4', 'item5']
    return items

from typing import List

from utils import project_root
from .models import ShowcaseItem


def showcase_item_by_uid(uid: str) -> ShowcaseItem:
    item = ShowcaseItem(uid=uid,
                        description=f'This is a test description of the showcase item {uid}',
                        chain_id='50b86b52-b9f0-42a8-971b-575578879393',
                        icon_path=f'{project_root()}/data/mocked_images/showcase.png')
    return item


def all_showcase_items_ids() -> List[str]:
    items = ['item1', 'item2', 'item3', 'item4', 'item5']
    return items

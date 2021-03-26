from dataclasses import dataclass
from typing import List


@dataclass
class ShowcaseItem:
    uid: str
    description: str
    chain_id: str
    icon_path: str


@dataclass
class Showcase:
    items_uids: List[str]

from dataclasses import dataclass
from typing import List


@dataclass
class ShowcaseItem:
    case_id: str
    chain_id: str
    description: str
    icon_path: str

@dataclass
class Showcase:
    items_uids: List[str]

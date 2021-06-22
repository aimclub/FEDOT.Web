from dataclasses import dataclass
from typing import List


@dataclass
class Metadata:
    task_name: str
    metric_name: str
    dataset_name: str


@dataclass
class ShowcaseItem:
    case_id: str
    title: str
    chain_id: str
    description: str
    icon_path: str
    metadata: Metadata


@dataclass
class Showcase:
    items_uids: List[str]

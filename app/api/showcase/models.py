from dataclasses import dataclass


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
class ShowcaseItemFull:
    case_id: str
    title: str
    chain_id: str
    description: str
    icon_path: str
    metadata: Metadata
    details: dict

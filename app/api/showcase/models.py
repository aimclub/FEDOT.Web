from dataclasses import dataclass, field
from typing import Optional


@dataclass
class Metadata:
    task_name: str
    metric_name: str
    dataset_name: str


@dataclass
class ShowcaseItem:
    case_id: str
    title: str
    individual_id: Optional[str]
    description: str
    icon_path: str
    metadata: Metadata
    details: dict = field(default_factory=lambda: {})

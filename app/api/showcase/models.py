from dataclasses import dataclass, field


@dataclass
class Metadata:
    task_name: str
    metric_name: str
    dataset_name: str


@dataclass
class ShowcaseItem:
    case_id: str
    title: str
    pipeline_id: str
    description: str
    icon_path: str
    metadata: Metadata
    details: dict = field(default_factory=lambda: {})

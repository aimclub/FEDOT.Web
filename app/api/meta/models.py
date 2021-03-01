from dataclasses import dataclass


@dataclass
class TaskInfo:
    task_name: str
    display_name: str


@dataclass
class ModelInfo:
    model_name: str
    display_name: str


@dataclass
class MetricInfo:
    metric_name: str
    display_name: str

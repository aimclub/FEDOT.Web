from dataclasses import dataclass


@dataclass
class PipelineEpochMapping:
    epoch_num: int
    individual_id: str


@dataclass
class SandboxDefaultParams:
    task_id: str
    dataset_name: str
    metric_id: str

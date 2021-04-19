from dataclasses import dataclass


@dataclass
class ChainEpochMapping:
    epoch_num: int
    chain_id: str


@dataclass
class SandboxDefaultParams:
    task_id: str
    dataset_name: str
    metric_id: str

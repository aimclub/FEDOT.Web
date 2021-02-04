from dataclasses import dataclass


@dataclass
class ComposingHistory:
    populations: dict
    dataset_name: str
    task_name: str
    is_finished: bool

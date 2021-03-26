from dataclasses import dataclass


@dataclass
class ComposingHistoryGraph:
    uid: str
    dataset_name: str
    task_name: str
    is_finished: bool
    nodes: list
    edges: list

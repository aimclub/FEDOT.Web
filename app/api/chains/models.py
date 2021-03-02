from dataclasses import dataclass
from typing import List


@dataclass
class Chain:
    uid: str
    nodes: List


@dataclass
class ChainGraph:
    uid: str
    nodes: list
    edges: list


@dataclass
class ChainResponse:
    uid: str
    is_new: bool

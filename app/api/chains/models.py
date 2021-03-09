from dataclasses import dataclass
from typing import List, Optional


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
class ChainValidationResults:
    is_valid: bool
    error_desc: str


@dataclass
class ChainResponse:
    uid: Optional[str]
    is_new: bool

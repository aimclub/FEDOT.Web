from dataclasses import dataclass
from typing import Optional


@dataclass
class ChainGraph:
    uid: str
    nodes: list
    edges: list


@dataclass
class ChainValidationResponse:
    is_valid: bool
    error_desc: str


@dataclass
class ChainResponse:
    uid: Optional[str]
    is_new: bool

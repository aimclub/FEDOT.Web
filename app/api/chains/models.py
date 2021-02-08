from dataclasses import dataclass


@dataclass
class Chain:
    uid: str
    nodes: dict


@dataclass
class ChainResponse:
    uid: str
    is_new: bool

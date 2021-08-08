from dataclasses import dataclass
from typing import Optional


@dataclass
class PipelineGraph:
    uid: str
    nodes: list
    edges: list


@dataclass
class PipelineValidationResponse:
    is_valid: bool
    error_desc: str


@dataclass
class PipelineResponse:
    uid: Optional[str]
    is_new: bool


@dataclass
class PipelineImage:
    uid: str
    image_url: str

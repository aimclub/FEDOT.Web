from dataclasses import dataclass
from typing import List


@dataclass
class PlotData:
    y: List[float]
    x: List[float]
    meta: dict

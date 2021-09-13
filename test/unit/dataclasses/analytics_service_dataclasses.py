from dataclasses import dataclass
from typing import Any, Callable, Dict, List, Optional, Tuple, Union

from ..mocks.analytics_service_mocks import MockPipeline, MockShowcaseItem


@dataclass
class BoxplotChartTestCase:
    x: List[int]
    ys: List[List[Union[int, float]]]
    x_title: str
    y_title: str
    correct_output: List[Dict]


@dataclass
class ChartTestCase:
    x: List[int]
    ys: List[List[Union[int, float]]]
    x_title: str
    y_title: str
    names: List[str]
    plot_type: str
    y_bnd: Optional[Tuple[int, int]]
    correct_series: List[Dict]
    correct_options: Dict


@dataclass
class PopulationAnalyticsTestCase:
    analytic_type: str
    correct_x: List[int]
    correct_y: List[Any]


@dataclass
class PipelinePredictionTestCase:
    showcase: MockShowcaseItem
    pipeline: Optional[MockPipeline]
    target: Union[str, Callable[[Any], Any]]


@dataclass
class ModelResultsTestCase:
    task_name: str
    pipeline: Optional[MockPipeline]
    baseline_pipeline: Optional[MockPipeline]
    correct_x: List[int]
    correct_y: List[Any]

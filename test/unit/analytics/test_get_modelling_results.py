import pytest
from app.api.analytics.service import get_modelling_results
from pandas import Series
from pandas.testing import assert_series_equal

from ..dataclasses.analytics_service_dataclasses import ModelResultsTestCase
from ..fixtures.analytics_service_fixtures import (make_chart_dicts_fixture,
                                                   pipeline_prediction_fixture,
                                                   plot_data_fixture,
                                                   showcase_item_fixture)
from ..mocks.analytics_service_mocks import (MockMetaData, MockPipeline,
                                             MockShowcaseItem)

MODEL_RESULTS_TEST_CASES = [
    ModelResultsTestCase(
        task_name='classification',
        pipeline=None,
        baseline_pipeline=None,
        correct_x=[],
        correct_y=[]
    ),
    ModelResultsTestCase(
        task_name='classification',
        pipeline=None,
        baseline_pipeline=MockPipeline(should_return_baseline=True),
        correct_x=[],
        correct_y=[]
    ),
    ModelResultsTestCase(
        task_name='classification',
        pipeline=MockPipeline(),
        baseline_pipeline=None,
        correct_x=[0, 1, 2, 3, 4, 5],
        correct_y=[[1, 2, 3, 4, 5, 6]]
    ),
    ModelResultsTestCase(
        task_name='classification',
        pipeline=MockPipeline(),
        baseline_pipeline=MockPipeline(should_return_baseline=True),
        correct_x=[0, 1, 2, 3, 4, 5],
        correct_y=[[1, 2, 3, 4, 5, 6], [22, 33, 44, 55, 66, 77]]
    ),

    ModelResultsTestCase(
        task_name='regression',
        pipeline=None,
        baseline_pipeline=None,
        correct_x=[],
        correct_y=[]
    ),
    ModelResultsTestCase(
        task_name='regression',
        pipeline=None,
        baseline_pipeline=MockPipeline(should_return_baseline=True),
        correct_x=[],
        correct_y=[]
    ),
    ModelResultsTestCase(
        task_name='regression',
        pipeline=MockPipeline(),
        baseline_pipeline=None,
        correct_x=[0, 1, 2, 3, 4, 5],
        correct_y=[[1, 2, 3, 4, 5, 6]]
    ),
    ModelResultsTestCase(
        task_name='regression',
        pipeline=MockPipeline(),
        baseline_pipeline=MockPipeline(should_return_baseline=True),
        correct_x=[0, 1, 2, 3, 4, 5],
        correct_y=[[1, 2, 3, 4, 5, 6], [22, 33, 44, 55, 66, 77]]
    ),

    ModelResultsTestCase(
        task_name='ts_forecasting',
        pipeline=None,
        baseline_pipeline=None,
        correct_x=[],
        correct_y=[]
    ),
    ModelResultsTestCase(
        task_name='ts_forecasting',
        pipeline=None,
        baseline_pipeline=MockPipeline(should_return_baseline=True),
        correct_x=[],
        correct_y=[]
    ),
    ModelResultsTestCase(
        task_name='ts_forecasting',
        pipeline=MockPipeline(),
        baseline_pipeline=None,
        correct_x=[0],
        correct_y=[[1, 2, 3, 4, 5, 6]]
    ),
    ModelResultsTestCase(
        task_name='ts_forecasting',
        pipeline=MockPipeline(),
        baseline_pipeline=MockPipeline(should_return_baseline=True),
        correct_x=[0],
        correct_y=[[1, 2, 3, 4, 5, 6], [10, 11, 12, 13, 14, 15]]
    ),

    ModelResultsTestCase(
        task_name='exception',
        pipeline=None,
        baseline_pipeline=None,
        correct_x=[],
        correct_y=[]
    ),
    ModelResultsTestCase(
        task_name='exception',
        pipeline=None,
        baseline_pipeline=MockPipeline(should_return_baseline=True),
        correct_x=[],
        correct_y=[]
    ),
    ModelResultsTestCase(
        task_name='exception',
        pipeline=MockPipeline(),
        baseline_pipeline=None,
        correct_x=[],
        correct_y=[]
    ),
    ModelResultsTestCase(
        task_name='exception',
        pipeline=MockPipeline(),
        baseline_pipeline=MockPipeline(should_return_baseline=True),
        correct_x=[],
        correct_y=[]
    ),
]


@pytest.mark.parametrize('case', MODEL_RESULTS_TEST_CASES)
def test_get_modelling_results(
    case: ModelResultsTestCase,
    plot_data_fixture,
    showcase_item_fixture,
    make_chart_dicts_fixture,
    pipeline_prediction_fixture
):
    showcase = MockShowcaseItem(MockMetaData('', case.task_name))
    if case.task_name == 'exception':
        with pytest.raises(NotImplementedError):
            get_modelling_results(showcase, case.pipeline, case.baseline_pipeline)
    elif case.pipeline is None:
        with pytest.raises(AttributeError):
            get_modelling_results(showcase, case.pipeline, case.baseline_pipeline)
    else:
        x, y = get_modelling_results(showcase, case.pipeline, case.baseline_pipeline)
        assert_series_equal(Series(x), Series(case.correct_x), obj='x')
        assert_series_equal(Series(y), Series(case.correct_y), check_dtype=False, obj='y')

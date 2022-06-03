import pytest
from app.api.analytics.service import get_prediction_for_pipeline

from ..dataclasses.analytics_service_dataclasses import \
    PipelinePredictionTestCase
from ..fixtures.analytics_service_fixtures import (input_output_data_fixture,
                                                   make_chart_dicts_fixture,
                                                   pipeline_fixture,
                                                   showcase_item_fixture)
from ..mocks.analytics_service_mocks import (MockInputData, MockMetaData,
                                             MockOutputData, MockPipeline,
                                             MockShowcaseItem)

PIPELINE_PREDICTION_TEST_CASES = [
    PipelinePredictionTestCase(
        showcase=MockShowcaseItem(MockMetaData(dataset_name=None)),
        pipeline=None,
        target=lambda test_data, prediction: test_data is None and prediction is None
    ),
    PipelinePredictionTestCase(
        showcase=MockShowcaseItem(MockMetaData(dataset_name=None)),
        pipeline=MockPipeline(),
        target=lambda test_data, prediction: test_data is None and prediction is None
    ),
    PipelinePredictionTestCase(
        showcase=MockShowcaseItem(MockMetaData(dataset_name=None)),
        pipeline=MockPipeline(is_fitted=True),
        target=lambda test_data, prediction: test_data is None and prediction is None
    ),
    PipelinePredictionTestCase(
        showcase=MockShowcaseItem(),
        pipeline=None,
        target=lambda test_data, prediction: type(test_data) is MockInputData and prediction is None
    ),
    PipelinePredictionTestCase(
        showcase=MockShowcaseItem(),
        pipeline=MockPipeline(),
        target=lambda test_data, prediction: type(test_data) is MockInputData and type(prediction) is MockOutputData
    ),
    PipelinePredictionTestCase(
        showcase=MockShowcaseItem(),
        pipeline=MockPipeline(is_fitted=True),
        target=lambda test_data, prediction: type(test_data) is MockInputData and type(prediction) is MockOutputData
    ),
]


@pytest.mark.parametrize('case', PIPELINE_PREDICTION_TEST_CASES)
def test_get_prediction_for_pipeline(
    case: PipelinePredictionTestCase,
    pipeline_fixture,
    showcase_item_fixture,
    make_chart_dicts_fixture,
    input_output_data_fixture,
):
    assert case.target(*get_prediction_for_pipeline(case.showcase, case.pipeline))

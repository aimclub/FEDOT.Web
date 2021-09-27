import pytest
from app.api.analytics.service import get_population_analytics
from pandas import Series
from pandas.testing import assert_series_equal

from ..dataclasses.analytics_service_dataclasses import \
    PopulationAnalyticsTestCase
from ..fixtures.analytics_service_fixtures import (
    box_plot_data_fixture, composer_history_for_case_fixture,
    make_chart_dicts_fixture)

POPULATION_ANALYTICS_TEST_CASES = [
    PopulationAnalyticsTestCase(
        analytic_type='pheno',
        correct_x=[0, 1, 2],
        correct_y=[[1.1111, 2.2229999], [3.3366], [5.54321, 6.123456, 10.54346]]
    ),
    PopulationAnalyticsTestCase(
        analytic_type='geno',
        correct_x=[0, 1, 2],
        correct_y=[[1, 4], [9], [25, 36, 100]]
    ),
    PopulationAnalyticsTestCase(
        analytic_type='exception',
        correct_x=[],
        correct_y=[]
    )
]


@pytest.mark.parametrize('case', POPULATION_ANALYTICS_TEST_CASES)
def test_get_population_analytics(
    case: PopulationAnalyticsTestCase,
    box_plot_data_fixture,
    make_chart_dicts_fixture,
    composer_history_for_case_fixture,
):
    if case.analytic_type == 'exception' and not case.correct_x and not case.correct_y:
        with pytest.raises(ValueError):
            get_population_analytics('', case.analytic_type)
    else:
        x, y = get_population_analytics('', case.analytic_type)
        assert x and y, 'MockBoxPlotData is empty'
        assert len(x) == len(y), 'x and y should have the same shape'
        assert_series_equal(Series(x), Series(case.correct_x), obj='x')
        assert_series_equal(Series(y), Series(case.correct_y), check_dtype=False, obj='y')

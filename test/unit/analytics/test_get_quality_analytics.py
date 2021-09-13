from app.api.analytics.service import get_quality_analytics
from pandas import Series
from pandas.testing import assert_series_equal

from ..fixtures.analytics_service_fixtures import (
    composer_history_for_case_fixture, make_chart_dicts_fixture,
    plot_data_fixture)


def test_get_quality_analytics(
    plot_data_fixture,
    composer_history_for_case_fixture,
    make_chart_dicts_fixture
):
    x, y = get_quality_analytics('_')
    y = y[0]
    assert x and y, 'MockPlotData is empty'
    assert len(x) == len(y), 'x and y should have the same shape'
    correct_x = [0, 1, 2]
    assert_series_equal(Series(x), Series(correct_x), obj='x')
    correct_y = [1.111, 3.337, 6.123]
    assert_series_equal(Series(y), Series(correct_y), check_dtype=False, obj='y')

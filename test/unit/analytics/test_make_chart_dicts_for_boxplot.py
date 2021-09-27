import pytest
from app.api.analytics.service import _make_chart_dicts_for_boxplot
from pandas import Series
from pandas.testing import assert_series_equal

from ..dataclasses.analytics_service_dataclasses import BoxplotChartTestCase

BOXPLOT_CHART_TEST_CASES = [
    BoxplotChartTestCase(
        x=[1, 2, 3],
        ys=[
            [1, 2, 3],
            [4, 5, 6],
            [7, 8, 9]
        ],
        x_title='x',
        y_title='y',
        correct_output=[
            {
                'x': [1, 2, 3],
                'y': 'Gen 1',
                'type': 'box',
                'name': 0
            },
            {
                'x': [4, 5, 6],
                'y': 'Gen 2',
                'type': 'box',
                'name': 1
            },
            {
                'x': [7, 8, 9],
                'y': 'Gen 3',
                'type': 'box',
                'name': 2
            }
        ],
    ),
    BoxplotChartTestCase(
        x=[4, 5, 6],
        ys=[
            [1.2, 2.3, 3.4],
            [4.5, 5.6, 6.7],
            [7.8, 8.9, 9.10]
        ],
        x_title='x',
        y_title='y',
        correct_output=[
            {
                'x': [1.2, 2.3, 3.4],
                'y': 'Gen 4',
                'type': 'box',
                'name': 0
            },
            {
                'x': [4.5, 5.6, 6.7],
                'y': 'Gen 5',
                'type': 'box',
                'name': 1
            },
            {
                'x': [7.8, 8.9, 9.10],
                'y': 'Gen 6',
                'type': 'box',
                'name': 2
            }
        ]
    ),
    BoxplotChartTestCase(
        x=[10, 50, 100],
        ys=[
            [0.00199, 0.01999, 0.19999],
            [0.5555, 0, 0],
            [7, 8, 9]
        ],
        x_title='x',
        y_title='y',
        correct_output=[
            {
                'x': [0.002, 0.02, 0.2],
                'y': 'Gen 10',
                'type': 'box',
                'name': 0
            },
            {
                'x': [0.555, 0, 0],
                'y': 'Gen 50',
                'type': 'box',
                'name': 1
            },
            {
                'x': [7, 8, 9],
                'y': 'Gen 100',
                'type': 'box',
                'name': 2
            }
        ],
    )
]


@pytest.mark.parametrize('case', BOXPLOT_CHART_TEST_CASES)
def test_make_chart_dicts_for_boxplot(case: BoxplotChartTestCase):
    result = _make_chart_dicts_for_boxplot(
        x=case.x,
        ys=case.ys,
        x_title=case.x_title,
        y_title=case.y_title
    )
    assert_series_equal(Series(result), Series(case.correct_output), check_dtype=False, obj='chart')

import pytest
from app.api.analytics.service import _make_chart_dicts
from pandas import Series
from pandas.testing import assert_series_equal

from ..dataclasses.analytics_service_dataclasses import ChartTestCase

CHART_TEST_CASES = [
    ChartTestCase(
        x=[1, 2, 3],
        ys=[
            [1, 2, 3],
            [4, 5, 6],
            [7, 8, 9]
        ],
        x_title='x1',
        y_title='y1',
        names=['test1', 'sample1', 'cases1'],
        plot_type='other',
        y_bnd=None,
        correct_series=[
            {
                'name': 'test1',
                'data': [
                    [1, 1],
                    [2, 2],
                    [3, 3]
                ]
            },
            {
                'name': 'sample1',
                'data': [
                    [1, 4],
                    [2, 5],
                    [3, 6]
                ]
            },
            {
                'name': 'cases1',
                'data': [
                    [1, 7],
                    [2, 8],
                    [3, 9]
                ]
            }
        ],
        correct_options={
            'chart': {
                'type': 'other'
            },
            'xaxis': {
                'categories': [1, 2, 3],
                'title': {
                    'text': 'x1'
                }
            },
            'yaxis': {
                'title': {
                    'text': 'y1'
                },
                'min': 0.95,
                'max': 9.45
            }
        }
    ),
    ChartTestCase(
        x=[1, 2, 3, 4],
        ys=[
            [1, 2, 3, 4],
            [5, 6, 7, 8],
            [9, 10, 11, 12]
        ],
        x_title='x2',
        y_title='y2',
        names=['test2', 'sample2', 'cases2'],
        plot_type='line',
        y_bnd=None,
        correct_series=[
            {
                'name': 'test2',
                'data': [1, 2, 3, 4]
            },
            {
                'name': 'sample2',
                'data': [5, 6, 7, 8]
            },
            {
                'name': 'cases2',
                'data': [9, 10, 11, 12]
            }
        ],
        correct_options={
            'chart': {
                'type': 'line'
            },
            'xaxis': {
                'categories': [1, 2, 3, 4],
                'title': {
                    'text': 'x2'
                }
            },
            'yaxis': {
                'title': {
                    'text': 'y2'
                },
                'min': 0.95,
                'max': 12.6
            }
        }
    ),

    ChartTestCase(
        x=[0, 1, 2],
        ys=[
            [1.2, 2.3, 3.4],
            [4.5, 5.6, 6.7],
            [7.8, 8.9, 9.1]
        ],
        x_title='x3',
        y_title='y3',
        names=['test3', 'sample3', 'cases3'],
        plot_type='other',
        y_bnd=(1.14, 9.555),
        correct_series=[
            {
                'name': 'test3',
                'data': [
                    [0, 1.2],
                    [1, 2.3],
                    [2, 3.4]
                ]
            },
            {
                'name': 'sample3',
                'data': [
                    [0, 4.5],
                    [1, 5.6],
                    [2, 6.7]
                ]
            },
            {
                'name': 'cases3',
                'data': [
                    [0, 7.8],
                    [1, 8.9],
                    [2, 9.1]
                ]
            }
        ],
        correct_options={
            'chart': {
                'type': 'other'
            },
            'xaxis': {
                'categories': [0, 1, 2],
                'title': {
                    'text': 'x3'
                }
            },
            'yaxis': {
                'title': {
                    'text': 'y3'
                },
                'min': 1.14,
                'max': 9.555
            }
        }
    ),
    ChartTestCase(
        x=[0, 1, 2],
        ys=[
            [1.2, 2.3, 3.4],
            [4.5, 5.6, 6.7],
            [7.8, 8.9, 9.1]
        ],
        x_title='x4',
        y_title='y4',
        names=['test4', 'sample4', 'cases4'],
        plot_type='line',
        y_bnd=(1.14, 9.555),
        correct_series=[
            {
                'name': 'test4',
                'data': [1.2, 2.3, 3.4]
            },
            {
                'name': 'sample4',
                'data': [4.5, 5.6, 6.7]
            },
            {
                'name': 'cases4',
                'data': [7.8, 8.9, 9.1]
            }
        ],
        correct_options={
            'chart': {
                'type': 'line'
            },
            'xaxis': {
                'categories': [0, 1, 2],
                'title': {
                    'text': 'x4'
                }
            },
            'yaxis': {
                'title': {
                    'text': 'y4'
                },
                'min': 1.14,
                'max': 9.555
            }
        }
    ),

    ChartTestCase(
        x=[10, 50, 100],
        ys=[
            [0.00199, 0.01999, 0.19999],
            [0.5555, 0, 0],
            [7, 8, 9]
        ],
        x_title='x5',
        y_title='y5',
        names=['test5', 'sample5', 'cases5'],
        plot_type='other',
        y_bnd=(0, 9.45),
        correct_series=[
            {
                'name': 'test5',
                'data': [
                    [10, 0.002],
                    [50, 0.02],
                    [100, 0.2]
                ]
            },
            {
                'name': 'sample5',
                'data': [
                    [10, 0.555],
                    [50, 0],
                    [100, 0]
                ]
            },
            {
                'name': 'cases5',
                'data': [
                    [10, 7],
                    [50, 8],
                    [100, 9]
                ]
            }
        ],
        correct_options={
            'chart': {
                'type': 'other'
            },
            'xaxis': {
                'categories': [10, 50, 100],
                'title': {
                    'text': 'x5'
                }
            },
            'yaxis': {
                'title': {
                    'text': 'y5'
                },
                'min': 0,
                'max': 9.45
            }
        }
    ),
    ChartTestCase(
        x=[10, 50, 100],
        ys=[
            [0.00199, 0.01999, 0.19999],
            [0.5555, 0, 0],
            [7, 8, 9]
        ],
        x_title='x6',
        y_title='y6',
        names=['test6', 'sample6', 'cases6'],
        plot_type='line',
        y_bnd=None,
        correct_series=[
            {
                'name': 'test6',
                'data': [0.002, 0.02, 0.2]
            },
            {
                'name': 'sample6',
                'data': [0.555, 0, 0]
            },
            {
                'name': 'cases6',
                'data': [7, 8, 9]
            }
        ],
        correct_options={
            'chart': {
                'type': 'line'
            },
            'xaxis': {
                'categories': [10, 50, 100],
                'title': {
                    'text': 'x6'
                }
            },
            'yaxis': {
                'title': {
                    'text': 'y6'
                },
                'min': 0,
                'max': 9.45
            }
        }
    )
]


@pytest.mark.parametrize('case', CHART_TEST_CASES)
def test_make_chart_dicts(case: ChartTestCase):
    result_series, result_options = _make_chart_dicts(
        x=case.x,
        ys=case.ys,
        names=case.names,
        x_title=case.x_title,
        y_title=case.y_title,
        plot_type=case.plot_type,
        y_bnd=case.y_bnd
    )
    assert_series_equal(Series(result_series), Series(case.correct_series), check_dtype=False, obj='series')
    assert_series_equal(Series(result_options), Series(case.correct_options), check_dtype=False, obj='options')

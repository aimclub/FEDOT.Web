from fedot.core.composer.metrics import MAE, MAPE, RMSE, ROCAUC

from app.api.composer.service import composer_history_for_case
from app.api.data.service import get_input_data
from .models import PlotData

max_items_in_plot = 50
import numpy as np


def _make_chart_dicts_for_boxplot(x, ys, x_title, y_title):
    series = []

    for i in range(len(ys)):
        y = [round(_, 3) for _ in ys[i]]
        series.append({
            'data': {
                'x': x[i],
                'y': y
            }
        })

    options = {
        'chart': {
            'type': 'boxPlot'
        },
        'xaxis': {
            'categories': x,
            'title': {
                'text': x_title
            }
        },
        'yaxis': {
            'title': {
                'text': y_title
            }
        }
    }
    return series, options


def _make_chart_dicts(x, ys, names, x_title, y_title, plot_type, y_bnd=None):
    series = []

    for i in range(len(ys)):
        if plot_type == 'line':
            data = [round(_, 3) for _ in ys[i]]
        else:
            data = [[x[j], round(ys[i][j], 3)] for j in range(len(ys[i]))]

            series.append({
                'name': names[i],
                'data': data
            })

    if not y_bnd:
        min_y = min([min(y) for y in ys]) * 0.95
        max_y = max([max(y) for y in ys]) * 1.05
    else:
        min_y, max_y = y_bnd

    options = {
        'chart': {
            'type': plot_type
        },
        'xaxis': {
            'categories': x,
            'title': {
                'text': x_title
            }
        },
        'yaxis': {
            'title': {
                'text': y_title
            },
            'min': min_y,
            'max': max_y
        }
    }
    return series, options


def get_quality_analytics(case_id) -> PlotData:
    history = composer_history_for_case(case_id)

    y = [round(abs(min([i.fitness for i in gen])), 3) for gen in history.individuals]
    x = list(range(len(history.individuals)))

    series, options = _make_chart_dicts(x=x, ys=[y], names=['Test sample'],
                                        x_title='Epochs', y_title='Fitness',
                                        plot_type='line')

    output = PlotData(series=series, options=options)
    return output


def get_population_analytics(case_id) -> PlotData:
    history = composer_history_for_case(case_id)

    y_gen = [[abs(i.fitness) for i in gen] for gen in history.individuals]
    x = list(range(len(history.individuals)))

    y_quant = []
    for y in y_gen:
        y_quant.append([min(y), np.quantile(y, 0.25), np.quantile(y, 0.5), np.quantile(y, 0.75), max(y)])

    series, options = _make_chart_dicts_for_boxplot(x=x, ys=y_quant,
                                                    x_title='Epochs', y_title='Fitness')

    output = PlotData(series=series, options=options)
    return output


def get_metrics_for_chain(case, chain) -> dict:
    input_data, output_data = _test_prediction_for_chain(case, chain)

    metrics = {}
    if case.metadata.task_name == 'classification':
        input_data.target = input_data.target.astype('int')
        metrics['ROCAUC'] = round(abs(ROCAUC().metric(input_data, output_data)), 3)
    elif case.metadata.task_name == 'regression':
        metrics['RMSE'] = round(abs(RMSE().metric(input_data, output_data)), 3)
        metrics['MAE'] = round(abs(MAE().metric(input_data, output_data)), 3)
    elif case.metadata.task_name == 'ts_forecasting':
        output_data.predict = output_data.predict[0, :len(input_data.target)]
        input_data.target = input_data.target[:len(output_data.predict)]

        metrics['RMSE'] = round(abs(RMSE().metric(input_data, output_data)), 3)
        metrics['MAPE'] = round(abs(MAPE().metric(input_data, output_data)), 3)

    else:
        raise NotImplementedError(f'Task {case.metadata.task_name} not supported')

    return metrics


def _test_prediction_for_chain(case, chain):
    train_data = get_input_data(dataset_name=case.metadata.dataset_name, sample_type='train')

    # if not chain.is_fitted: #TODO something wrong with pre-fitted chains
    chain.fit(train_data)

    test_data = get_input_data(dataset_name=case.metadata.dataset_name, sample_type='test')
    prediction = chain.predict(test_data)
    return test_data, prediction


def get_modelling_results(case, chain, baseline_chain=None) -> PlotData:
    _, prediction = _test_prediction_for_chain(case, chain)
    baseline_prediction = None
    if baseline_chain:
        _, baseline_prediction = _test_prediction_for_chain(case, baseline_chain)
    y_bnd = None
    if case.metadata.task_name == 'classification':
        y_title = 'Probability'
        x_title = 'Item'
        y_bnd = (0, 1)
    elif case.metadata.task_name == 'regression':
        y_title = 'Value'
        x_title = 'Item'
    elif case.metadata.task_name == 'ts_forecasting':
        y_title = 'Value'
        x_title = 'Time step'
    else:
        raise NotImplementedError(f'Task {case.metadata.task_name} not supported')

    if case.metadata.task_name == 'ts_forecasting':
        plot_type = 'line'
        y = list(prediction.predict[0, :])
        y_baseline = list(baseline_prediction.predict[0, :]) if baseline_prediction else None

    else:
        plot_type = 'scatter'
        y = prediction.predict.tolist()
        y_baseline = baseline_prediction.predict.tolist() if baseline_prediction else None

    x = list(range(len(prediction.predict)))
    x = x[:max_items_in_plot]
    y = y[:max_items_in_plot]
    ys = [y]
    names = ['Candidate']
    if baseline_prediction:
        y_baseline = y_baseline[:max_items_in_plot]
        ys.append(y_baseline)
        names.append('Baseline')
    series, options = _make_chart_dicts(x=x, ys=ys, names=names,
                                        x_title=x_title, y_title=y_title,
                                        plot_type=plot_type, y_bnd=y_bnd)

    return PlotData(series, options)

from typing import List

from fedot.core.composer.metrics import MAE, MAPE, RMSE, ROCAUC

from app.api.composer.service import composer_history_for_case
from app.api.data.service import get_input_data
from .models import PlotData

max_items_in_plot = 50


def get_quality_analytics(case_id) -> List[PlotData]:
    history = composer_history_for_case(case_id)

    output = []

    meta = dict()

    meta['y_title'] = 'Fitness'
    meta['x_title'] = 'Epochs'
    meta['name'] = 'Test'
    meta['plot_type'] = 'line'

    y = [min([i.fitness for i in gen]) for gen in history.individuals]
    x = list(range(len(history.individuals)))

    output.append(PlotData(meta=meta, x=x, y=y))

    if case_id == 'test':
        meta['y_title'] = 'ROC AUC'
        meta['x_title'] = 'Epochs'
        meta['name'] = 'Train'
        meta['plot_type'] = 'line'
        y = [0.6, 0.7, 0.75, 0.75, 0.9]
        x = [1, 2, 3, 4, 5]

        output.append(PlotData(meta=meta, x=x[:max_items_in_plot], y=y[:max_items_in_plot]))

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


def get_modelling_results(case, chain) -> List[PlotData]:
    _, prediction = _test_prediction_for_chain(case, chain)

    meta = dict()

    if case.metadata.task_name == 'classification':
        meta['y_title'] = 'Probability'
        meta['x_title'] = 'Item'
    elif case.metadata.task_name == 'regression':
        meta['y_title'] = 'Value'
        meta['x_title'] = 'Item'
    elif case.metadata.task_name == 'ts_forecasting':
        meta['y_title'] = 'Value'
        meta['x_title'] = 'Time step'
    else:
        raise NotImplementedError(f'Task {case.metadata.task_name} not supported')

    if case.metadata.task_name == 'ts_forecasting':
        meta['plot_type'] = 'line'
        y = list(prediction.predict[0, :])

    else:
        meta['plot_type'] = 'scatter'
        y = prediction.predict

    x = list(range(len(prediction.predict)))

    return [PlotData(meta=meta, x=x[:max_items_in_plot], y=y[:max_items_in_plot])]

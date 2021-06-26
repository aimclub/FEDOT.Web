from typing import List

from fedot.core.composer.metrics import ROCAUC

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
    input, output = _test_prediction_for_chain(case, chain)

    metrics = {}
    if case.metadata.task_name == 'classification':
        input.target = input.target.astype('int')
        metrics['ROCAUC'] = abs(ROCAUC().metric(input, output))
        # metrics['F1'] = abs(F1().metric(input, output))

    elif case.metadata.task_name == 'regression':
        pass
    elif case.metadata.task_name == 'ts_forecasting':
        pass
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


def get_modelling_results(case: str, chain: str) -> List[PlotData]:
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
    else:
        meta['plot_type'] = 'scatter'

    y = prediction.predict
    x = list(range(len(prediction.predict)))

    return [PlotData(meta=meta, x=x[:max_items_in_plot], y=y[:max_items_in_plot])]

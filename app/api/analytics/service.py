from typing import List

from fedot.core.data.data import InputData

from app.api.chains.service import chain_by_uid
from app.api.composer.service import composer_history_for_case
from app.api.data.service import get_input_data
from app.api.showcase.service import showcase_item_by_uid
from utils import project_root
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

    if case_id == 'test':
        y = [0.6, 0.7, 0.75, 0.75, 0.9]
        x = [1, 2, 3, 4, 5]

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


def get_modelling_results(case_id: str, chain_id: str) -> List[PlotData]:
    chain = chain_by_uid(chain_id)

    # TODO refactor
    data = InputData.from_csv(f'{project_root()}/data/scoring/scoring_train.csv')
    chain.fit(data)

    case_info = showcase_item_by_uid(case_id)
    data = get_input_data(dataset_name=case_info.metadata.dataset_name, sample_type='test')
    prediction = chain.predict(data)

    meta = dict()

    if case_info.metadata.task_name == 'classification':
        meta['y_title'] = 'Probability'
        meta['x_title'] = 'Item'
    elif case_info.metadata.task_name == 'regression':
        meta['y_title'] = 'Value'
        meta['x_title'] = 'Item'
    elif case_info.metadata.task_name == 'ts_forecasting':
        meta['y_title'] = 'Value'
        meta['x_title'] = 'Time step'
    else:
        raise NotImplementedError(f'Task {case_info.metadata.task_name} not supported')

    if case_info.metadata.task_name == 'ts_forecasting':
        meta['plot_type'] = 'line'
    else:
        meta['plot_type'] = 'scatter'

    y = prediction.predict
    x = list(range(len(prediction.predict)))

    if chain_id == 'test':
        y = [0.03, 0.1, 0.01, 0.5, 0.7, 0.9, 0.12, 0.5]
        x = [1, 2, 3, 4, 5, 6, 7, 8]

    return [PlotData(meta=meta, x=x[:max_items_in_plot], y=y[:max_items_in_plot])]

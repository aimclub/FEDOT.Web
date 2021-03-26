from typing import List

from .models import PlotData


def get_quality_analytics(case_id) -> List[PlotData]:
    output = []

    meta = dict()

    meta['y_title'] = 'ROC AUC'
    meta['x_title'] = 'Epochs'
    meta['name'] = 'Test'
    meta['plot_type'] = 'line'

    y = [0.6, 0.7, 0.75, 0.75, 0.9]
    x = [1, 2, 3, 4, 5]

    output.append(PlotData(meta=meta, x=x, y=y))

    meta['y_title'] = 'ROC AUC'
    meta['x_title'] = 'Epochs'
    meta['name'] = 'Train'
    meta['plot_type'] = 'line'

    y = [0.6, 0.7, 0.75, 0.75, 0.9]
    x = [1, 2, 3, 4, 5]

    output.append(PlotData(meta=meta, x=x, y=y))

    return output


def get_modelling_results(chain_id) -> List[PlotData]:
    meta = dict()

    meta['y_title'] = 'Probability'
    meta['yx_title'] = 'Item'
    meta['plot_type'] = 'scatter'

    y = [0.03, 0.1, 0.01, 0.5, 0.7, 0.9, 0.12, 0.5]
    x = [1, 2, 3, 4, 5, 6, 7, 8]

    return [PlotData(meta=meta, x=x, y=y)]

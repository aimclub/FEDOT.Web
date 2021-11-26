from typing import Dict

from fedot.core.composer.metrics import MAE, MAPE, RMSE, ROCAUC
from fedot.core.pipelines.pipeline import Pipeline

from app.api.analytics.service import get_prediction_for_pipeline
from app.api.showcase.models import ShowcaseItem
from .service import Integral


def get_metrics_for_pipeline(case: ShowcaseItem, pipeline: Pipeline) -> Dict[str, Integral]:
    input_data, output_data = get_prediction_for_pipeline(case, pipeline)

    if input_data is None or output_data is None:
        raise ValueError(f'Input/ouptut data should exist for case={case} and pipeline to score metrics')

    metrics: Dict[str, Integral] = {}
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

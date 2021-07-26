from fedot.core.composer.metrics import ROCAUC, RMSE, MAE, MAPE

from app.api.analytics.service import _test_prediction_for_chain


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

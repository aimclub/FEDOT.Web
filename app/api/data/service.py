import os
from typing import List, Optional, Tuple

from fedot.core.data.data import DataTypesEnum, InputData
from fedot.core.repository.tasks import (Task, TaskTypesEnum,
                                         TsForecastingParams)

from utils import project_root

default_datasets = {
    'scoring': {
        'train': 'scoring/scoring_train.csv',
        'test': 'scoring/scoring_test.csv',
        'task_type': Task(TaskTypesEnum.classification),
        'data_type': DataTypesEnum.table
    },
    'metocean': {
        'train': 'metocean/metocean_train.csv',
        'test': 'metocean/metocean_test.csv',
        'task_type': Task(task_type=TaskTypesEnum.ts_forecasting,
                          task_params=TsForecastingParams(forecast_length=30)),
        'data_type': DataTypesEnum.table
    },
    'oil': {
        'train': 'oil/oil_train.csv',
        'test': 'oil/oil_test.csv',
        'task_type': Task(TaskTypesEnum.regression),
        'data_type': DataTypesEnum.table
    }
}


def get_datasets_names() -> List[str]:
    return list(default_datasets)


def get_dataset_metadata(dataset_name: str, sample_type: str) -> Tuple[int, int]:
    data = get_input_data(dataset_name, sample_type)
    if data is None:
        raise ValueError(f'Data for dataset_name={dataset_name} with sample_type={sample_type} must exists')
    if len(data.features.shape) > 1:
        n_features, n_rows = data.features.shape[1], data.features.shape[0]
    else:
        n_features, n_rows = 1, len(data.features)
    return n_features, n_rows


def get_input_data(dataset_name: str, sample_type: str) -> Optional[InputData]:
    try:
        dataset = default_datasets[dataset_name]
        data_path = dataset[sample_type]

        if dataset['task_type'].task_type == TaskTypesEnum.ts_forecasting:
            data = InputData.from_csv_time_series(file_path=os.path.join(project_root(), 'data', data_path),
                                                  task=dataset['task_type'], target_column='target')
        else:
            data = InputData.from_csv(file_path=os.path.join(project_root(), 'data', data_path),
                                      task=dataset['task_type'],
                                      data_type=dataset['data_type'])
        return data
    except KeyError as ex:
        print(f'Dataset {dataset_name} has no data for {sample_type}: {ex}')
    return None

import os
from typing import List, Optional

from fedot.core.data.data import InputData, DataTypesEnum
from fedot.core.repository.tasks import Task, TaskTypesEnum, TsForecastingParams

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
    return list(default_datasets.keys())


def get_input_data(dataset_name: str, sample_type: str = 'test') -> Optional[InputData]:
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

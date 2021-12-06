import os
from typing import List, Optional, Tuple

from fedot.core.data.data import DataTypesEnum, InputData
from fedot.core.repository.tasks import Task, TsForecastingParams, TaskParams

from app.api.meta.service import task_type_from_id
from utils import project_root

default_datasets = {
    'scoring': {
        'train': 'scoring/scoring_train.csv',
        'test': 'scoring/scoring_test.csv',
        'data_type': DataTypesEnum.table
    },
    'metocean': {
        'train': 'metocean/metocean_train.csv',
        'test': 'metocean/metocean_test.csv',
        'data_type': DataTypesEnum.ts
    },
    'oil': {
        'train': 'oil/oil_train.csv',
        'test': 'oil/oil_test.csv',
        'data_type': DataTypesEnum.table
    }
}

data_types = {
    'ts': DataTypesEnum.ts,
    'table': DataTypesEnum.table,
    'image': DataTypesEnum.image,
    'text': DataTypesEnum.text,
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


def get_input_data(dataset_name: str, sample_type: str,
                   task_type: Optional[str] = None,
                   task_params: Optional[TaskParams] = None) -> Optional[InputData]:
    try:
        dataset = default_datasets[dataset_name]
        data_path = dataset[sample_type]

        if task_params is None and task_type == 'ts_forecasting':
            # forecast_length should be defined
            task_params = TsForecastingParams(forecast_length=30)

        task = Task(task_type_from_id(task_type), task_params) if task_type is not None else None

        if dataset['data_type'] == DataTypesEnum.ts:
            data = InputData.from_csv_time_series(file_path=os.path.join(project_root(), 'data', data_path),
                                                  task=task, target_column='target')
        else:
            data = InputData.from_csv(file_path=os.path.join(project_root(), 'data', data_path),
                                      task=task,
                                      data_type=dataset['data_type'])
        return data
    except KeyError as ex:
        print(f'Dataset {dataset_name} has no data for {sample_type}: {ex}')
    return None

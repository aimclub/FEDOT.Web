import glob
import json
import os
import pickle
from pathlib import Path
from typing import List, Optional, Tuple

from app.api.meta.service import task_type_from_id
from fedot.core.data.data import DataTypesEnum, InputData
from fedot.core.repository.tasks import Task, TaskParams, TsForecastingParams
from utils import project_root

datasets = {
    'scoring': {
        'train': 'data/scoring/scoring_train.csv',
        'test': 'data/scoring/scoring_test.csv',
        'data_type': DataTypesEnum.table
    },
    'metocean': {
        'train': 'data/metocean/metocean_train.csv',
        'test': 'data/metocean/metocean_test.csv',
        'data_type': DataTypesEnum.ts
    },
    'oil': {
        'train': 'data/oil/oil_train.csv',
        'test': 'data/oil/oil_test.csv',
        'data_type': DataTypesEnum.table
    }
}

data_types = {
    'ts': DataTypesEnum.ts,
    'table': DataTypesEnum.table,
    'image': DataTypesEnum.image,
    'text': DataTypesEnum.text,
}


def create_dataset(data_json):
    dataset_name = data_json['dataset_name']

    if dataset_name in get_datasets_names():
        return False

    data_path = Path(project_root(), 'data', dataset_name)
    data_path.mkdir(exist_ok=True)

    train_data, test_data = [
        pickle.loads(bytes(data_json[content_label], encoding='latin1'))
        for content_label in ('content_train', 'content_test')
    ]

    dataset_folder_path = Path(project_root(), 'data', dataset_name)

    train_path, test_path = [
        Path(dataset_folder_path, f'{dataset_name}_{sample_type}.csv')
        for sample_type in ('train', 'test')
    ]

    train_data.to_csv(train_path)
    test_data.to_csv(test_path)

    meta = {
        'train': str(os.path.relpath(train_path, project_root())),
        'test': str(os.path.relpath(test_path, project_root())),
        'data_type': data_json['data_type']
    }

    with open(Path(dataset_folder_path, 'meta.json'), 'w') as f:
        json.dump(meta, f)

    load_datasets_from_file_system()

    return True


def load_datasets_from_file_system():
    datasets_folder_path = Path(project_root(), 'data')
    for file in glob.glob(f'{datasets_folder_path}/*/meta.json', recursive=True):
        name = os.path.basename(os.path.dirname(file))
        with open(file, 'r') as f:
            dataset = json.load(f)
            datasets[name] = dataset
            datasets[name]['data_type'] = data_types[datasets[name]['data_type']]


def get_datasets_names() -> List[str]:
    return list(datasets)


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
        dataset = datasets[dataset_name]
        data_path = dataset[sample_type]

        if task_params is None and task_type == 'ts_forecasting':
            # forecast_length should be defined
            task_params = TsForecastingParams(forecast_length=30)

        task = Task(task_type_from_id(task_type), task_params) if task_type is not None else None

        file_path = Path(project_root(), data_path)

        if dataset['data_type'] == DataTypesEnum.ts:
            data = InputData.from_csv_time_series(file_path=file_path, task=task, target_column='target')
        else:
            data = InputData.from_csv(file_path=file_path, task=task, data_type=dataset['data_type'])
        return data
    except KeyError as ex:
        print(f'Dataset {dataset_name} has no data for {sample_type}: {ex}')
    return None

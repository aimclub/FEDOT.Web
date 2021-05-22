import os
from typing import List, Optional

from fedot.core.data.data import InputData

from utils import project_root

default_datasets = {
    'scoring': {
        'train': 'scoring/scoring_train.csv',
        'test': 'scoring/scoring_test.csv'
    }
}


def get_datasets_names() -> List[str]:
    return list(default_datasets.keys())


def get_input_data(dataset_name: str, sample_type: str = 'test') -> Optional[InputData]:
    try:
        data_path = default_datasets[dataset_name][sample_type]
        data = InputData.from_csv(os.path.join(project_root(), 'data', data_path))
        return data
    except KeyError:
        print(f'Dataset {dataset_name} has no data for {sample_type}')
    return None

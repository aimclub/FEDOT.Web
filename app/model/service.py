from typing import List

from .model import Model


def all_models() -> List[Model]:
    models_sample = [Model(model_id='0', label='xgboost', description='xgboost'),
                     Model(model_id='1', label='KNN', description='KNN')]
    return models_sample

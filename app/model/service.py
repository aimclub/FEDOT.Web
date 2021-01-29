from typing import List

from .model import Model


def all_models() -> List[Model]:
    xgboost = Model(model_id='0', label='xgboost', description='xgboost')
    knn = Model(model_id='1', label='KNN', description='KNN')
    models_sample = [xgboost, knn]
    return models_sample

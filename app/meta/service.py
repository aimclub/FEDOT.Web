from typing import List

from fedot.core.repository.model_types_repository import \
    ModelTypesRepository
from fedot.core.repository.quality_metrics_repository import \
    ClassificationMetricsEnum, \
    ClusteringMetricsEnum, \
    RegressionMetricsEnum
from fedot.core.repository.tasks import TaskTypesEnum

task_dict = {'regression': TaskTypesEnum.regression,
             'classification': TaskTypesEnum.classification,
             'clustering': TaskTypesEnum.clustering,
             'ts_forecasting': TaskTypesEnum.ts_forecasting
             }

metrics_dict = {TaskTypesEnum.regression: RegressionMetricsEnum,
                TaskTypesEnum.classification: ClassificationMetricsEnum,
                TaskTypesEnum.clustering: ClusteringMetricsEnum,
                TaskTypesEnum.ts_forecasting: RegressionMetricsEnum
                }


def get_model_names(task_type: TaskTypesEnum) -> List[str]:
    model_names, _ = ModelTypesRepository().suitable_model(task_type=task_type)
    return model_names


def get_metrics(task_type: TaskTypesEnum) -> List[str]:
    return [m.value for m in metrics_dict[task_type]]


def task_type_from_id(task_type_id: str):
    return task_dict[task_type_id]

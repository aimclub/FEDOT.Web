from typing import List

from fedot.core.repository.operation_types_repository import \
    OperationTypesRepository
from fedot.core.repository.metrics_repository import (
    ClassificationMetricsEnum, ClusteringMetricsEnum, RegressionMetricsEnum)
from fedot.core.repository.tasks import TaskTypesEnum

from .models import MetricInfo, ModelInfo, TaskInfo

_task_dict = {'regression': TaskTypesEnum.regression,
              'classification': TaskTypesEnum.classification,
              'clustering': TaskTypesEnum.clustering,
              'ts_forecasting': TaskTypesEnum.ts_forecasting
              }

_metrics_dict = {TaskTypesEnum.regression: RegressionMetricsEnum,
                 TaskTypesEnum.classification: ClassificationMetricsEnum,
                 TaskTypesEnum.clustering: ClusteringMetricsEnum,
                 TaskTypesEnum.ts_forecasting: RegressionMetricsEnum
                 }


def get_models_info(task_type: TaskTypesEnum) -> List[ModelInfo]:
    model_names = OperationTypesRepository().suitable_operation(task_type=task_type)
    operation_names = OperationTypesRepository(operation_type='data_operation'). \
        suitable_operation(task_type=task_type)

    models = [ModelInfo(name, name, 'model') for name in model_names]
    operations = [ModelInfo(name, name, 'data_operation') for name in operation_names]
    all_info = models + operations
    return all_info


def get_metrics_info(task_type: TaskTypesEnum) -> List[MetricInfo]:
    return [MetricInfo(m.name, m.name) for m in _metrics_dict[task_type]]


def task_type_from_id(task_type_id: str) -> TaskTypesEnum:
    return _task_dict[task_type_id]


def get_tasks_info() -> List[TaskInfo]:
    tasks = [TaskInfo(task_name, task_name) for task_name in _task_dict]
    return tasks

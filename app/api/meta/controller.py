from typing import List

from flask_accepts import responds
from flask_restx import Namespace, Resource

from .models import MetricInfo, ModelInfo, TaskInfo
from .schema import MetricInfoSchema, ModelInfoSchema, TaskInfoSchema
from .service import (get_metrics_info, get_models_info, get_tasks_info,
                      task_type_from_id)

api = Namespace("Meta", description="Operations with metadata")


@api.route("/tasks")
class MetaTaskResource(Resource):
    """Meta for tasks"""

    @responds(schema=TaskInfoSchema, many=True)
    def get(self) -> List[TaskInfo]:
        """Get all tasks from metadata"""
        tasks_info = get_tasks_info()
        return tasks_info


@api.route("/models/<string:task_name>")
@api.param('task_name', 'ID of task that should be supported by models')
class MetaModelsResource(Resource):
    """Metadata for models"""

    @responds(schema=ModelInfoSchema, many=True)
    def get(self, task_name: str) -> List[ModelInfo]:
        """Get all model names from metadata"""
        task = task_type_from_id(task_name)
        models_info = get_models_info(task)
        return models_info


@api.route("/metrics/<string:task_name>")
@api.param('task_name', 'ID of task that should be supported by metrics')
class MetaMetricsResource(Resource):
    """Metadata for composing metrics"""

    @responds(schema=MetricInfoSchema, many=True)
    def get(self, task_name: str) -> List[MetricInfo]:
        """Get all model names from metadata"""
        task = task_type_from_id(task_name)
        metric_info = get_metrics_info(task)
        return metric_info

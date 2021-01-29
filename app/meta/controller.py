from typing import List

from flask_accepts import responds
from flask_restx import Namespace, Resource

from .entities import ModelName, Task
from .schema import ModelNameSchema, TaskSchema
from .service import get_model_names, task_dict, task_type_from_id

api = Namespace("Meta", description="Operations with metadata")


@api.route("/tasks")
class MetaTaskResource(Resource):
    """Meta for tasks"""

    @responds(schema=TaskSchema, many=True)
    def get(self) -> List[Task]:
        """Get all tasks from metadata"""
        tasks = [Task(task_name) for task_name in list(task_dict.keys())]
        return tasks


@api.route("/models/<string:task_id>")
@api.param('task_id', 'ID of task that should be supported by models')
class MetaModelsResource(Resource):
    """Meta for models"""

    @responds(schema=ModelNameSchema, many=True)
    def get(self, task_id) -> List[ModelName]:
        """Get all model names from metadata"""
        task = task_type_from_id(task_id)
        model_names = [ModelName(_) for _ in get_model_names(task)]
        return model_names

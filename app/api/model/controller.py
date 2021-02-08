from typing import List

from flask import request
from flask_accepts import responds, accepts
from flask_restx import Namespace, Resource

from .model import Model
from .schema import ModelSchema
from .service import all_models

api = Namespace("Model", description="Operations with models")


@api.route("/")
class ModelResource(Resource):
    """Models"""

    @responds(schema=ModelSchema, many=True)
    def get(self) -> List[Model]:
        """Get all models"""
        models = all_models()
        return models

    @accepts(schema=ModelSchema, api=api)
    @responds(schema=ModelSchema)
    def post(self) -> Model:
        """Create a single Model"""

        obtained = request.parsed_obj
        print(obtained)
        return obtained

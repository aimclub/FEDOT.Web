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

    @responds(schema=ModelSchema)
    def get_all_models(self) -> List[Model]:
        """Get all models"""
        models = all_models()
        return models

    @accepts(schema=ModelSchema, api=api)
    @responds(schema=ModelSchema)
    def post(self) -> Model:
        """Create a Single Widget"""

        obtained = request.parsed_obj
        print(obtained)
        return obtained

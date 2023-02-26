from typing import List

from flask import request
from flask_accepts import accepts, responds
from flask_cors import cross_origin
from flask_restx import Namespace, Resource

from .models import Dataset
from .schema import DatasetAddingScheme, DatasetSchema
from .service import get_datasets_names, create_dataset

api = Namespace("Data", description="Operations with experiments data")


@api.route("/datasets")
class DataSetsResource(Resource):
    """Datasets"""

    @responds(schema=DatasetSchema, many=True)
    def get(self) -> List[Dataset]:
        """Get list of all datasets names"""
        dataset_name = get_datasets_names()

        return [Dataset(_) for _ in dataset_name]


@cross_origin()
@api.route("/add", methods=['POST', 'OPTIONS'])
class DatasetAddResource(Resource):
    """Add custom dataset"""

    @accepts(schema=DatasetAddingScheme, api=api)
    def post(self) -> bool:
        """Add dataset with specific name"""
        data_json = request.parsed_obj
        return create_dataset(data_json)

    def options(self):
        return True

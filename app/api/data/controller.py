from typing import List

from flask_accepts import responds
from flask_restx import Namespace, Resource

from .models import Dataset
from .schema import DatasetSchema
from .service import get_datasets_names

api = Namespace("Data", description="Operations with experiments data")


@api.route("/datasets")
class DataSetsResource(Resource):
    """Datasets"""

    @responds(schema=DatasetSchema, many=True)
    def get(self) -> List[Dataset]:
        """Get list of all datasets names"""
        dataset_name = get_datasets_names()

        return [Dataset(_) for _ in dataset_name]

from typing import List

from flask_accepts import responds
from flask_restx import Namespace, Resource

from .models import Dataset
from .schema import DatasetSchema
from .service import get_datasets

api = Namespace("Data", description="Operations with experiments data")


@api.route("/datasets")
class DataSetsResource(Resource):
    """Datasets"""

    @responds(schema=DatasetSchema, many=True)
    def get(self) -> List[Dataset]:
        """Get chain for specific dataset"""
        dataset_name = get_datasets()

        return [Dataset(_) for _ in dataset_name]

import pickle
from pathlib import Path
from typing import List

from flask import request
from flask_accepts import accepts, responds
from flask_cors import cross_origin
from flask_restx import Namespace, Resource

from utils import project_root
from .models import Dataset
from .schema import DatasetAddingScheme, DatasetSchema
from .service import data_types, default_datasets, get_datasets_names

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

        dataset_name = data_json['dataset_name']
        data_type = data_types[data_json['data_type']]

        if dataset_name in get_datasets_names():
            return False

        data_path = Path(project_root(), 'data', dataset_name)
        data_path.mkdir(exist_ok=True)

        train_data, test_data = [
            pickle.loads(data_json[content_label], encoding='latin1')
            for content_label in ('content_train', 'content_test')
        ]

        train_path, test_path = [
            Path(project_root(), 'data', dataset_name, f'{dataset_name}_{sample_type}.csv')
            for sample_type in ('train', 'test')
        ]

        train_data.to_csv(train_path)
        test_data.to_csv(test_path)

        # TODO refactor - move to database
        default_datasets[dataset_name] = {
            'train': str(train_path),
            'test': str(test_path),
            'data_type': data_type
        }

        return True

    def options(self):
        return True

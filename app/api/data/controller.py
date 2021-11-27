import os
import pickle
from pathlib import Path
from typing import List

from flask import request
from flask_accepts import accepts, responds
from flask_cors import cross_origin
from flask_restx import Namespace, Resource

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

        data_path = Path(dataset_name)
        if not data_path.exists():
            os.mkdir(data_path)

        train_data = pickle.loads(data_json['content_train'])
        test_data = pickle.loads(data_json['content_test'])

        train_path = Path(dataset_name, f'{dataset_name}_train.csv')
        test_path = Path(dataset_name, f'{dataset_name}_train.csv')

        train_data.to_csv()
        test_data.to_csv(Path(dataset_name, f'{dataset_name}_test.csv'))

        # TODO refactor
        default_datasets[dataset_name] = {
            'train': str(train_path),
            'test': str(test_path),
            'data_type': data_type
        }

        return True

    def options(self):
        return True

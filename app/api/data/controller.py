import json
import os.path
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
from .service import data_types, datasets, get_datasets_names

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

        if dataset_name in get_datasets_names():
            return False

        data_path = Path(project_root(), 'data', dataset_name)
        data_path.mkdir(exist_ok=True)

        train_data, test_data = [
            pickle.loads(bytes(data_json[content_label], encoding='latin1'))
            for content_label in ('content_train', 'content_test')
        ]

        dataset_folder_path = Path(project_root(), 'data', dataset_name)

        train_path, test_path = [
            Path(dataset_folder_path, f'{dataset_name}_{sample_type}.csv')
            for sample_type in ('train', 'test')
        ]

        train_data.to_csv(train_path)
        test_data.to_csv(test_path)

        meta = {
            'train': str(os.path.relpath(train_path, project_root())),
            'test': str(os.path.relpath(test_path, project_root())),
            'data_type': data_json['data_type']
        }

        with open(Path(dataset_folder_path, 'meta.json'), 'w') as f:
            json.dump(meta, f)

        return True

    def options(self):
        return True

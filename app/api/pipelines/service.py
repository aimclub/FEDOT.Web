import json
import warnings
from io import BytesIO
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import pymongo
from bson import json_util
from fedot.core.pipelines.pipeline import Pipeline
from fedot.core.pipelines.verification import verify_pipeline as verify
from flask import current_app, has_app_context, url_for
from pymongo.errors import DuplicateKeyError

from app.singletons.db_service import DBServiceSingleton
from utils import project_root


def is_pipeline_exists(uid: str) -> bool:
    return DBServiceSingleton().try_find_one('pipelines', {'individual_id': uid}) is not None


def pipeline_by_uid(uid: str) -> Optional[Pipeline]:
    db_service = DBServiceSingleton()
    pipeline = Pipeline()
    pipeline_dict: Optional[Dict[str, Any]] = db_service.try_find_one('pipelines', {'individual_id': uid})
    if pipeline_dict is None:
        return None

    dict_fitted_operations: Optional[Dict[str, Any]] = None
    if current_app.config['CONFIG_NAME'] == 'test':
        dict_fitted_operations = db_service.try_find_one('dict_fitted_operations', {'individual_id': uid})
    else:
        file = db_service.try_find_one_file({'filename': str(uid), 'type': 'dict_fitted_operations'})
        if file is not None:
            dict_fitted_operations = json_util.loads(file.read())

    if dict_fitted_operations:
        dict_fitted_operations = {key: BytesIO(operation) for key, operation in dict_fitted_operations.items()
                                  if key not in ['individual_id', '_id']}
    pipeline.load(pipeline_dict, dict_fitted_operations)
    return pipeline


def verify_pipeline(pipeline: Pipeline) -> Tuple[bool, str]:
    try:
        verify(pipeline)
        return True, 'Correct pipeline'
    except ValueError as ex:
        return False, str(ex)


def create_pipeline(uid: str, pipeline: Pipeline, overwrite: bool = False) -> Tuple[str, bool]:
    is_new = True
    existing_uid = is_pipeline_exists(uid)
    if existing_uid and not overwrite:
        is_new = False

    dumped_json, dict_fitted_operations = pipeline.save()
    if dict_fitted_operations:
        for key in dict_fitted_operations:
            if key.find('operation') != -1 or key == 'preprocessing':
                dict_fitted_operations[key].seek(0)
                saved_operation = dict_fitted_operations[key].read()
                dict_fitted_operations[key] = saved_operation
        dict_fitted_operations['individual_id'] = str(uid)

    if is_new:
        dict_pipeline = json.loads(dumped_json)
        _add_pipeline_to_db(uid, dict_pipeline, dict_fitted_operations, overwrite=overwrite)
    else:
        warnings.warn('Cannot create new pipeline')

    return uid, is_new


def _add_pipeline_to_db(
    uid: str, dict_pipeline: Dict, dict_fitted_operations: Dict,
    init_db: bool = False, overwrite: bool = False
) -> Optional[List[Dict]]:
    uid = uid
    dict_pipeline['individual_id'] = uid
    db_service = DBServiceSingleton()
    db_service.try_reinsert_one('pipelines', {'individual_id': uid}, dict_pipeline)

    if dict_fitted_operations is not None:
        try:
            if has_app_context() and current_app.config['CONFIG_NAME'] == 'test':
                dict_fitted_operations = db_service.try_find_one('dict_fitted_operations', {'individual_id': uid})
            else:
                db_service.try_reinsert_file(
                    {'filename': uid, 'type': 'dict_fitted_operations'}, dict_fitted_operations
                )

            if init_db:
                return [dict_pipeline, dict_fitted_operations]

        except DuplicateKeyError:
            print(f'Fitted operations dict {str(uid)} already exists')
        except pymongo.errors.DocumentTooLarge as ex:
            print(f'Dict {str(uid)} too large: {ex}')
    return None


def get_image_url(filename: str, pipeline: Optional[Pipeline]) -> str:
    image_path = f'{project_root()}/frontend/build/static/generated_images/{filename}'
    image = Path(image_path)
    if not image.exists():
        dir_path = Path(f'{project_root()}/frontend/build/static/generated_images/')
        if not dir_path.exists():
            dir_path.mkdir()
        if pipeline is not None:
            pipeline.show(image_path)
    return url_for('static', filename=f'generated_images/{filename}')


def get_pipeline_metadata(individual_id: str) -> Tuple[int, int]:
    pipeline = pipeline_by_uid(individual_id)
    if not pipeline:
        return -1, -1
    return pipeline.length, pipeline.depth

import json
import warnings
from io import BytesIO
from pathlib import Path
from typing import Optional, Tuple

from fedot.core.pipelines.pipeline import Pipeline
from fedot.core.pipelines.validation import validate
from flask import url_for
from pymongo.errors import DuplicateKeyError

from app import storage
from utils import project_root


def is_pipeline_exists(db, uid: str) -> Optional[Pipeline]:
    pipeline_dict = db.pipelines.find_one({'uid': str(uid)})
    return pipeline_dict is not None


def pipeline_by_uid(uid: str) -> Optional[Pipeline]:
    pipeline = Pipeline()
    pipeline_dict = storage.db.pipelines.find_one({'uid': str(uid)})
    if pipeline_dict is None:
        return None

    dict_fitted_operations = storage.db.dict_fitted_operations.find_one({'uid': str(uid)})
    if dict_fitted_operations:
        _replace_symbols_in_dct_keys(dict_fitted_operations, "-", ".")
        for key in dict_fitted_operations:
            if key.find("fitted") != -1:
                bytes_container = BytesIO()
                bytes_container.write(dict_fitted_operations[key])
                dict_fitted_operations[key] = bytes_container
    pipeline.load(pipeline_dict, dict_fitted_operations)
    return pipeline


def validate_pipeline(pipeline: Pipeline) -> Tuple[bool, str]:
    try:
        validate(pipeline)
        return True, 'Correct pipeline'
    except ValueError as ex:
        return False, str(ex)


def create_pipeline(db, uid: str, pipeline: Pipeline):
    is_new = True
    existing_uid = db.pipelines.find_one({'uid': str(uid)})
    if existing_uid:
        is_new = False

    is_duplicate = False
    dumped_json, dict_fitted_operations = pipeline.save()

    # if len(pipeline.nodes) > 0 and \
    #        storage.db.pipelines.find_one({'descriptive_id': pipeline.root_node.descriptive_id}):
    #    is_duplicate = True

    if is_new:
        dict_pipeline = json.loads(dumped_json)
        dict_pipeline['uid'] = str(uid)
        try:
            db.pipelines.insert_one(dict_pipeline)
        except DuplicateKeyError:
            print(f'Pipeline {str(uid)} already exists')
    else:
        warnings.warn('Cannot create new pipeline')

    return uid, is_new


def get_image_url(filename, pipeline):
    image_path = f'{project_root()}/app/web/static/generated_images/{filename}'
    image = Path(image_path)
    if not image.exists():
        dir_path = Path(f'{project_root()}/app/web/static/generated_images/')
        if not dir_path.exists():
            dir_path.mkdir()
        pipeline.show(image_path)
    return url_for('static', filename=f'generated_images/{filename}', _external=True)


def get_pipeline_metadata(pipeline_id) -> Tuple[int, int]:
    pipeline = pipeline_by_uid(pipeline_id)
    if not pipeline:
        return -1, -1
    return pipeline.length, pipeline.depth


def _replace_symbols_in_dct_keys(dct, old, new_symb):
    for key in list(dct.keys()):
        new_key = key.replace(old, new_symb)
        dct[new_key] = dct.pop(key)
    return dct

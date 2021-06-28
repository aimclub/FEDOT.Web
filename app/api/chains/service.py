import json
import warnings
from pathlib import Path
from typing import Optional, Tuple

from fedot.core.chains.chain import Chain
from fedot.core.chains.chain_validation import validate
from flask import url_for

from app import storage
from utils import project_root


def chain_by_uid(uid: str) -> Optional[Chain]:
    chain = Chain()
    chain_dict = storage.db.chains.find_one({'uid': uid})
    if chain_dict is None:
        # TODO temporary workaround
        chain_dict = storage.db.chains.find_one({'uid': 'best_scoring_chain'})

    dict_fitted_operations = storage.db.dict_fitted_operations.find_one({'uid': uid})
    chain.load(chain_dict, dict_fitted_operations)
    return chain


def validate_chain(chain: Chain) -> Tuple[bool, str]:
    try:
        validate(chain)
        return True, 'Correct chain'
    except ValueError as ex:
        return False, str(ex)


def create_chain(uid: str, chain: Chain):
    is_new = True
    existing_uid = storage.db.chains.find_one({'uid': uid})
    if existing_uid:
        is_new = False

    is_duplicate = False
    dumped_json = chain.save('tumped_tmp')

    if len(chain.nodes) > 0 and \
            storage.db.chains.find_one({'descriptive_id': chain.root_node.descriptive_id}):
        is_duplicate = True

    if is_new and not is_duplicate:
        dict_chain = json.loads(dumped_json)
        dict_chain['uid'] = uid
        storage.db.chains.insert_one(dict_chain)
    else:
        warnings.warn('Cannot create new chain')

    return uid, is_new


def get_image_url(filename, chain):
    image_path = f'{project_root()}/app/web/static/generated_images/{filename}'
    image = Path(image_path)
    if not image.exists():
        dir_path = Path(f'{project_root()}/app/web/static/generated_images/')
        if not dir_path.exists():
            dir_path.mkdir()
        chain.show(image_path)
    return url_for('static', filename=f'generated_images/{filename}', _external=True)


def get_chain_metadata(chain_id) -> Tuple[int, int]:
    chain = chain_by_uid(chain_id)
    if not chain:
        return -1, -1
    return chain.length, chain.depth

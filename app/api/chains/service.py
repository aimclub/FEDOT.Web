import json
import warnings
from typing import Tuple

from fedot.core.chains.chain import Chain
from fedot.core.chains.chain_validation import validate

from app import storage


def chain_by_uid(uid: str) -> Chain:
    chain = Chain()
    chain_dict = storage.db.chains.find_one({'uid': uid})
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
    dumped_json = chain.save()

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

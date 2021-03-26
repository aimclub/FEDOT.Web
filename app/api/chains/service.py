import warnings
from typing import Tuple

from fedot.core.chains.chain import Chain
from fedot.core.chains.chain_validation import validate

from utils import project_root


def chain_by_uid(uid: str) -> Chain:
    chain = Chain()
    chain.load(f'{project_root()}/data/mocked_jsons/chain.json')
    return chain


def validate_chain(chain: Chain) -> Tuple[bool, str]:
    try:
        validate(chain)
        return True, 'Correct chain'
    except ValueError as ex:
        return False, str(ex)


def create_chain(uid: str, chain: Chain):
    # TODO search chain with same structure and data in database
    existing_uid = 'test_chain'
    is_new = uid != existing_uid

    if is_new:
        # TODO save chain to database
        warnings.warn('Cannot create new chain')
        uid = 'new_uid'

    return uid, is_new

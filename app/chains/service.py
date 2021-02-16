import json
import warnings

from utils import project_root


def chain_by_uid(uid: str) -> dict:
    chain_json = None
    with open(f'{project_root()}/data/mocked_jsons/chain.json') as f:
        chain_json = json.load(f)
        chain_json['uid'] = uid

    return chain_json


def create_chain_from_graph(graph: dict):
    # TODO convert graph to Chain

    # TODO search chain with same structure and data in database
    is_new = True

    existing_uid = 'test_chain'
    if graph['uid'] == existing_uid:
        is_new = False

    with open(f'{project_root()}/data/mocked_jsons/chain.json') as f:
        chain = json.load(f)
        uid = chain['uid']

    if not is_new:
        uid = existing_uid
    else:
        # TODO save chain to database
        warnings.warn('Cannot create new chain')

    return uid, is_new

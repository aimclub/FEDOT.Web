import json


def chain_by_uid(uid: str) -> dict:
    chain_json = None
    with open('./data/mocked_jsons/chain.json') as f:
        chain_json = json.load(f)
        chain_json['uid'] = uid

    return chain_json


def create_chain_from_graph(graph: dict):
    # TODO convert graph to Chain

    # TODO search chain with same structure and data in database
    is_exists = True

    uid = 'new_uid'

    if is_exists:
        with open('./data/mocked_jsons/chain.json') as f:
            chain = json.load(f)
            uid = chain['uid']
    else:
        raise NotImplementedError('Cannot create new chain')
        # TODO save chain to database

    return uid, is_exists

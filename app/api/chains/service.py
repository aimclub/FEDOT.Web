import json
import hashlib
import warnings
from typing import Tuple

from fedot.core.chains.chain import Chain
from fedot.core.chains.chain_validation import validate
from fedot.core.chains.node import PrimaryNode, SecondaryNode

from app import storage


def chain_first():
    #    XG
    #  |     \
    # XG     KNN
    # |  \    |  \
    # LR LDA LR  LDA
    chain = Chain()

    root_of_tree, root_child_first, root_child_second = \
        [SecondaryNode(model) for model in ('xgboost', 'xgboost', 'knn')]

    for root_node_child in (root_child_first, root_child_second):
        for requirement_model in ('logit', 'lda'):
            new_node = PrimaryNode(requirement_model)
            root_node_child.nodes_from.append(new_node)
            chain.add_node(new_node)
        chain.add_node(root_node_child)
        root_of_tree.nodes_from.append(root_node_child)

    chain.add_node(root_of_tree)
    return chain


def chain_mock():
    #      XG
    #   |      \
    #  XG      KNN
    #  | \      |  \
    # LR XG   LR   LDA
    #    |  \
    #   KNN  LDA
    new_node = SecondaryNode('xgboost')
    for model_type in ('knn', 'pca'):
        new_node.nodes_from.append(PrimaryNode(model_type))
    chain = chain_first()
    chain.update_subtree(chain.root_node.nodes_from[0].nodes_from[1], new_node)
    return chain


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
    hash = hashlib.md5(dumped_json.encode('utf-8')).hexdigest()
    if storage.db.chains.find_one({'hash': hash}):
        is_duplicate = True

    if is_new and not is_duplicate:
        dict_chain = json.loads(dumped_json)
        dict_chain['hash'] = hash
        dict_chain['uid'] = uid
        storage.db.chains.insert_one(dict_chain)
    else:
        warnings.warn('Cannot create new chain')

    return uid, is_new

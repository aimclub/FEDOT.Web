import json

import bson
import pymongo
from fedot.core.chains.chain import Chain
from fedot.core.chains.node import PrimaryNode, SecondaryNode
from pymongo.errors import CollectionInvalid

from app.api.data.service import get_input_data


def create_default_chains(db):
    _create_collection(db, 'chains', 'uid')

    _create_custom_chain(db, 'best_scoring_chain', 'scoring', chain_mock('class'))
    chain_1 = Chain(SecondaryNode('logit', nodes_from=[SecondaryNode('logit',
                                                                     nodes_from=[PrimaryNode('scaling')]),
                                                       PrimaryNode('knn')]))
    _create_custom_chain(db, 'scoring_chain_1', 'scoring', chain_1)

    chain_2 = Chain(SecondaryNode('logit', nodes_from=[SecondaryNode('logit',
                                                                     nodes_from=[PrimaryNode('scaling')]),
                                                       SecondaryNode('knn',
                                                                     nodes_from=[PrimaryNode('scaling')])]))
    _create_custom_chain(db, 'scoring_chain_2', 'scoring', chain_2)
    _create_custom_chain(db, 'scoring_baseline', 'scoring', get_baseline('class'))

    ######

    _create_custom_chain(db, 'best_metocean_chain', 'metocean', chain_mock('ts'))
    _create_custom_chain(db, 'metocean_baseline', 'metocean', get_baseline('ts'))

    #######

    _create_custom_chain(db, 'best_oil_chain', 'oil', chain_mock('regr'))
    _create_custom_chain(db, 'oil_baseline', 'oil', get_baseline('regr'))


def _create_custom_chain(db, chain_id, case_id, chain):
    uid = chain_id
    data = get_input_data(dataset_name=case_id, sample_type='train')
    chain.fit(data)
    chain_dict, dict_fitted_operations = _extract_chain_with_fitted_operations(chain, uid)
    chain_dict['uid'] = uid
    _add_chain_to_db(db, uid, chain_dict, dict_fitted_operations)


def _extract_chain_with_fitted_operations(chain, uid):
    chain_json, dict_fitted_operations = chain.save()
    chain_json = json.loads(chain_json)
    new_dct = {}
    for i in dict_fitted_operations:
        data = dict_fitted_operations[i].getvalue()
        new_dct[i.replace(".", "-")] = bson.Binary(data)
    new_dct['uid'] = uid
    return chain_json, new_dct


def _create_collection(db, name: str, id_name: str):
    try:
        db.create_collection(name)
        db.chains.create_index([(id_name, pymongo.TEXT)], unique=True)
    except CollectionInvalid:
        print('Chains collection already exists')


def _add_chain_to_db(db, uid, chain_dict, dict_fitted_operations):
    _add_to_db(db, 'uid', uid, chain_dict)
    db.dict_fitted_operations.remove(dict_fitted_operations)
    db.dict_fitted_operations.insert(dict_fitted_operations, check_keys=False)


def _add_to_db(db, id_name, id_value, obj_to_add):
    db.chains.remove({id_name: id_value})
    db.chains.insert_one(obj_to_add)


def _chain_first():
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


def chain_mock(task: str = 'class'):
    if task == 'regr':
        new_node = SecondaryNode('ridge')
        for model_type in ('scaling', 'xgbreg'):
            new_node.nodes_from.append(PrimaryNode(model_type))
        chain = Chain(new_node)
    elif task == 'ts':
        new_node = SecondaryNode('ridge')
        new_node.nodes_from.append(PrimaryNode('lagged'))
        chain = Chain(new_node)
    else:
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
        chain = _chain_first()
        chain.update_subtree(chain.root_node.nodes_from[0].nodes_from[1], new_node)
    return chain


def get_baseline(task: str = 'class'):
    if task == 'regr':
        chain = Chain(PrimaryNode('ridge'))
    elif task == 'ts':
        new_node = SecondaryNode('linear', nodes_from=[PrimaryNode('lagged')])
        chain = Chain(new_node)
    else:
        chain = Chain(PrimaryNode('logit'))
    return chain

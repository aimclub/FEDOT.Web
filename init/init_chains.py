import json
import os

import pymongo
from fedot.core.chains.chain import Chain
from fedot.core.chains.node import SecondaryNode, PrimaryNode
from pymongo.errors import CollectionInvalid

from app.api.chains.chain_convert_utils import chain_to_graph
from app.api.data.service import get_input_data
from utils import project_root


def create_default_chains(storage):
    _create_collection(storage, 'chains', 'uid')

    data = get_input_data(dataset_name='scoring', sample_type='train')
    chain = chain_mock()
    chain.fit(data)
    dict_fitted_operations = _extract_fitted_operations(chain)
    scoring_case_chain = chain_to_graph(chain)

    scoring_case_chain.uid = 'best_scoring_chain'
    _add_chain_to_db(storage, scoring_case_chain, dict_fitted_operations)

    return


def _extract_fitted_operations(chain):
    dict_fitted_operations = {}
    chain_json = json.loads(chain.save())
    for op in chain_json['nodes']:
        with open(os.path.join(project_root(), 'data/mocked_jsons/', op['fitted_operation_path']), 'rb') as f:
            op_pickle = f.read()
            dict_fitted_operations[op['fitted_operation_path']] = op_pickle
    return dict_fitted_operations


def _create_collection(storage, name: str, id_name: str):
    try:
        storage.db.create_collection(name)
        storage.db.chains.create_index([(id_name, pymongo.TEXT)], unique=True)
    except CollectionInvalid:
        print('Chains collection already exists')


def _add_chain_to_db(storage, chain, dict_fitted_operations):
    chain_dict = {
        'uid': chain.uid,
        'nodes': chain.nodes,
        'edges': chain.edges,
    }

    _add_to_db(storage, 'uid', chain.uid, chain_dict)
    storage.db.dict_fitted_operations.insert(dict_fitted_operations, check_keys=False)


def _add_to_db(storage, id_name, id_value, obj_to_add):
    storage.db.chains.remove({id_name: id_value})
    storage.db.chains.insert_one(obj_to_add)


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
    chain = _chain_first()
    chain.update_subtree(chain.root_node.nodes_from[0].nodes_from[1], new_node)
    return chain

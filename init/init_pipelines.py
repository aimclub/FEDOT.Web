import json
import os

import bson
import gridfs
import pymongo
from bson import json_util
from fedot.core.pipelines.node import PrimaryNode, SecondaryNode
from fedot.core.pipelines.pipeline import Pipeline
from pymongo.errors import CollectionInvalid

from app.api.data.service import get_input_data
from utils import project_root


def create_default_pipelines(db=None):
    if db:
        _create_collection(db, 'pipelines', 'uid')

    mock_list = []

    _create_custom_pipeline(db, 'best_scoring_pipeline', 'scoring', pipeline_mock('class'), mock_list)
    pipeline_1 = Pipeline(SecondaryNode('logit', nodes_from=[SecondaryNode('logit',
                                                                           nodes_from=[PrimaryNode('scaling')]),
                                                             PrimaryNode('knn')]))
    _create_custom_pipeline(db, 'scoring_pipeline_1', 'scoring', pipeline_1, mock_list)

    pipeline_2 = Pipeline(SecondaryNode('logit', nodes_from=[SecondaryNode('logit',
                                                                           nodes_from=[PrimaryNode('scaling')]),
                                                             SecondaryNode('knn',
                                                                           nodes_from=[PrimaryNode('scaling')])]))
    _create_custom_pipeline(db, 'scoring_pipeline_2', 'scoring', pipeline_2, mock_list)
    _create_custom_pipeline(db, 'scoring_baseline', 'scoring', get_baseline('class'), mock_list)

    ######

    _create_custom_pipeline(db, 'best_metocean_pipeline', 'metocean', pipeline_mock('ts'), mock_list)
    _create_custom_pipeline(db, 'metocean_baseline', 'metocean', get_baseline('ts'), mock_list)

    #######

    _create_custom_pipeline(db, 'best_oil_pipeline', 'oil', pipeline_mock('regr'), mock_list)
    _create_custom_pipeline(db, 'oil_baseline', 'oil', get_baseline('regr'), mock_list)

    if len(mock_list) > 0:
        pipelines = [i[0] for i in mock_list]
        with open(os.path.join(project_root(), 'test/fixtures/pipelines.json'), 'w') as f:
            f.write(json_util.dumps(pipelines))
            print('pipelines are mocked')

        dict_fitted_operations = [i[1] for i in mock_list]
        with open(os.path.join(project_root(), 'test/fixtures/dict_fitted_operations.json'), 'w') as f:
            f.write(json_util.dumps(dict_fitted_operations))
            print('dict_fitted_operations are mocked')


def _create_custom_pipeline(db, pipeline_id, case_id, pipeline, mock_list):
    uid = pipeline_id
    data = get_input_data(dataset_name=case_id, sample_type='train')
    if db is None:
        data = data.subset(0, 500)
    pipeline.fit(data)
    pipeline_dict, dict_fitted_operations = _extract_pipeline_with_fitted_operations(pipeline, uid)
    pipeline_dict['uid'] = uid
    if db:
        _add_pipeline_to_db(db, uid, pipeline_dict, dict_fitted_operations)
    else:
        mock_list.append([pipeline_dict, dict_fitted_operations])


def _extract_pipeline_with_fitted_operations(pipeline, uid):
    try:
        pipeline_json, dict_fitted_operations = pipeline.save()
    except:
        return
    pipeline_json = json.loads(pipeline_json)
    new_dct = {}
    for i in dict_fitted_operations:
        data = dict_fitted_operations[i].getvalue()
        new_dct[i.replace(".", "-")] = bson.Binary(data)
    new_dct['uid'] = uid
    pipeline_json['uid'] = uid
    return pipeline_json, new_dct


def _create_collection(db, name: str, id_name: str):
    try:
        db.create_collection(name)
        db.pipelines.create_index([(id_name, pymongo.TEXT)], unique=True)
    except CollectionInvalid:
        print('Pipelines collection already exists')


def _add_pipeline_to_db(db, uid, pipeline_dict, dict_fitted_operations):
    _add_to_db(db, 'uid', uid, pipeline_dict)
    fs = gridfs.GridFS(db)
    file = fs.find_one({'filename': uid, 'type': 'dict_fitted_operations'})
    if file:
        fs.delete(file._id)
    fs.put(json_util.dumps(dict_fitted_operations), filename=uid, type='dict_fitted_operations', encoding='utf-8')


def _add_to_db(db, id_name, id_value, obj_to_add):
    db.pipelines.remove({id_name: id_value})
    db.pipelines.insert_one(obj_to_add)


def _pipeline_first():
    #    XG
    #  |     \
    # XG     KNN
    # |  \    |  \
    # LR LDA LR  LDA
    pipeline = Pipeline()

    root_of_tree, root_child_first, root_child_second = \
        [SecondaryNode(model) for model in ('xgboost', 'xgboost', 'knn')]

    for root_node_child in (root_child_first, root_child_second):
        for requirement_model in ('logit', 'pca'):
            new_node = PrimaryNode(requirement_model)
            root_node_child.nodes_from.append(new_node)
            pipeline.add_node(new_node)
        pipeline.add_node(root_node_child)
        root_of_tree.nodes_from.append(root_node_child)

    pipeline.add_node(root_of_tree)
    return pipeline


def pipeline_mock(task: str = 'class'):
    if task == 'regr':
        new_node = SecondaryNode('ridge')
        for model_type in ('scaling', 'xgbreg'):
            new_node.nodes_from.append(PrimaryNode(model_type))
        pipeline = Pipeline(new_node)
    elif task == 'ts':
        new_node = SecondaryNode('ridge')
        new_node.nodes_from.append(PrimaryNode('lagged'))
        pipeline = Pipeline(new_node)
    else:
        #      XG
        #   |      \
        #  XG      KNN
        #  | \      |  \
        # LR XG   LR   LDA
        #    |  \
        #   KNN  LDA
        new_node = SecondaryNode('xgboost')
        for model_type in ('knn', 'lda'):
            new_node.nodes_from.append(PrimaryNode(model_type))
        pipeline = _pipeline_first()
        pipeline.update_subtree(pipeline.root_node.nodes_from[0].nodes_from[1], new_node)
    return pipeline


def get_baseline(task: str = 'class'):
    if task == 'regr':
        pipeline = Pipeline(PrimaryNode('ridge'))
    elif task == 'ts':
        new_node = SecondaryNode('linear', nodes_from=[PrimaryNode('lagged')])
        pipeline = Pipeline(new_node)
    else:
        pipeline = Pipeline(PrimaryNode('logit'))
    return pipeline

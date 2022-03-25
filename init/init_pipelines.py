import json
import os

import bson
from bson import json_util
from fedot.core.pipelines.node import PrimaryNode, SecondaryNode
from fedot.core.pipelines.pipeline import Pipeline

from app.api.data.service import get_input_data
from app.api.pipelines.service import _add_pipeline_to_db
from app.singletons.db_service import DBServiceSingleton
from utils import project_root


def create_default_pipelines():
    db_service = DBServiceSingleton()
    db_service.try_create_collection('pipelines', '_id')

    cases = [
        {
            'individual_id': 'best_scoring_pipeline', 'case_id': 'scoring',
            'pipeline': pipeline_mock('class'), 'task_type': 'classification'
        },
        {
            'individual_id': 'scoring_baseline', 'case_id': 'scoring',
            'pipeline': get_baseline('class'), 'task_type': 'classification'
        },
        {
            'individual_id': 'metocean_baseline', 'case_id': 'metocean',
            'pipeline': get_baseline('ts'), 'task_type': 'ts_forecasting'
        },
        {
            'individual_id': 'oil_baseline', 'case_id': 'oil',
            'pipeline': get_baseline('regr'), 'task_type': 'regression'
        }
    ]

    mock_list = [_create_custom_pipeline(**case) for case in cases]

    if not db_service.exists():
        mockup_pipelines(mock_list)


def mockup_pipelines(mock_list):
    if len(mock_list) > 0:
        pipelines = [i[0] for i in mock_list]
        with open(os.path.join(project_root(), 'test/fixtures/pipelines.json'), 'w') as f:
            f.write(json_util.dumps(pipelines))
            print('pipelines are mocked')

        dict_fitted_operations = [i[1] for i in mock_list]
        with open(os.path.join(project_root(), 'test/fixtures/dict_fitted_operations.json'), 'w') as f:
            f.write(json_util.dumps(dict_fitted_operations))
            print('dict_fitted_operations are mocked')


def _create_custom_pipeline(individual_id: str, case_id: str, pipeline: Pipeline, task_type: str):
    uid = individual_id
    data = get_input_data(dataset_name=case_id, sample_type='train', task_type=task_type)
    db_service = DBServiceSingleton()
    if not db_service.exists():
        data = data.subset_range(0, 50)
    pipeline.fit(data)
    pipeline_dict, dict_fitted_operations = _extract_pipeline_with_fitted_operations(pipeline, uid)
    pipeline_dict['_id'] = uid
    if db_service.exists():
        _add_pipeline_to_db(uid, pipeline_dict, dict_fitted_operations)

    return [pipeline_dict, dict_fitted_operations]


def _extract_pipeline_with_fitted_operations(pipeline, uid):
    pipeline_json, dict_fitted_operations = pipeline.save()
    pipeline_json = json.loads(pipeline_json)
    new_dct = {}
    for i in dict_fitted_operations:
        data = dict_fitted_operations[i].getvalue()
        new_dct[i.replace(".", "-")] = bson.Binary(data)
    new_dct['_id'] = uid
    pipeline_json['_id'] = uid
    return pipeline_json, new_dct


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

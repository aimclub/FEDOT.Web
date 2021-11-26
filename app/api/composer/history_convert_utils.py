from copy import deepcopy
from typing import Any, Dict

import networkx as nx
from fedot.core.optimisers.opt_history import OptHistory
from matplotlib import pyplot as plt


def history_to_graph(history: OptHistory) -> Dict[str, Any]:
    all_nodes = _create_operators_and_nodes(history)

    all_nodes, edges = _create_edges(all_nodes)
    all_nodes = _clear_tmp_fields(all_nodes)

    # postprocessing of edges
    new_edges = []
    nodes_ids = [n['uid'] for n in all_nodes]
    for _, edge in enumerate(edges):
        if edge['source'] in nodes_ids and edge['target'] in nodes_ids and edge['source'] != edge['target']:
            new_edges.append(edge)
        else:
            print(edge)

    output_graph_dict = {
        'nodes': all_nodes,
        'edges': new_edges
    }

    if False:
        _draw_history(output_graph_dict)

    return output_graph_dict


def _process_operator(all_nodes, operator, individual, o_id, gen_id, prev_operator, skip_next):
    operator_node = _init_operator_dict(operator=operator, o_id=o_id, gen_id=gen_id,
                                        ind=individual)
    if prev_operator:
        # parent is operator, not individual
        operator_node['parent_operator'] = prev_operator.uid
        operator_node['tmp_parent_pipelines'] = []

    if skip_next:
        operator_node['tmp_next_pipeline'] = []
    if operator.uid \
            not in [n['tmp_operator_uid'] for n in all_nodes if n['type'] == 'evo_operator']:
        all_nodes.append(operator_node)
    else:
        node_to_update = \
            [n for n in all_nodes if n['type'] == 'evo_operator' and n['tmp_operator_uid'] == operator.uid][0]
        node_to_update['tmp_parent_pipelines'].extend(operator_node['tmp_parent_pipelines'])
    return all_nodes


def _create_all_pipeline_nodes_for_pop(history, all_nodes, gen_id, local_id):
    for ind_id in range(len(history.individuals[gen_id])):
        individual = history.individuals[gen_id][ind_id]

        # add pipelines as node
        pipeline_id = str(individual.graph.uid)
        uid = f'pipeline_{gen_id}_{ind_id}'
        objs = {}
        for metric in history.metrics:
            objs[str(metric)] = history.all_historical_fitness[local_id]
        pipeline_node = _init_pipeline_dict(individual, objs, uid, pipeline_id, gen_id, ind_id)
        all_nodes.append(pipeline_node)
        local_id += 1

    return all_nodes, local_id


def _create_operators_and_nodes(history):
    all_nodes = []
    local_id = 0
    for gen_id in range(len(history.archive_history)):
        o_id = 0
        all_nodes, local_id = _create_all_pipeline_nodes_for_pop(history, all_nodes, gen_id, local_id)
        if gen_id == 0:
            continue
        for ind_id in range(len(history.archive_history[gen_id])):
            individual = history.archive_history[gen_id][ind_id]

            # add evo operators as nodes
            operators = history.archive_history[gen_id][ind_id].parent_operators
            operators = [operators] if not isinstance(operators, list) else operators

            for o_num, operator in enumerate(operators):
                if isinstance(operator, list) and len(operator) == 0:
                    continue
                prev_operator = None
                if operator.operator_type != 'selection':
                    # connect with previous operator (e.g. crossover -> mutation)
                    skip_next = False
                    if len(operators) > 1:
                        # in several operator in a row
                        if o_num > 0:
                            prev_operator = operators[o_num - 1]
                        else:
                            skip_next = True

                    all_nodes = _process_operator(all_nodes, operator, individual, o_id, gen_id,
                                                  prev_operator, skip_next)
                    o_id += 1
    return all_nodes


def _create_edges(all_nodes):
    edges = []
    for i, node in enumerate(all_nodes):
        # connect individuals
        if node['type'] == 'individual':
            if node['gen_id'] > 0:
                # same inds from prev generation
                parent_ind = [n for n in all_nodes if n['type'] == 'individual'
                              and n['tmp_pipeline_uid'] == node['tmp_pipeline_uid'] and
                              n['gen_id'] == node['gen_id'] - 1]

                if len(parent_ind) > 0:
                    edges = _add_edge(edges, parent_ind[0]['uid'], node['uid'])

        elif node['type'] == 'evo_operator':
            # from pipeline to operator
            operator_node = node
            prev_pipelines = [n for n in all_nodes if n['type'] == 'individual'
                              and n['tmp_pipeline_uid'] in operator_node['tmp_parent_pipelines']
                              and n['gen_id'] == operator_node['prev_gen_id']]
            if len(prev_pipelines) > 0:
                for prev_pipeline in prev_pipelines:
                    edges = _add_edge(edges, prev_pipeline['uid'], operator_node['uid'])

            if 'parent_operator' in operator_node:
                parent_operator = [n for n in all_nodes if n['type'] == 'evo_operator'
                                   and n['tmp_operator_uid'] == operator_node['parent_operator']][0]
                edges = _add_edge(edges, parent_operator['uid'], operator_node['uid'])

            # from operator to pipeline
            next_pipelines = [n for n in all_nodes if n['type'] == 'individual'
                              and n['tmp_pipeline_uid'] == operator_node['tmp_next_pipeline']
                              and (n['gen_id'] == operator_node['next_gen_id'])]

            if len(next_pipelines) > 0:
                edges = _add_edge(edges, operator_node['uid'], next_pipelines[0]['uid'])

    return all_nodes, edges


def _add_edge(edges, source, target):
    edge = dict()
    edge['source'] = source
    edge['target'] = target
    if edge not in edges:
        edges.append(edge)
    return edges


def _init_operator_dict(ind, operator, o_id, gen_id):
    operator_id = f'evo_operator_{gen_id}_{o_id}_{operator.operator_type}'
    operator_node = dict()
    operator_node['tmp_operator_uid'] = operator.uid
    operator_node['uid'] = operator_id
    operator_node['prev_gen_id'] = gen_id - 1
    operator_node['next_gen_id'] = gen_id
    operator_node['operator_id'] = o_id
    operator_node['type'] = 'evo_operator'
    operator_node['name'] = operator.operator_type,
    operator_node['full_name'] = operator.operator_name

    # temporary fields
    operator_node['tmp_parent_pipelines'] = [c.struct_id for c in operator.parent_objects]
    operator_node['tmp_next_pipeline'] = ind.graph.root_node.descriptive_id if ind.graph.root_node else ''
    return operator_node


def _init_pipeline_dict(ind, objs, uid, pipeline_id, gen_id, ind_id):
    pipeline = dict()
    pipeline['uid'] = uid
    pipeline['gen_id'] = gen_id
    pipeline['ind_id'] = ind_id
    pipeline['type'] = 'individual'
    pipeline['pipeline_id'] = pipeline_id
    pipeline['objs'] = objs
    pipeline['tmp_pipeline_uid'] = ind.graph.root_node.descriptive_id if ind.graph.root_node else ''
    return pipeline


def _clear_tmp_fields(all_nodes):
    for node in all_nodes:
        if 'tmp_pipeline_uid' in node:
            del node['tmp_pipeline_uid']
        if 'tmp_parent_pipelines' in node:
            del node['tmp_parent_pipelines']
        if 'tmp_next_pipeline' in node:
            del node['tmp_next_pipeline']
        if 'source_pipeline' in node:
            del node['source_pipeline']
        if 'tmp_operator_uid' in node:
            del node['tmp_operator_uid']
    return all_nodes


def _move_pipeline_to_next_gen(pipeline, nodes, operator_node, generation_field_to_check):
    if pipeline['gen_id'] < operator_node[generation_field_to_check]:
        pipeline_copy = deepcopy(pipeline)
        gen_id = operator_node[generation_field_to_check]
        # increment index of individual in population
        try:
            new_ind_id = max(
                [n['ind_id'] for n in nodes if n['type'] == 'individual' and n['gen_id'] == gen_id]) + 1
        except ValueError:
            new_ind_id = 0

        pipeline_copy['gen_id'] = gen_id
        pipeline_copy['ind_id'] = new_ind_id
        pipeline_copy['uid'] = f'pipeline_{gen_id}_{new_ind_id}'
        return pipeline_copy
    return None


def _history_dict_as_nx_graph(history):
    """ Convert history into networkx graph object """
    graph = nx.DiGraph()
    node_labels = {}
    new_node_idx = {}
    for node in history['nodes']:
        unique_id, label = node['uid'], node['uid']
        node_labels[unique_id] = node
        new_node_idx[node['uid']] = unique_id
        graph.add_node(unique_id)

    def add_edges(graph, history):
        for edge in history['edges']:
            if edge['source'] in graph.nodes and edge['target'] in graph.nodes:
                graph.add_edge(edge['source'], edge['target'])

    add_edges(graph, history)
    return graph, node_labels


def _draw_history(history):
    nx_graph, node_labels = _history_dict_as_nx_graph(history)
    p = nx.drawing.nx_pydot.to_pydot(nx_graph)
    p.write_png('graph.png')


def _colors_by_node_labels(node_labels: dict):
    colors = [color for color in range(len(node_labels.keys()))]
    return colors


def _draw_labels(pos, node_labels):
    for node, (x, y) in pos.items():
        text = node_labels[node]['uid']
        plt.text(x, y, text, ha='center', va='center')

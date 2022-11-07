from copy import deepcopy
from typing import Any, Dict

import networkx as nx
from fedot.core.optimisers.opt_history_objects.opt_history import OptHistory
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
        operator_node['tmp_parent_individuals'] = []

    if skip_next:
        # there is next operator, not individual
        operator_node['tmp_next_individual_id'] = None

    existing_operators = [n['tmp_operator_uid'] for n in all_nodes if n['type'] == 'evo_operator']
    if operator.uid not in existing_operators:
        all_nodes.append(operator_node)
    else:
        # find node that should be connected with operator
        operator_to_update = next(
            (n for n in all_nodes if n['type'] == 'evo_operator' and n['tmp_operator_uid'] == operator.uid),
            None
        )
        if operator_to_update is not None:
            parents_for_operator = operator_node['tmp_parent_individuals']
            for parent in parents_for_operator:
                if parent not in operator_to_update['tmp_parent_individuals']:
                    operator_to_update['tmp_parent_individuals'].append(parent)
    return all_nodes


def _create_all_individuals_for_population(history, all_nodes, gen_id, order_id, uids_to_show):
    for ind_id in range(len(history.individuals[gen_id])):
        individual = history.individuals[gen_id][ind_id]
        if individual.uid not in uids_to_show or gen_id > uids_to_show[individual.uid]:
            continue

        # add pipelines as node
        individual_id = individual.uid
        uid = f'ind_{gen_id}_{ind_id}'
        objs = {}
        for metric in history._objective.metric_names:
            objs[metric] = history.all_historical_fitness[order_id]
        pipeline_node = _init_pipeline_dict(individual, objs, uid, individual_id, gen_id, ind_id)
        all_nodes.append(pipeline_node)
        order_id += 1

    return all_nodes, order_id


def _create_operators_and_nodes(history):
    all_nodes = []
    current_order_id = 0
    if hasattr(history, 'final_choices') and history.final_choices:
        final_choices = history.final_choices
    elif len(history.individuals[-1]) == 1:
        final_choices = history.individuals[-1]
    else:
        final_choices = [max(history.individuals[-1], key=lambda ind: ind.fitness)]

    uid_to_last_generation_map = {ind.uid: len(history.individuals) for ind in final_choices}
    current_inds = final_choices
    for iteration in range(10_000):
        next_inds = []
        for ind in current_inds:
            if not ind.parents:
                continue
            for parent in ind.parents_from_prev_generation:
                next_inds.append(parent)
                gen_id = max(uid_to_last_generation_map.get(parent.uid, 0), ind.native_generation - 1)
                uid_to_last_generation_map[parent.uid] = gen_id
        current_inds = next_inds

    for gen_id, generation in enumerate(history.individuals):
        o_id = 0
        all_nodes, current_order_id = _create_all_individuals_for_population(history, all_nodes, gen_id,
                                                                             current_order_id,
                                                                             uid_to_last_generation_map)
        if gen_id == 0:
            continue
        for ind_id, individual in enumerate(generation):
            if individual.native_generation != gen_id:
                continue
            if individual.uid not in uid_to_last_generation_map or gen_id > uid_to_last_generation_map[individual.uid]:
                continue

            # add evo operators as nodes
            parent_operators_for_ind = individual.operators_from_prev_generation
            for o_num, operator in enumerate(parent_operators_for_ind):
                if not operator.parent_individuals:
                    continue

                prev_operator = None
                if operator.type_ == 'selection':
                    continue
                # connect with previous operator (e.g. crossover -> mutation)
                skip_next = False
                # in several operator in a row
                if o_num > 0:
                    prev_operator = parent_operators_for_ind[o_num - 1]
                if o_num < len(parent_operators_for_ind) - 1:
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
                parent_ind = next((n for n in all_nodes if n['type'] == 'individual'
                                   and n['individual_id'] == node['individual_id'] and
                                   n['gen_id'] == node['gen_id'] - 1), None)

                if parent_ind is not None:
                    edges = _add_edge(edges, parent_ind['uid'], node['uid'])

        elif node['type'] == 'evo_operator':
            # from pipeline to operator
            operator_node = node
            prev_pipelines = [n for n in all_nodes if n['type'] == 'individual'
                              and n['individual_id'] in operator_node['tmp_parent_individuals']
                              and n['gen_id'] == operator_node['prev_gen_id']]

            used_individuals_ids = []
            for prev_individual in prev_pipelines:
                if prev_individual['individual_id'] not in used_individuals_ids:
                    edges = _add_edge(edges, prev_individual['uid'], operator_node['uid'])
                    used_individuals_ids.append(prev_individual['individual_id'])

            if 'parent_operator' in operator_node:
                parent_operator = [n for n in all_nodes if n['type'] == 'evo_operator'
                                   and n['tmp_operator_uid'] == operator_node['parent_operator']][0]
                edges = _add_edge(edges, parent_operator['uid'], operator_node['uid'])

            # from operator to individual
            next_individual = next((n for n in all_nodes if n['type'] == 'individual'
                                    and n['individual_id'] == operator_node['tmp_next_individual_id']
                                    and n['gen_id'] == operator_node['next_gen_id']), None)

            if next_individual is not None:
                edges = _add_edge(edges, operator_node['uid'], next_individual['uid'])

    return all_nodes, edges


def _add_edge(edges, source, target):
    edge = dict()
    edge['source'] = source
    edge['target'] = target
    if edge not in edges:
        edges.append(edge)
    return edges


def _init_operator_dict(ind, operator, o_id, gen_id):
    operator_id = f'evo_operator_{gen_id}_{o_id}_{operator.type_}'
    operator_node = dict()
    operator_node['tmp_operator_uid'] = operator.uid
    operator_node['uid'] = operator_id
    operator_node['prev_gen_id'] = gen_id - 1
    operator_node['next_gen_id'] = gen_id
    operator_node['operator_id'] = o_id
    operator_node['type'] = 'evo_operator'
    operator_node['name'] = operator.type_
    operator_node['full_name'] = ', '.join(operator.operators)

    # temporary fields
    try:
        operator_node['tmp_parent_individuals'] = [c.uid for c in operator.parent_individuals]
    except Exception as ex:
        # in case of incorrect ids
        print(f'Error: can not create tmp_parent_individuals: {ex}')
        operator_node['tmp_parent_individuals'] = []

    operator_node['tmp_next_individual_id'] = ind.uid
    return operator_node


def _init_pipeline_dict(ind, objs, uid, individual_id, gen_id, ind_id):
    pipeline = dict()
    pipeline['uid'] = uid
    pipeline['gen_id'] = gen_id
    pipeline['ind_id'] = ind_id
    pipeline['type'] = 'individual'
    pipeline['individual_id'] = individual_id
    pipeline['objs'] = objs
    return pipeline


def _clear_tmp_fields(all_nodes):
    for node in all_nodes:
        if 'tmp_parent_individuals' in node:
            del node['tmp_parent_individuals']
        if 'source_individual' in node:
            del node['source_individual']
        if 'tmp_operator_uid' in node:
            del node['tmp_operator_uid']
    return all_nodes


def _move_individual_to_next_gen(individual, nodes, operator_node, generation_field_to_check):
    if individual['gen_id'] < operator_node[generation_field_to_check]:
        individual_copy = deepcopy(individual)
        gen_id = operator_node[generation_field_to_check]
        # increment index of individual in population
        try:
            new_ind_id = max(
                [n['ind_id'] for n in nodes if n['type'] == 'individual' and n['gen_id'] == gen_id]) + 1
        except ValueError:
            new_ind_id = 0

        individual_copy['gen_id'] = gen_id
        individual_copy['ind_id'] = new_ind_id
        individual_copy['uid'] = f'ind_{gen_id}_{new_ind_id}'
        return individual_copy
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

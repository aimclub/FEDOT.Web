def history_to_graph(history):
    output_graph = {}
    nodes = []
    edges = []

    local_id = 0
    for gen_id in range(len(history.chains)):
        for ind_id in range(len(history.chains[gen_id])):
            operators = history.parent_operators[gen_id][ind_id]
            operators_dict = dict()
            for o_id, operator in enumerate(operators):
                # add evo operators as nodes
                node = dict()
                node_id = f'evo_operator_{o_id}_gen{gen_id}'
                if node_id not in [n['uid'] for n in nodes]:
                    node['uid'] = node_id
                    node['type'] = 'evo_operator'
                    node['name'] = operator.operator_type,
                    node['full_name'] = operator.operator_name
                    node['tmp_parent_chains'] = [c.unique_chain_id for c in operator.parent_chains]
                    nodes.append(node)

            chain_id = ''
            objs = {}

            for metric in history.metrics:
                objs[str(metric)] = history.all_historical_fitness[local_id]

            node_id = f'chain_{gen_id}_{ind_id}'
            if node_id not in [n['uid'] for n in nodes]:
                # add operations as nodes
                ind = dict()
                ind['uid'] = node_id
                ind['type'] = 'individual'
                ind['chain_id'] = chain_id
                ind['objs'] = objs
                ind['tmp_chain_uid'] = history.chains[gen_id][ind_id].unique_chain_id
                nodes.append(ind)

            local_id += 1

    for node in nodes:
        if 'tmp_chain_uid' in node:
            chain_uid = node['tmp_chain_uid']
            parent_uids = \
                [n['uid'] for n in nodes if
                 'tmp_parent_chains' in n and
                 chain_uid in n['tmp_parent_chains']]

            for parent_uid in parent_uids:
                edge = dict()
                edge['source'] = node['uid']
                edge['target'] = parent_uid
                edges.append(edge)

    for node in nodes:
        if 'tmp_chain_uid' in node:
            del node['tmp_chain_uid']
        if 'tmp_parent_chains' in node:
            del node['tmp_parent_chains']

    output_graph['nodes'] = nodes
    output_graph['edges'] = edges

    return output_graph

import os

from fedot.core.optimisers.opt_history_objects.opt_history import OptHistory

from app.api.composer.history_convert_utils import history_to_graph
from utils import project_root


def test_correct_operator_ancestors_count(client):
    case_path = os.path.join(project_root(), 'data/scoring/scoring_classification.json')
    history = OptHistory.load(case_path)

    graph = history_to_graph(history)

    for node in graph['nodes']:
        if node['type'] == 'evo_operator':
            operator_uid, operator_name = node['uid'], node['name']
            sources = [edge['source'] for edge in graph['edges'] if edge['target'] == operator_uid]
            test_status = True
            if operator_name == 'mutation':
                test_status = len(sources) == 1
            elif operator_name == 'crossover':
                test_status = len(sources) == (2 if sources[0].startswith('ind') else 1)
            assert test_status, (
                f'{operator_name} operators must have exactly '
                f'{"one ancestor" if operator_name == "mutation" else "two ancestors"}: '
                f'operator_ancestors_ids={sources}'
            )

import json

from .models import ComposingHistory


def composer_history_for_experiment(dataset_name: str) -> ComposingHistory:
    with open('./data/mocked_jsons/evo_history.json') as f:
        evo_history_json = json.load(f)

    history = ComposingHistory(evo_history_json['populations'],
                               dataset_name,
                               evo_history_json['task_name'],
                               evo_history_json['is_finished'])
    return history

import json


def composer_history_for_experiment(dataset_id):
    with open('./data/mocked_jsons/evo_history.json') as f:
        evo_history = json.load(f)
        evo_history['dataset_id'] = dataset_id
    return evo_history

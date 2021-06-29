from .models import ChainEpochMapping, SandboxDefaultParams


def chains_ids_for_epochs_in_case(case_id):
    chain_ids_by_epochs = {
        1: 'scoring_chain_1',
        2: 'scoring_chain_2',
        3: 'best_scoring_chain'}
    return [ChainEpochMapping(key, chain_ids_by_epochs[key])
            for key in chain_ids_by_epochs.keys()]


def default_params_for_case(case_id):
    params = SandboxDefaultParams(task_id='classification',
                                  dataset_name='scoring',
                                  metric_id='roc_auc')
    return params

from .models import ChainEpochMapping, SandboxDefaultParams


def chains_ids_for_epochs_in_case(case_id):
    chain_ids_by_epochs = {
        'scoring': {1: 'scoring_chain_1',
                    2: 'scoring_chain_2',
                    3: 'best_scoring_chain'},
        'metocean': {1: 'best_metocean_chain',
                     2: 'best_metocean_chain',
                     3: 'best_metocean_chain'},
        'oil': {1: 'best_oil_chain',
                2: 'best_oil_chain',
                3: 'best_oil_chain'}
    }
    return [ChainEpochMapping(key, chain_ids_by_epochs[case_id][key])
            for key in chain_ids_by_epochs[case_id].keys()]


def default_params_for_case(case_id):
    params = SandboxDefaultParams(task_id='classification',
                                  dataset_name='scoring',
                                  metric_id='roc_auc')
    return params

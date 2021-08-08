from .models import PipelineEpochMapping, SandboxDefaultParams
from ..composer.service import composer_history_for_case


def pipelines_ids_for_epochs_in_case(case_id):
    history = composer_history_for_case(case_id)
    epochs = {}

    def get_fitness(ind):
        return ind.fitness

    for epoch_id, epoch_inds in enumerate(history.individuals):
        best_ind = min(epoch_inds, key=get_fitness)
        epochs[epoch_id + 1] = best_ind.graph.unique_pipeline_id

    return [PipelineEpochMapping(key, epochs[key])
            for key in epochs.keys()]


def default_params_for_case(case_id):
    params = SandboxDefaultParams(task_id='classification',
                                  dataset_name='scoring',
                                  metric_id='roc_auc')
    return params

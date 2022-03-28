from typing import List

from fedot.core.optimisers.opt_history import OptHistory

from .models import PipelineEpochMapping, SandboxDefaultParams
from ..composer.service import composer_history_for_case


def pipelines_ids_for_epochs_in_case(case_id: str) -> List[PipelineEpochMapping]:
    history: OptHistory = composer_history_for_case(case_id)
    epochs = {}

    for epoch_id, epoch_inds in enumerate(history.individuals, start=1):
        best_ind = min(epoch_inds, key=lambda ind: ind.fitness)
        epochs[epoch_id] = best_ind.uid

    return [PipelineEpochMapping(key, value) for key, value in epochs.items()]


def default_params_for_case(case_id: str) -> SandboxDefaultParams:
    params = SandboxDefaultParams(task_id='classification',
                                  dataset_name='scoring',
                                  metric_id='roc_auc')
    return params

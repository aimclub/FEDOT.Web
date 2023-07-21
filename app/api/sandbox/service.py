from typing import List

from golem.core.optimisers.opt_history_objects.opt_history import OptHistory

from .models import PipelineEpochMapping, SandboxDefaultParams
from ..composer.service import composer_history_for_case
from ..showcase.service import showcase_full_item_by_uid


def pipelines_ids_for_epochs_in_case(case_id: str) -> List[PipelineEpochMapping]:
    history: OptHistory = composer_history_for_case(case_id)
    epochs = {}

    for epoch_id, epoch_inds in enumerate(history.individuals, start=1):
        best_ind = min(epoch_inds, key=lambda ind: ind.fitness.value)
        epochs[epoch_id] = best_ind.uid

    return [PipelineEpochMapping(key, value) for key, value in epochs.items()]


def default_params_for_case(case_id: str) -> SandboxDefaultParams:
    item = showcase_full_item_by_uid(case_id)
    params = SandboxDefaultParams(task_id=item.metadata.task_name,
                                  dataset_name=item.metadata.dataset_name,
                                  metric_id=item.metadata.metric_name)
    return params

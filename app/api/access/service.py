from .models import PipelineEpochMapping, SandboxDefaultParams


def pipelines_ids_for_epochs_in_case(case_id):
    pipeline_ids_by_epochs = {
        1: 'ad39eb8c-6050-4734-9e0a-b9884a125a11',
        2: '2ed5ef79-94ec-49eb-af86-9bb99a4038f3',
        3: '472f9181-a454-4578-8fb1-c4c9aa813def'}
    return [PipelineEpochMapping(key, pipeline_ids_by_epochs[key])
            for key in pipeline_ids_by_epochs.keys()]


def default_params_for_case(case_id):
    params = SandboxDefaultParams(task_id='classification',
                                  dataset_name='scoring',
                                  metric_id='roc_auc')
    return params

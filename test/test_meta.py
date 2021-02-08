def test_task_names_endpoint(client):
    tasks_json = client.get(f'api/meta/tasks').json
    tasks = [task['task_name'] for task in tasks_json]
    assert {'classification',
            'regression',
            'ts_forecasting',
            'clustering'} == set(tasks)


def test_metric_names_endpoint(client):
    task_name = 'classification'
    classification_metrics_json = client.get(f'api/meta/metrics/{task_name}').json
    classification_metrics_names = [metric['metric_name'] for metric in classification_metrics_json]
    assert 'ROCAUC' in classification_metrics_names
    assert 'RMSE' not in classification_metrics_names

    task_name = 'regression'

    regression_metrics_json = client.get(f'api/meta/metrics/{task_name}').json
    regression_metrics = [metric['metric_name'] for metric in regression_metrics_json]

    assert set(regression_metrics) != set(classification_metrics_names)

    assert 'RMSE' in regression_metrics
    assert 'MAE' in regression_metrics


def test_model_names_endpoint(client):
    task_name = 'classification'
    classification_models_json = client.get(f'api/meta/models/{task_name}').json
    classification_models_names = [model['model_name'] for model in classification_models_json]
    assert 'logit' in classification_models_names
    assert 'lasso' not in classification_models_names

    task_name = 'regression'

    regression_models_json = client.get(f'api/meta/models/{task_name}').json
    regression_models = [model['model_name'] for model in regression_models_json]

    assert set(regression_models) != set(classification_models_names)

    assert 'linear' in regression_models
    assert 'knnreg' in regression_models

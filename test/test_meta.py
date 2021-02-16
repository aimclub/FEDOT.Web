def test_task_names_endpoint(client):
    tasks_json = client.get(f'api/meta/tasks').json
    tasks = [task['task_name'] for task in tasks_json]
    assert {'classification',
            'regression',
            'ts_forecasting',
            'clustering'} == set(tasks)


def test_metric_names_classification_endpoint(client):
    classification_metrics_json = \
        client.get('api/meta/metrics/classification').json
    classification_metrics_names = [metric['metric_name'] for
                                    metric in classification_metrics_json]
    assert 'ROCAUC' in classification_metrics_names
    assert 'RMSE' not in classification_metrics_names


def test_metric_names_regression_endpoint(client):
    regression_metrics_json = \
        client.get('api/meta/metrics/regression').json
    regression_metrics = [metric['metric_name'] for
                          metric in regression_metrics_json]

    assert 'RMSE' in regression_metrics
    assert 'MAE' in regression_metrics
    assert 'ROCAUC' not in regression_metrics


def test_model_names_classification_endpoint(client):
    classification_models_json = \
        client.get('api/meta/models/classification').json
    classification_models_names = [model['model_name'] for
                                   model in classification_models_json]
    assert 'logit' in classification_models_names
    assert 'linear' not in classification_models_names


def test_model_names_regression_endpoint(client):
    regression_models_json = \
        client.get('api/meta/models/regression').json
    regression_models = [model['model_name'] for
                         model in regression_models_json]

    assert 'linear' in regression_models
    assert 'logit' not in regression_models

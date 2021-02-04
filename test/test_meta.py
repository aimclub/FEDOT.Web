def test_task_names_endpoint(client):
    tasks_json = client.get(f'api/meta/tasks').json
    tasks = [task['task_name'] for task in tasks_json]
    assert set(['classification',
                'regression',
                'ts_forecasting',
                'clustering']) == set(tasks)

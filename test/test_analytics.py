def test_quality_endpoint(client):
    case_id = 'case1'
    quality_plots = client.get(f'api/analytics/quality/{case_id}').json
    quality_plot = quality_plots[0]
    assert len(quality_plot['x']) > 0
    assert len(quality_plot['x']) == len(quality_plot['y'])


def test_results_endpoint(client):
    chain_id = 'test_chain'
    case_id = 'test_case'
    results_plots = client.get(f'api/analytics/results/{case_id}/{chain_id}').json
    results_plot = results_plots[0]

    assert len(results_plot['x']) > 0
    assert len(results_plot['x']) == len(results_plot['y'])

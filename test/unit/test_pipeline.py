from app.api.data.service import get_input_data
from app.api.pipelines.service import pipeline_by_uid
from app.api.showcase.showcase_utils import showcase_item_from_db


def test_load_fitted_pipeline(app):
    pipeline, case = pipeline_by_uid('best_scoring_pipeline'), showcase_item_from_db('scoring')
    train_data = get_input_data(dataset_name='scoring', sample_type='train', task_type=case.metadata.task_name)
    prediction = pipeline.predict(train_data)
    assert prediction is not None

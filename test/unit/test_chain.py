from app.api.chains.service import chain_by_uid
from app.api.data.service import get_input_data
from app.api.showcase.service import showcase_item_by_uid


def test_load_fitted_chain_chain():
    chain, case = chain_by_uid('best_scoring_chain'), showcase_item_by_uid('scoring')
    train_data = get_input_data(dataset_name='scoring', sample_type='train')
    prediction = chain.predict(train_data)
    assert prediction is not None

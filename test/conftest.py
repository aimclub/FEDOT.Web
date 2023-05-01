import multiprocessing
import os

import pytest
from app import create_app, db, storage
from app.singletons.db_service import DBServiceSingleton

multiprocessing.set_start_method('spawn')


@pytest.fixture
def app(mongodb):
    app = create_app('test')
    storage.db = mongodb
    DBServiceSingleton(storage.db)
    with app.app_context():
        db.create_all()
    return app


@pytest.fixture
def temp_files():
    name = "test_sert"
    config = {
        "name": name,
        "cert": f"{name}.crt",
        "key": f"{name}.key"
    }
    return config


@pytest.fixture
def teardown(temp_files):
    yield
    os.remove(temp_files["cert"])
    os.remove(temp_files["key"])

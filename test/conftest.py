import os

import pytest
from app import create_app, db, storage
from app.singletons.db_service import DBServiceSingleton


@pytest.fixture
def app(mongodb):
    app = create_app('test')
    storage.db = mongodb
    DBServiceSingleton(storage.db)
    db.create_all(app=app)
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

import os

import pytest

from app import create_app, db


@pytest.fixture
def app():
    app = create_app('test')
    db.create_all(app=app)
    return app


@pytest.fixture
def temp_files():
    name = "test_sert"
    config = {
        "name": name,
        "cert": name + ".crt",
        "key": name + ".key"
    }
    return config


@pytest.fixture
def teardown(temp_files):
    yield
    os.remove(temp_files["cert"])
    os.remove(temp_files["key"])

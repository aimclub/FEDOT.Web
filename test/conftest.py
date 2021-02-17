import pytest

from app import create_app, db


@pytest.fixture
def app():
    app = create_app('test')
    db.create_all(app=app)
    return app

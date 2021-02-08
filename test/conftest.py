import pytest

from main import create_app


@pytest.fixture
def app():
    app = create_app('test')
    return app

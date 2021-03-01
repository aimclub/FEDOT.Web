import os

from app.ssl.ssl_config import SslConfig


def test_create_dummy(temp_files, teardown):
    config = SslConfig()
    config.create_dummy(temp_files["name"])
    assert os.path.exists(temp_files["cert"])
    assert os.path.exists(temp_files["key"])


def test_get_config(temp_files, teardown):
    config = SslConfig()
    config.get_config(temp_files["name"])
    assert config.ssl_cert == temp_files["cert"]
    assert config.ssl_key == temp_files["key"]


def test_get_context(temp_files, teardown):
    config = SslConfig()
    config.get_config(temp_files["name"])
    assert config.get_context() == (temp_files["cert"], temp_files["key"])

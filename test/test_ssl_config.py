import os

from app.ssl.ssl_config import SslConfig


def test_create_dummy():
    config = SslConfig()
    name = "test_sert"
    config.create_dummy(name)
    cert = name + ".crt"
    key = name + ".key"
    assert os.path.exists(cert)
    assert os.path.exists(key)


def test_get_config():
    config = SslConfig()
    name = "test_sert"
    config.get_config(name)
    cert = name + ".crt"
    key = name + ".key"
    assert config.ssl_cert == cert
    assert config.ssl_key == key


def test_get_context():
    config = SslConfig()
    name = "test_sert"
    config.get_config(name)
    cert = name + ".crt"
    key = name + ".key"
    assert config.get_context() == (cert, key)
    os.remove(cert)
    os.remove(key)

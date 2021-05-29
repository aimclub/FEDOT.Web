import os
from typing import List, Type

basedir = os.path.abspath(os.path.dirname(__file__))


class BaseConfig:
    CONFIG_NAME = "base"
    USE_MOCK_EQUIVALENCY = False
    DEBUG = False


class DevelopmentConfig(BaseConfig):
    CONFIG_NAME = "dev"
    SECRET_KEY = os.getenv("DEV_SECRET_KEY", "Dev secret")
    DEBUG = True
    TESTING = False
    DATABASE_URI = "sqlite:///{0}/app-dev.sqlite".format(basedir)
    MONGO_URI = os.getenv("MONGO_CONN_STRING")


class TestingConfig(BaseConfig):
    CONFIG_NAME = "test"
    SECRET_KEY = os.getenv("TEST_SECRET_KEY", "Test ")
    DEBUG = True
    TESTING = True
    SQLALCHEMY_DATABASE_URI = "sqlite:///{0}/app-test.sqlite".format(basedir)
    MONGO_URI = os.getenv("MONGO_CONN_STRING")


class ProductionConfig(BaseConfig):
    CONFIG_NAME = "prod"
    SECRET_KEY = os.getenv("PROD_SECRET_KEY", "I'm Ron Burgundy?")
    DEBUG = False
    TESTING = False
    DATABASE_URI = "sqlite:///{0}/app-prod.sqlite".format(basedir)


EXPORT_CONFIGS: List[Type[BaseConfig]] = [
    DevelopmentConfig,
    TestingConfig,
    ProductionConfig,
]

config_by_name = {cfg.CONFIG_NAME: cfg for cfg in EXPORT_CONFIGS}

from fcreplay.config import Config as FcreplayConfig
import os


class Config(object):
    DEBUG = False
    SQLALCHEMY_TRACK_MODIFICATIONS = False


class ProdConfig(Config):
    config = FcreplayConfig().config
    ENV = 'prod'
    SQLALCHEMY_DATABASE_URI = config['sql_baseurl']
    SECRET_KEY = config['secret_key']


class DevConfig(Config):
    os.environ['FCREPLAY_CONFIG'] = 'config_dev.json'
    config = FcreplayConfig().config

    ENV = 'dev'
    DEBUG = True

    SQLALCHEMY_DATABASE_URI = config['sql_baseurl']
    SECRET_KEY = config['secret_key']


class TestConfig(Config):
    os.environ['FCREPLAY_CONFIG'] = 'fcreplay/tests/common/config_test_site.json'
    config = FcreplayConfig().config

    TESTING = True
    DEBUG = True

    SQLALCHEMY_DATABASE_URI = 'sqlite://'
    SECRET_KEY = 'testingtestingtesting'

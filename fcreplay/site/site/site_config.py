from fcreplay.config import Config

class Config(object):
    config = Config().config()

    ENV = 'prod'
    DEBUG = False

    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_DATABASE_URI = config['sql_baseurl']
    SECRET_KEY = config['secret_key']


    
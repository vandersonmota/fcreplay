from fcreplay.config import Config
import os
import logging

config = Config().config

GCLOUD_FUNCTION = True
if 'X_GOOGLE_FUNCTION_IDENTITY' not in os.environ:
    logging.basicConfig(
        format='%(asctime)s %(levelname)s: %(message)s',
        filename=config['logfile'],
        level=config['loglevel'],
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    logging.getLogger('sqlalchemy').setLevel(logging.ERROR)
    GCLOUD_FUNCTION = False


def info(logdata):
    if GCLOUD_FUNCTION:
        print(str(logdata))
    else:
        logging.info(logdata)


def debug(logdata):
    if GCLOUD_FUNCTION:
        print(str(logdata))
    else:
        logging.debug(logdata)


def error(logdata):
    if GCLOUD_FUNCTION:
        print(str(logdata))
    else:
        logging.error(logdata)
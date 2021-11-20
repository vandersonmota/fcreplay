from fcreplay.config import Config
from multiprocessing import Queue
import os
import logging
import logging_loki
import socket


def _loki_handler(config: Config):
    loki_handler = logging_loki.LokiQueueHandler(
        Queue(-1),
        url=config.logging_loki['url'],
        tags={
            "application": "fcreplay",
            "instance": socket.gethostname(),
        },
        auth=(config.logging_loki['username'], config.logging_loki['password']),
        version="1",
    )
    loki_handler.setLevel(config.loglevel)
    return loki_handler


def _file_handler(config: Config):
    file_handler = logging.FileHandler(
        filename=config.logfile
    )
    file_formatter = logging.Formatter(
        datefmt='%Y-%m-%d %H:%M:%S',
        fmt='%(asctime)s ' + socket.gethostname() + ' %(name)s %(levelname)s: %(message)s'
    )
    file_handler.setFormatter(file_formatter)
    return file_handler


def setup_logger():
    config = Config()

    # create logger
    logger = logging.getLogger('fcreplay')
    logger.setLevel(config.loglevel)

    # create console handler and set level
    stream_handler = logging.StreamHandler()
    stream_handler.setLevel(config.loglevel)
    logger.addHandler(stream_handler)

    # Setup logging_loki handler
    if config.logging_loki['enabled']:
        logger.addHandler(_loki_handler(config))

    # Setup file handler if we aren't running in a cloud function (which is read only)
    if 'X_GOOGLE_FUNCTION_IDENTITY' not in os.environ:
        logger.addHandler(_file_handler(config))

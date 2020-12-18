from fcreplay.config import Config
from multiprocessing import Queue
import os
import logging
import logging_loki
import socket


class Logging:
    def __init__(self):
        self.config = Config().config
        if 'X_GOOGLE_FUNCTION_IDENTITY' in os.environ:
            self.GCLOUD_FUNCTION = True
        else:
            self.GCLOUD_FUNCTION = False

        if 'X_GOOGLE_FUNCTION_IDENTITY' not in os.environ:
            self.logger = logging.getLogger("fcreplay")

            if self.config['logging_loki']['enabled']:
                self.logger.addHandler(self._setup_loki())

            # File handler
            self.logger.addHandler(self._file_handler())

            # Set level
            self.logger.setLevel(self.config['loglevel'])

    def _setup_loki(self):
        # Loki Handler
        loki_handler = logging_loki.LokiQueueHandler(
            Queue(-1),
            url=self.config['logging_loki']['url'],
            tags={
                "application": "fcreplay",
                "instance": socket.gethostname(),
            },
            auth=(self.config['logging_loki']['username'], self.config['logging_loki']['password']),
            version="1",
        )
        return loki_handler

    def _file_handler(self):
        file_handler = logging.FileHandler(
            filename=self.config['logfile']
        )
        file_formatter = logging.Formatter(
            datefmt='%Y-%m-%d %H:%M:%S',
            fmt='%(asctime)s ' + socket.gethostname() + ' %(name)s %(levelname)s: %(message)s'
        )
        file_handler.setFormatter(file_formatter)
        return file_handler

    def info(self, logdata):
        if self.GCLOUD_FUNCTION:
            print(str(logdata))
        else:
            self.logger.info(logdata)

    def debug(self, logdata):
        if self.GCLOUD_FUNCTION:
            print(str(logdata))
        else:
            self.logger.debug(logdata)

    def error(self, logdata):
        if self.GCLOUD_FUNCTION:
            print(str(logdata))
        else:
            self.logger.error(logdata)

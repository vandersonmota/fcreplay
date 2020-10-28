from fcreplay.config import Config
import os
import logging


class Logging:
    def __init__(self):
        self.config = Config().config

        self.GCLOUD_FUNCTION = True
        if 'X_GOOGLE_FUNCTION_IDENTITY' not in os.environ:
            logging.basicConfig(
                format='%(asctime)s %(name)s %(levelname)s: %(message)s',
                filename=self.config['logfile'],
                level=self.config['loglevel'],
                datefmt='%Y-%m-%d %H:%M:%S'
            )
            logging.getLogger('sqlalchemy').setLevel(logging.ERROR)
            self.GCLOUD_FUNCTION = False

    def info(self, logdata):
        if self.GCLOUD_FUNCTION:
            print(str(logdata))
        else:
            logging.info(logdata)

    def debug(self, logdata):
        if self.GCLOUD_FUNCTION:
            print(str(logdata))
        else:
            logging.debug(logdata)

    def error(self, logdata):
        if self.GCLOUD_FUNCTION:
            print(str(logdata))
        else:
            logging.error(logdata)

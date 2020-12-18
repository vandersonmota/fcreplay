from fcreplay.logging import Logging
from unittest.mock import patch
import os
import pytest
import tempfile


class TestLogging:
    @patch('logging.getLogger')
    @patch('fcreplay.logging.Config')
    def test_init(self, mock_config, mock_logging):
        temp_logfile = tempfile._get_default_tempdir() + '/' + next(tempfile._get_candidate_names())
        mock_config().config = {
            'logging_loki': {'enabled': False},
            'loglevel': 'INFO',
            'logfile': temp_logfile
        }

        Logging()

    @patch('logging.getLogger')
    @patch('fcreplay.logging.Config')
    def test_gcloud(self, mock_config, mock_logging):
        os.environ['X_GOOGLE_FUNCTION_IDENTITY'] = 'true'
        temp_logfile = tempfile._get_default_tempdir() + '/' + next(tempfile._get_candidate_names())
        mock_config().config = {
            'logging_loki': {'enabled': False},
            'loglevel': 'INFO',
            'logfile': temp_logfile
        }

        Logging()

    @patch('logging.getLogger')
    @patch('fcreplay.logging.logging_loki')
    @patch('fcreplay.logging.Config')
    def test_loki(self, mock_config, mock_logging_loki, mock_logging):
        del os.environ['X_GOOGLE_FUNCTION_IDENTITY']
        temp_logfile = tempfile._get_default_tempdir() + '/' + next(tempfile._get_candidate_names())
        mock_config().config = {
            'logging_loki': {
                'enabled': True,
                'password': 'test',
                'url': 'http://test.local',
                'username': 'test'
                },
            'loglevel': 'INFO',
            'logfile': temp_logfile
        }

        Logging()

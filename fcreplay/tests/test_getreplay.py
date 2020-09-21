import pytest
import sys
from unittest.mock import patch, mock_open, MagicMock

sys.modules['pyautogui'] = MagicMock()
from fcreplay.getreplay import Getreplay


class TestGetreplay:

    @patch('fcreplay.gcloud.Database')
    @patch('fcreplay.gcloud.Config')
    @patch('debugpy.wait_for_client')
    @patch('debugpy.listen')
    def setUp(self, mock_debugpy_listen, mock_debugpy_wait_for_client, mock_config, mock_database):
        with patch.dict('os.environ', {'REMOTE_DEBUG': 'True'}):
            getreplay = Getreplay()
            assert mock_debugpy_listen.called
            assert mock_debugpy_wait_for_client.called
            return getreplay

    def test_get_date(self):
        pass

    def test_add_replay(self):
        pass

    def get_game_replays(self):
        pass

    def get_top_weekly(self):
        pass

    def get_ranked_replays(self):
        pass

    def get_replay(self):
        pass

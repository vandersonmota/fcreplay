import pytest
import sys
from unittest.mock import patch, MagicMock

sys.modules['pyautogui'] = MagicMock()
from fcreplay.loop import Loop

class TestLoop:
    @patch('fcreplay.loop.Config')
    @patch('fcreplay.loop.Logging')
    @patch('debugpy.wait_for_client')
    @patch('debugpy.listen')
    def test_debug(self, mock_debugpy_listen, mock_debugpy_wait_for_client, mock_logging, mock_config):
        with patch.dict('os.environ', {'REMOTE_DEBUG': 'True'}):
            Loop()
            assert mock_debugpy_listen.called
            assert mock_debugpy_wait_for_client.called

    @patch('fcreplay.loop.Config')
    @patch('fcreplay.loop.Logging')
    @patch('os.mkdir')
    def test_create_dir(self, mock_mkdir, mock_logging, mock_config):
        with patch('os.path.exists', return_value=False) as mock_create_dirs:
            Loop().create_dirs()
            assert mock_create_dirs.called, "Should create dirs"

            mock_logging = MagicMock()
            assert mock_logging.any_call, "Should Log"

        with patch('os.path.exists', return_value=True) as mock_create_dirs:
            Loop().create_dirs()
            assert mock_create_dirs.not_called, "Shouldn't create dirs when they exist"

    @patch('fcreplay.loop.Config')
    @patch('fcreplay.loop.Gcloud')
    @patch('fcreplay.loop.Logging')
    @patch('fcreplay.loop.Replay', )
    @patch('os.path')
    def test_noreplay(self, mock_os, mock_replay, mock_logging, mock_gcloud, mock_config):
        with pytest.raises(SystemExit) as e:
            mock_replay.replay.return_value = None
            loop = Loop()
            loop.debug = True
            loop.main()

            assert mock_replay.add_job.not_called, "Shouldn't add a replay"
            assert e.type == SystemExit, "Should exit"

        with pytest.raises(SystemExit) as e, patch('os.path.exists', return_value=False):
            mock_os.path.exists.return_value = False

            loop = Loop()
            loop.debug = True
            loop.gcloud = True
            loop.main()

            assert mock_gcloud.destroy_replay.called, "Should destroy replay when gcloud is true"
            assert e.type == SystemExit, "Should exit"
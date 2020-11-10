import os
import sys
import tempfile
from unittest.mock import patch, MagicMock

sys.modules['pyautogui'] = MagicMock()
from fcreplay.replay import Replay


class TestReplay:
    @patch('fcreplay.replay.Gcloud')
    @patch('fcreplay.replay.Logging')
    @patch('fcreplay.replay.subprocess')
    @patch('fcreplay.replay.Database')
    @patch('fcreplay.replay.Config')
    def test_encode(self, mock_config, mock_database, mock_subprocess, mock_logging, mock_gcloud):
        r = Replay()

        with tempfile.TemporaryDirectory() as single_file_dir:
            os.mkdir(f"{single_file_dir}/finished")
            open(f"{single_file_dir}/finished/test_0.avi", "w")

            r.config = {'fcreplay_dir': single_file_dir}
            r.encode()

            mock_subprocess.run.assert_called(), 'Should call encoder'

        with tempfile.TemporaryDirectory() as multi_file_dir:
            os.mkdir(f"{multi_file_dir}/finished")
            for i in range(0, 3):
                open(f"{multi_file_dir}/finished/test_{i}.avi", "w")
            r.config = {'fcreplay_dir': multi_file_dir}
            r.encode()
            mock_subprocess.run.assert_called(), 'Should call encoder'

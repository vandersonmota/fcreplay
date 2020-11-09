import sys
import tempfile
from tempfile import TemporaryFile
from unittest.mock import patch, MagicMock

sys.modules['pyautogui'] = MagicMock()
from fcreplay.replay import Replay


class TestReplay:
    @patch('fcreplay.replay.os')
    @patch('fcreplay.replay.Gcloud')
    @patch('fcreplay.replay.Logging')
    @patch('fcreplay.replay.subprocess')
    @patch('fcreplay.replay.Database')
    @patch('fcreplay.replay.Config')
    def test_encode(self, mock_config, mock_database, mock_subprocess, mock_logging, mock_gcloud, mock_os):
        r = Replay()

        with tempfile.TemporaryDirectory() as single_file_dir:
            f1 = TemporaryFile(dir=single_file_dir)
            mock_os.listdir.return_value = [single_file_dir]
            r.encode()
            mock_subprocess.run.assert_called(), 'Should call subprocess'

        with tempfile.TemporaryDirectory() as multi_file_dir:
            f1 = TemporaryFile(dir=multi_file_dir)
            f2 = TemporaryFile(dir=multi_file_dir)
            f3 = TemporaryFile(dir=multi_file_dir)
            mock_os.listdir.return_value = [multi_file_dir]
            r.encode()
            mock_subprocess.run.assert_called(), 'Should call subprocess'

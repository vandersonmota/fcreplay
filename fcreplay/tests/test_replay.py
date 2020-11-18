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

            mock_subprocess.run.assert_called(), 'Single file should call encoder'

        with tempfile.TemporaryDirectory() as multi_file_dir:
            os.mkdir(f"{multi_file_dir}/finished")
            for i in range(0, 3):
                open(f"{multi_file_dir}/finished/test_{i}.avi", "w")

            r.config = {'fcreplay_dir': multi_file_dir}
            r.encode()
            mock_subprocess.run.assert_called(), 'Multi file sould call encoder'

        with tempfile.TemporaryDirectory() as multi_file_dir:
            os.mkdir(f"{multi_file_dir}/finished")
            for i in range(0, 3):
                open(f"{multi_file_dir}/finished/_foo_bar_{i}.avi", "w")
            
            r.config = {'fcreplay_dir': multi_file_dir}
            r.encode()
            mock_subprocess.run.assert_called(), 'Multifile with underscores should call encoder'


    @patch('fcreplay.replay.Gcloud')
    @patch('fcreplay.replay.Logging')
    @patch('fcreplay.replay.subprocess')
    @patch('fcreplay.replay.Database')
    @patch('fcreplay.replay.Config')
    def test_sort(self, mock_config, mock_database, mock_subprocess, mock_logging, mock_gcloud):
        r = Replay()

        r.config = {
            'fcreplay_dir': 'dir'
        }

        unsorted_list = [
            "foo_bar_1A.avi",
            "foo_bar_A.avi",
            "foo_bar_1.avi",
            "foo_bar_2.avi",
            "foo_bar_2B.avi",
            "foo_bar_9.avi",
            "foo_bar_0.avi",
            "foo_bar_F.avi",
            "foo_bar_10.avi",
        ]

        good_list = [
            "dir/finished/foo_bar_0.avi",
            "dir/finished/foo_bar_1.avi",
            "dir/finished/foo_bar_2.avi",
            "dir/finished/foo_bar_9.avi",
            "dir/finished/foo_bar_A.avi",
            "dir/finished/foo_bar_F.avi",
            "dir/finished/foo_bar_10.avi",
            "dir/finished/foo_bar_1A.avi",
            "dir/finished/foo_bar_2B.avi",
        ]

        sorted_list = r.sort_files(unsorted_list)

        assert sorted_list == good_list, 'List with hex characters should be sorted'

        single_list = [
            'foo_bar_0.avi'
        ]

        good_list = [
            'dir/finished/foo_bar_0.avi'
        ]
        
        sorted_list = r.sort_files(single_list)
        assert sorted_list == good_list, 'List with single file should be sorted'


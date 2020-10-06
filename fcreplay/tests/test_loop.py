import os
import pytest
import sys
import tempfile
from unittest.mock import patch, MagicMock

sys.modules['pyautogui'] = MagicMock()
from fcreplay.loop import Loop


class TestLoop:
    def setUp(self):
        loop = Loop()
        return loop

    @patch('fcreplay.loop.Config')
    @patch('debugpy.wait_for_client')
    @patch('debugpy.listen')
    def test_debugpy(self, mock_debugpy_listen, mock_debugpy_wait_for_client, mock_config):
        with patch.dict('os.environ', {'REMOTE_DEBUG': 'True'}):
            self.setUp()
            assert mock_debugpy_listen.called
            assert mock_debugpy_wait_for_client.called

    @patch('fcreplay.logging.Config')
    @patch('fcreplay.loop.Config')
    def test_create_dir(self, mock_config, mock_logging_config):
        loop = self.setUp()
        temp_dir = tempfile.TemporaryDirectory()
        loop.config = {'fcreplay_dir': temp_dir.name}

        loop.create_dirs()
        assert os.path.exists(f"{temp_dir.name}/tmp"), "Should create tmp dir"
        assert os.path.exists(f"{temp_dir.name}/videos"), "Should create vidoes dir"
        assert os.path.exists(f"{temp_dir.name}/finished"), "Should create finished dir"

    @patch('fcreplay.loop.time.sleep')
    @patch('fcreplay.loop.Config')
    @patch('fcreplay.loop.Gcloud')
    @patch('fcreplay.loop.Replay')
    def test_noreplay(self, mock_replay, mock_gcloud, mock_config, mock_time):
        with pytest.raises(SystemExit) as e:
            mock_replay().replay = None
            temp_dir = tempfile.TemporaryDirectory()

            loop = self.setUp()
            loop.config = {'fcreplay_dir': temp_dir.name, 'upload_to_ia': False}
            loop.debug = True

            loop.main()

            assert mock_replay.add_job.not_called, "Shouldn't process a replay when none is returned"
            assert e.type == SystemExit, "Should exit no errors"

        with pytest.raises(SystemExit) as e:
            temp_dir = tempfile.TemporaryDirectory()

            loop = Loop()
            loop.config = {'fcreplay_dir': temp_dir.name}

            loop.debug = True
            loop.gcloud = True
            loop.main()

            assert mock_gcloud.destroy_replay.called, "Should destroy replay when gcloud is true"
            assert e.type == SystemExit, "Should exit no errors"

        with pytest.raises(SystemExit) as e:
            temp_dir = tempfile.TemporaryDirectory()

            loop = Loop()
            loop.config = {'fcreplay_dir': temp_dir.name}

            loop.debug = True
            loop.gcloud = True
            loop.main()

            assert mock_gcloud.destroy_replay.called, "Should destroy replay when gcloud is true"
            assert e.type == SystemExit, "Should exit no errors"

    @patch('fcreplay.loop.Config')
    @patch('fcreplay.logging.Config')
    @patch('fcreplay.loop.Replay', )
    def test_ia(self, mock_replay, mock_logging_config, mock_config):
        with pytest.raises(SystemExit) as e:
            temp_dir = tempfile.TemporaryDirectory()
            loop = Loop()
            loop.config = {'upload_to_ia': True, 'upload_to_yt': False, 'remove_generated_files': False, 'fcreplay_dir': temp_dir.name}
            loop.debug = True

            loop.main()

            assert mock_replay.upload_to_ia.called, "Should upload to IA when upload_to_ia is true"
            assert e.type == SystemExit, "Should exit no errors"

    @patch('fcreplay.loop.Config')
    @patch('fcreplay.logging.Config')
    @patch('fcreplay.loop.Replay')
    def test_youtube(self, mock_replay, mock_logging_config, mock_config):
        with pytest.raises(SystemExit) as e:
            temp_dir = tempfile.TemporaryDirectory()
            loop = Loop()
            loop.config = {'upload_to_ia': False, 'upload_to_yt': True, 'remove_generated_files': False, 'fcreplay_dir': temp_dir.name}
            loop.debug = True

            loop.main()

            assert mock_replay.upload_to_yt.called, "Should upload to YT when upload_to_yt is true"
            assert e.type == SystemExit, "Should exit with no errors"

    @patch('fcreplay.loop.Config')
    @patch('fcreplay.logging.Config')
    @patch('fcreplay.loop.Replay', )
    def test_remove_files(self, mock_replay, mock_logging_config, mock_config):
        with pytest.raises(SystemExit) as e:
            temp_dir = tempfile.TemporaryDirectory()
            loop = Loop()
            loop.config = {'upload_to_ia': False, 'upload_to_yt': False, 'remove_generated_files': True, 'fcreplay_dir': temp_dir.name}
            loop.debug = True

            loop.main()

            assert mock_replay.remove_generated_files.called, "Should remove generated files when remove_generated_files is true"
            assert e.type == SystemExit, "Should exit with no errors"

    @patch('fcreplay.loop.Config')
    @patch('fcreplay.logging.Config')
    @patch('fcreplay.loop.Replay')
    def test_loop(self, mock_replay, mock_logging_config, mock_config):
        with pytest.raises(SystemExit) as e:
            temp_dir = tempfile.TemporaryDirectory()
            mock_replay.replay.return_value = True

            loop = Loop()

            loop.config = {'upload_to_ia': False, 'upload_to_yt': False, 'remove_generated_files': False, 'fcreplay_dir': temp_dir.name}
            loop.debug = True

            loop.main()

            assert mock_replay.add_job.called
            assert e.type == SystemExit, "Should exit with no errors"
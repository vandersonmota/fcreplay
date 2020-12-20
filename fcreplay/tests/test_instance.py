import os
import pathlib
import pytest
import tempfile
from unittest.mock import patch
from fcreplay.instance import Instance


class TestInstance:
    def setUp(self):
        instance = Instance()
        return instance

    @patch('fcreplay.instance.Config')
    def test_clean(self, mock_config):
        instance = self.setUp()
        fcreplay_temp_dir = tempfile.TemporaryDirectory()
        fcadefbneo_temp_dir = tempfile.TemporaryDirectory()
        instance.config = {'fcreplay_dir': fcreplay_temp_dir.name, 'fcadefbneo_path': fcadefbneo_temp_dir.name}

        instance.create_dirs()
        pathlib.Path(instance.config['fcadefbneo_path'] + '/avi').mkdir(parents=True, exist_ok=True)

        create_list = [
            f"{instance.config['fcreplay_dir']}/tmp",
            f"{instance.config['fcadefbneo_path']}/avi"
        ]

        for f in create_list:
            with open(f"{f}/fakefile.bin", 'wb') as fout:
                fout.write(os.urandom(1024))

        instance.clean()

        for f in create_list:
            assert len(os.listdir(f)) == 0, "Directory should be empty"

    @patch('fcreplay.instance.Config')
    def test_create_dir(self, mock_config):
        instance = self.setUp()
        temp_dir = tempfile.TemporaryDirectory()
        instance.config = {'fcreplay_dir': temp_dir.name}

        instance.create_dirs()
        assert os.path.exists(f"{temp_dir.name}/tmp"), "Should create tmp dir"

    @patch('fcreplay.instance.time.sleep')
    @patch('fcreplay.instance.Config')
    @patch('fcreplay.instance.Replay')
    def test_noreplay(self, mock_replay, mock_config, mock_time):
        with pytest.raises(SystemExit) as e:
            mock_replay().replay = None
            temp_dir = tempfile.TemporaryDirectory()

            instance = self.setUp()
            instance.config = {'fcreplay_dir': temp_dir.name, 'fcadefbneo_path': temp_dir.name, 'upload_to_ia': False}
            instance.debug = True

            instance.main()

            assert mock_replay.add_job.not_called, "Shouldn't process a replay when none is returned"
            assert e.type == SystemExit, "Should exit no errors"

        with pytest.raises(SystemExit) as e:
            temp_dir = tempfile.TemporaryDirectory()

            instance = Instance()
            instance.config = {'fcreplay_dir': temp_dir.name, 'fcadefbneo_path': temp_dir.name}

            instance.debug = True
            instance.main()

            assert e.type == SystemExit, "Should exit no errors"

        with pytest.raises(SystemExit) as e:
            temp_dir = tempfile.TemporaryDirectory()

            instance = Instance()
            instance.config = {'fcreplay_dir': temp_dir.name, 'fcadefbneo_path': temp_dir.name}

            instance.debug = True
            instance.main()

            assert e.type == SystemExit, "Should exit no errors"

    @patch('fcreplay.instance.Config')
    @patch('fcreplay.instance.Replay', )
    def test_ia(self, mock_replay, mock_config):
        with pytest.raises(SystemExit) as e:
            temp_dir = tempfile.TemporaryDirectory()
            instance = Instance()
            instance.config = {'upload_to_ia': True, 'upload_to_yt': False, 'remove_generated_files': False, 'fcreplay_dir': temp_dir.name, 'fcadefbneo_path': temp_dir.name}
            instance.debug = True

            instance.main()

            assert mock_replay.upload_to_ia.called, "Should upload to IA when upload_to_ia is true"
            assert e.type == SystemExit, "Should exit no errors"

    @patch('fcreplay.instance.Config')
    @patch('fcreplay.instance.Replay')
    def test_youtube(self, mock_replay, mock_config):
        with pytest.raises(SystemExit) as e:
            temp_dir = tempfile.TemporaryDirectory()
            instance = Instance()
            instance.config = {'upload_to_ia': False, 'upload_to_yt': True, 'remove_generated_files': False, 'fcreplay_dir': temp_dir.name, 'fcadefbneo_path': temp_dir.name}
            instance.debug = True

            instance.main()

            assert mock_replay.upload_to_yt.called, "Should upload to YT when upload_to_yt is true"
            assert e.type == SystemExit, "Should exit with no errors"

    @patch('fcreplay.instance.Config')
    @patch('fcreplay.instance.Replay', )
    def test_remove_files(self, mock_replay, mock_config):
        with pytest.raises(SystemExit) as e:
            temp_dir = tempfile.TemporaryDirectory()
            instance = Instance()
            instance.config = {'upload_to_ia': False, 'upload_to_yt': False, 'remove_generated_files': True, 'fcreplay_dir': temp_dir.name, 'fcadefbneo_path': temp_dir.name}
            instance.debug = True

            instance.main()

            assert mock_replay.remove_generated_files.called, "Should remove generated files when remove_generated_files is true"
            assert e.type == SystemExit, "Should exit with no errors"

    @patch('fcreplay.instance.Config')
    @patch('fcreplay.instance.Replay')
    def test_instance(self, mock_replay, mock_config):
        with pytest.raises(SystemExit) as e:
            temp_dir = tempfile.TemporaryDirectory()
            mock_replay.replay.return_value = True

            instance = Instance()

            instance.config = {'upload_to_ia': False, 'upload_to_yt': False, 'remove_generated_files': False, 'fcreplay_dir': temp_dir.name, 'fcadefbneo_path': temp_dir.name}
            instance.debug = True

            instance.main()

            assert mock_replay.add_job.called
            assert e.type == SystemExit, "Should exit with no errors"

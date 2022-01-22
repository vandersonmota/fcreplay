import datetime
import os
import sys
import tempfile
from unittest.mock import patch, MagicMock

sys.modules['pyautogui'] = MagicMock()
from fcreplay.replay import Replay

# Note for future self: decorator @handle_fail does a kill_all if
# config['kill_all'] is set


class TestReplay:
    @patch('fcreplay.replay.Database')
    @patch('fcreplay.replay.Config')
    def test_get_resolution(self, mock_config, mock_database):
        r = Replay()
        desired_resolution = r.get_resolution(
            aspect_ratio=[4, 3],
            video_resolution=[1920, 1080]
        )

        assert isinstance(desired_resolution, list), "Returned value is not a list"

    @patch('fcreplay.replay.Database')
    @patch('fcreplay.replay.Config')
    def test_description_and_tags_no_chars_no_append(self, mock_config, mock_database):
        """Test description is created with tags."""
        r = Replay()
        r.replay.id = '1234567890'
        r.replay.game = '2020bb'
        r.replay.date_replay = datetime.datetime.now()
        r.replay.p1 = 'P1'
        r.replay.p2 = 'P2'
        r.replay.p1_loc = 'L1'
        r.replay.p2_loc = 'L2'
        r.detected_characters = []
        r.config.description_append_file = [False]

        expected_tags = [
            f"#{r.replay.p1}",
            f"#{r.replay.p2}",
            f"#{r.replay.game}",
        ]

        assert r.set_description(), 'Description should be set without characters or appended text'
        assert all(tag in r.description_text for tag in expected_tags), 'Expected tags should be in generated description'
        assert r.db.add_description.called, 'Database should be called to add description'
        assert f"({r.replay.p1_loc}) {r.replay.p1} vs " \
               f"({r.replay.p2_loc}) {r.replay.p2} - {r.replay.date_replay}" \
               f"\nFightcade replay id: {r.replay.id}" in r.description_text, 'Expected description should be in generated description'

        r.config.description_append_file = [True, '/does/not/exist']
        assert not r.set_description(), 'Description should fail when description append is set to true, but not file is configured'

    @patch('fcreplay.replay.Database')
    @patch('fcreplay.replay.Config')
    def test_description_and_tags_and_chars_and_append(self, mock_config, mock_database):
        """Test description is created with tags."""
        r = Replay()
        r.replay.id = '1234567890'
        r.replay.game = '2020bb'
        r.replay.date_replay = datetime.datetime.now()
        r.replay.p1 = 'P1'
        r.replay.p2 = 'P2'
        r.replay.p1_loc = 'L1'
        r.replay.p2_loc = 'L2'
        r.detected_characters = [
            ['0:05', 'C1', 'C2'],
            ['1:00', 'C3', 'C2']
        ]

        expected_tags = [
            f"#{r.replay.p1}",
            f"#{r.replay.p2}",
            f"#{r.replay.game}",
            f"#{r.detected_characters[0][1]}",
            f"#{r.detected_characters[0][2]}",
            f"#{r.detected_characters[1][1]}",
        ]

        with tempfile.NamedTemporaryFile() as f:
            r.config.description_append_file = [True, f.name]

            append_contents = 'SomeAppendedText'
            f.write(append_contents.encode())

            assert r.set_description(), 'Description should be set without characters or appended text'
            assert all(tag in r.description_text for tag in expected_tags), 'Expected tags should be in generated description'

    @patch('fcreplay.replay.subprocess')
    @patch('fcreplay.replay.Database')
    @patch('fcreplay.replay.Config')
    def test_encode(self, mock_config, mock_database, mock_subprocess):
        r = Replay()
        r.replay.game = '2020bb'
        r.config.resolution = [1920, 1080]

        with tempfile.TemporaryDirectory() as single_file_dir:
            os.mkdir(f"{single_file_dir}/avi")
            open(f"{single_file_dir}/avi/test_0.avi", "w")

            r.config.fcadefbneo_path = single_file_dir
            r.encode()

            mock_subprocess.run.assert_called(), 'Single file should call encoder'

        with tempfile.TemporaryDirectory() as multi_file_dir:
            os.mkdir(f"{multi_file_dir}/avi")
            for i in range(0, 3):
                open(f"{multi_file_dir}/avi/test_{i}.avi", "w")

            r.config.fcadefbneo_path = multi_file_dir
            r.encode()
            mock_subprocess.run.assert_called(), 'Multi file sould call encoder'

        with tempfile.TemporaryDirectory() as multi_file_dir:
            os.mkdir(f"{multi_file_dir}/avi")
            for i in range(0, 3):
                open(f"{multi_file_dir}/avi/_foo_bar_{i}.avi", "w")

            r.config.fcadefbneo_path = multi_file_dir
            r.encode()
            mock_subprocess.run.assert_called(), 'Multifile with underscores should call encoder'

    @patch('fcreplay.replay.subprocess')
    @patch('fcreplay.replay.Database')
    @patch('fcreplay.replay.Config')
    def test_sort(self, mock_config, mock_database, mock_subprocess):
        r = Replay()

        r.config.fcadefbneo_path = 'dir'

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
            "dir/avi/foo_bar_0.avi",
            "dir/avi/foo_bar_1.avi",
            "dir/avi/foo_bar_2.avi",
            "dir/avi/foo_bar_9.avi",
            "dir/avi/foo_bar_A.avi",
            "dir/avi/foo_bar_F.avi",
            "dir/avi/foo_bar_10.avi",
            "dir/avi/foo_bar_1A.avi",
            "dir/avi/foo_bar_2B.avi",
        ]

        sorted_list = r.sort_files(unsorted_list)

        assert sorted_list == good_list, 'List with hex characters should be sorted'

        single_list = [
            'foo_bar_0.avi'
        ]

        good_list = [
            'dir/avi/foo_bar_0.avi'
        ]

        sorted_list = r.sort_files(single_list)
        assert sorted_list == good_list, 'List with single file should be sorted'

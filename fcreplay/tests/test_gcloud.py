import pytest
import sys
from unittest.mock import patch, mock_open, MagicMock

sys.modules['pyautogui'] = MagicMock()
from fcreplay.gcloud import Gcloud


class TestGcloud:
    @patch('fcreplay.gcloud.Database')
    @patch('fcreplay.gcloud.Config')
    def setUp(self, mock_config, mock_Database):
        gcloud = Gcloud()
        gcloud.config = {
            "gcloud_compute_service_account": "test",
            "gcloud_shutdown_instance": False
        }
        return gcloud

    @patch('fcreplay.gcloud.Path')
    def test_dont_destroy(self, mock_path):
        gcloud = self.setUp()

        mock_path.side_effect = FileExistsError
        with pytest.raises(SystemExit) as e:
            gcloud.destroy_fcreplay()
            assert e.type == SystemExit, 'Should exit when file exists'

    @patch('fcreplay.gcloud.Logging')
    @patch('fcreplay.gcloud.Path')
    @patch('fcreplay.gcloud.socket')
    def test_not_image(self, mock_socket, mock_path, mock_logging):
        gcloud = self.setUp()
        mock_socket.get_hostname.return_value = 'Not an fcreplay image'
        assert gcloud.destroy_fcreplay() is False, "Should return false when hostname doesn't match 'fcreplay-image-'"

    @patch('fcreplay.gcloud.subprocess')
    @patch('fcreplay.gcloud.requests')
    @patch('fcreplay.gcloud.Database')
    @patch('fcreplay.gcloud.Logging')
    @patch('fcreplay.gcloud.Path')
    @patch('fcreplay.gcloud.socket')
    def test_destroy(self, mock_socket, mock_path, mock_logging, mock_database, mock_requests, mock_subprocess):
        gcloud = self.setUp()

        mock_socket.gethostname.return_value = 'fcreplay-image-testsuit'

        with patch("builtins.open", mock_open(read_data="1234 UPLOADING_TO_IA")) as mock_file:
            gcloud.destroy_fcreplay()

            mock_file.assert_called_with('/tmp/fcreplay_status', 'r'), "Should try and read fcreplay_status"
            mock_logging().error.assert_called_with('Not able to safely recover replay 1234'), "Should log error"
            mock_requests.post.assert_called(), "Should call post to destroy instance"
            mock_subprocess.run.assert_not_called(), "Should not shutdown instance"

        with patch("builtins.open", mock_open(read_data="1234 RETRY")) as mock_file:
            gcloud.destroy_fcreplay()

            mock_database().rerecord_replay.assert_called, "Should call rerecord when possible"
            mock_requests.post.assert_called(), "Should call post to destroy instance"
            mock_subprocess.run.assert_not_called(), "Should not shutdown instance"

        with patch("builtins.open", mock_open(read_data="1234 FileNotFoundError")) as mock_file:
            mock_file.side_effect = FileNotFoundError
            gcloud.destroy_fcreplay()

            mock_logging().error.assert_called_with('/tmp/fcreplay_status not found')
            mock_requests.post.assert_called(), "Should call post to destroy instance"
            mock_subprocess.run.assert_not_called(), "Should not shutdown instance"

        gcloud.config['gcloud_shutdown_instance'] = True
        gcloud.destroy_fcreplay()

        mock_requests.post.assert_called(), "Should call post to destroy instance"
        mock_subprocess.run.assert_called_with(['sudo', '/usr/sbin/shutdown', 'now', '-h']), "Should shutdown instance"

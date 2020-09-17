from unittest.mock import MagicMock
import mock
import sys

from fcreplay.tests.datadir import datadir

# Set Config
import os


def test_init(request):
    os.environ['FCREPLAY_CONFIG'] = str(datadir(request, 'config_good.json'))
    sys.modules['pyautogui'] = MagicMock()
    sys.modules['fcreplay.database'] = MagicMock()

    from fcreplay.replay import Replay
    with mock.patch('fcreplay.replay.Replay.get_replay') as mock_get_replay:
        replay = Replay()
        mock_get_replay.assert_called()
from unittest.mock import MagicMock
from mock import mock, patch
import os
import sys


class TestReplay:
    def setUp(self, request):
        from fcreplay.tests.datadir import datadir
        os.environ['FCREPLAY_CONFIG'] = str(datadir(request, 'config_good.json'))
        sys.modules['fcreplay.database'] = MagicMock()
        sys.modules['pyautogui'] = MagicMock()

    def test_init(self, request):
        self.setUp(request)
        from fcreplay.replay import Replay

        with mock.patch('fcreplay.replay.Replay.get_replay') as mock_get_replay:
            replay = Replay()
            mock_get_replay.assert_called()

    def test_get_replay(self, request):
        self.setUp(request)
        from fcreplay.replay import Replay
        replay = Replay()

        #Assert return replay
        #Assert return none when no replays
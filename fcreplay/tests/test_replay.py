from unittest.mock import MagicMock
import pytest
import sys

from fcreplay.tests.datadir import datadir

# Set Config
import os


def test_init_started(request):
    os.environ['FCREPLAY_CONFIG'] = str(datadir(request, 'config_good.json'))
    sys.modules['pyautogui'] = MagicMock()
    sys.modules['fcreplay.database'] = MagicMock()

    from fcreplay.replay import Replay
    replay = Replay()

    assert(os.path.exists('/tmp/fcreplay_status'))


def test_update_status(request):
    os.environ['FCREPLAY_CONFIG'] = str(datadir(request, 'config_good.json'))
    sys.modules['pyautogui'] = MagicMock()
    sys.modules['fcreplay.database'] = MagicMock()

    from fcreplay.replay import Replay
    replay = Replay()

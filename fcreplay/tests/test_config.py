import pytest

from json import JSONDecodeError
from fcreplay.config import Config
from fcreplay.tests.datadir import datadir

import os


def test_validjson(request):
    os.environ['FCREPLAY_CONFIG'] = datadir(request, 'config_good.json')
    config = Config().config
    assert type(config) is dict, "Should be dict"


def test_invalidjson(request):
    os.environ['FCREPLAY_CONFIG'] = datadir(request, 'config_bad.json')
    with pytest.raises(JSONDecodeError):
        Config().config
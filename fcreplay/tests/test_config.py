import pytest
import tempfile

from json import JSONDecodeError
from fcreplay.config import Config
from fcreplay.tests.datadir import datadir

import os


def test_valid_json(request):
    os.environ['FCREPLAY_CONFIG'] = datadir(request, 'config_good.json')
    config = Config().config
    assert type(config) is dict, "Should be dict"


def test_invalid_json(request):
    os.environ['FCREPLAY_CONFIG'] = datadir(request, 'config_bad.json')
    with pytest.raises(JSONDecodeError):
        Config().config


def test_empty_json(request):
    os.environ['FCREPLAY_CONFIG'] = datadir(request, 'config_empty.json')
    with pytest.raises(SystemExit) as e:
        Config().config
        assert e.type == SystemExit, "Should exit when file isn't valid"


def test_file_not_found(request):
    temp_config = tempfile._get_default_tempdir() + '/' + next(tempfile._get_candidate_names())
    os.environ['FCREPLAY_CONFIG'] = temp_config
    with pytest.raises(SystemExit) as e:
        Config().config
        assert e.type == SystemExit, "Should exit when file doesn't exist"

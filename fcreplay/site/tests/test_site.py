import pytest
import os
os.environ['FCREPLAY_CONFIG'] = './fcreplay/site/tests/config_test_site.json'


class TestSite:
    def setUp(self):
        from fcreplay.config import Config
        config = Config().config
        return config

    def test_site(self):
        assert self.setUp() is False 
from fcreplay.site.create_app import create_app
from fcreplay.site.site_config import DevConfig, ProdConfig


class TestConfig:
    def test_production_config(self):
        """Production config."""
        app = create_app(ProdConfig)
        assert app.config['ENV'] == 'prod'
        assert not app.config['DEBUG']

    def test_dev_config(self):
        """Development config."""
        app = create_app(DevConfig)
        assert app.config['ENV'] == 'dev'
        assert app.config['DEBUG']
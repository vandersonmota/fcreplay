from fcreplay.site.create_app import create_app
from fcreplay.site.site_config import DevConfig, ProdConfig
from flask.helpers import get_debug_flag, get_env

if get_debug_flag() or get_env != "production":
    CONFIG = DevConfig
else:
    CONFIG = ProdConfig
    try:
        import googleclouddebugger
        googleclouddebugger.enable(
            breakpoint_enable_canary=True
        )
    except ImportError:
        pass

app = create_app(CONFIG)

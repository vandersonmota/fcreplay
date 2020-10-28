from fcreplay.site.create_app import create_app
from fcreplay.site.site_config import DevConfig, ProdConfig
from flask.helpers import get_debug_flag

if get_debug_flag():
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

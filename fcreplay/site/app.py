from fcreplay.site.create_app import create_app
from fcreplay.site.site_config import Config
from flask.helpers import get_debug_flag

if not get_debug_flag():
    try:
        import googleclouddebugger
        googleclouddebugger.enable(
            breakpoint_enable_canary=True
        )
    except ImportError:
        pass

app = create_app(Config)

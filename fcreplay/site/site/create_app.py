from flask import Flask
from flask_bootstrap import Bootstrap
from flask_cors import CORS

from fcreplay.site.site.site_filters import convertLength, linkPath
from fcreplay.site.site import routes as site_routes

import os

def create_app(app_config):
    if 'REMOTE_DEBUG' in os.environ:
        import debugpy
        debugpy.listen(("0.0.0.0", 5678))
        debugpy.wait_for_client()

    try:
        import googleclouddebugger
        googleclouddebugger.enable(
            breakpoint_enable_canary=True
        )
    except ImportError:
        pass

    app = Flask(__name__, static_folder='static')
    app.config.from_object(app_config)

    Bootstrap(app)
    app_filters(app)
    cors(app)
    routes(app)

    return app


def app_filters(app):
    app.jinja_env.filters['convertLenth'] = convertLength
    app.jinja_env.filters['linkPath'] = linkPath


def cors(app):
    cors = CORS(app, resources={r"/api/*": {"origins": "*"}})


def routes(app):
    app.add_url_rule('/', 'index', view_func=site_routes.index)
    app.add_url_rule('/api/videolinks', 'videolinks', view_func=site_routes.videolinks, methods=['POST'])
    app.add_url_rule('/api/supportedgames', 'supportedgames', view_func=site_routes.supportedgames)
    app.add_url_rule('/submit', 'submit', view_func=site_routes.submit)
    app.add_url_rule('/submitResult', 'submitResult', view_func=site_routes.submitResult, methods=['POST', 'GET'])
    app.add_url_rule('/assets/<path:path>', 'send_js', view_func=site_routes.send_js)
    app.add_url_rule('/about', 'about', view_func=site_routes.about)
    app.add_url_rule('/advancedSearch', 'advancedsearch', view_func=site_routes.advancedSearch)
    app.add_url_rule('/advancedSearchResult', 'advancedSearchResult', view_func=site_routes.advancedSearchResult, methods=['POST', 'GET'])
    app.add_url_rule('/search', 'search', view_func=site_routes.search, metods=['POST', 'GET'])
    app.add_url_rule('/robots', 'robots', view_func=site_routes.robots)
    app.add_url_rule('/ads', 'ads', view_func=site_routes.robots)
    app.add_url_rule('/sitemap.xml', 'sitemap', view_func=site_routes.sitemap)
    app.add_url_rule('/view/<challenge_id>', 'videopage', view_func=site_routes.videopage)


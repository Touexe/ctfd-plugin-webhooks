from CTFd.plugins import register_plugin_assets_directory

from .api import register_api
from .events import register_event_listeners
from .models import ensure_webhook_schema


def load(app):
    register_api(app)
    register_event_listeners(app)
    register_plugin_assets_directory(
        app, base_path="/plugins/ctfd-plugin-webhooks/assets/"
    )

    with app.app_context():
        ensure_webhook_schema()
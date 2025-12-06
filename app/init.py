from flask import Flask
from .config import Config
from .routes import bp


def create_app():
    app = Flask(
        __name__,
        template_folder=Config.TEMPLATE_DIR,
        static_folder=Config.STATIC_DIR
    )

    app.config.from_object(Config)

    # registra blueprint
    app.register_blueprint(bp)

    return app

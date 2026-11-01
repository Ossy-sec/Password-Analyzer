"""
Application factory. Serves the static frontend/ folder AND the JSON API
from the same Flask process, so the whole app is a single command
(`python app.py`) on a single origin — no CORS configuration needed.
"""

from pathlib import Path

from flask import Flask, send_from_directory

from config import Config
from db import init_db, register_app

FRONTEND_DIR = Path(__file__).resolve().parent.parent / "frontend"


def create_app(config_class=Config):
    app = Flask(__name__, static_folder=str(FRONTEND_DIR), static_url_path="")
    app.config.from_object(config_class)

    register_app(app)

    from routes.auth import bp as auth_bp
    from routes.password import bp as password_bp

    app.register_blueprint(auth_bp)
    app.register_blueprint(password_bp)

    @app.get("/")
    def index():
        return send_from_directory(FRONTEND_DIR, "index.html")

    @app.errorhandler(404)
    def not_found(_error):
        return {"error": "Not found"}, 404

    @app.errorhandler(500)
    def server_error(_error):
        # Never leak stack traces / internals to the client.
        return {"error": "Internal server error"}, 500

    return app


if __name__ == "__main__":
    app = create_app()
    if app.config["SECRET_KEY"] == "dev-secret-change-me":
        print(
            "WARNING: using the default SECRET_KEY. Set SECRET_KEY in backend/.env "
            "before running this anywhere other than your own machine."
        )
    init_db(app)
    app.run(debug=app.config["DEBUG"], port=5000)

import os

from flask import Flask
from sqlalchemy import text

from app.extensions import cors, db, limiter, ma, migrate
from app.utils.error_handlers import register_error_handlers


def create_app(config_name=None):
    flask_app = Flask(__name__)

    config_name = config_name or os.getenv("FLASK_ENV", "development")
    from config import config_by_name

    flask_app.config.from_object(config_by_name[config_name])

    db.init_app(flask_app)
    migrate.init_app(flask_app, db)

    # Flask-CORS treats a string as one origin. Production configuration may
    # contain a comma-separated list, so normalize it to a real list before
    # passing it to Flask-CORS. Without this, browser POST/preflight requests
    # such as login can fail even though GET requests appear to work.
    configured_origins = flask_app.config.get("CORS_ORIGINS", "")
    if isinstance(configured_origins, str):
        allowed_origins = [
            origin.strip()
            for origin in configured_origins.split(",")
            if origin.strip()
        ]
    else:
        allowed_origins = list(configured_origins or [])

    cors.init_app(
        flask_app,
        resources={r"/api/*": {"origins": allowed_origins}},
        supports_credentials=False,
    )
    limiter.init_app(flask_app)
    ma.init_app(flask_app)

    # Do not use `import app.models` here: Python binds the package name
    # `app` in the local scope and can accidentally replace the Flask instance
    # with the Python package module. Keep the imported package private.
    from app import models as _models  # noqa: F401

    register_error_handlers(flask_app)

    from app.api.admin_routes import admin_bp
    from app.api.auth_routes import auth_bp
    from app.api.learning_routes import learning_bp
    from app.api.practice_routes import practice_bp
    from app.api.question_routes import admin_questions_bp

    flask_app.register_blueprint(auth_bp)
    flask_app.register_blueprint(admin_bp)
    flask_app.register_blueprint(admin_questions_bp)
    flask_app.register_blueprint(learning_bp)
    flask_app.register_blueprint(practice_bp)

    from app.api.exam_registration import register_exam_blueprints
    register_exam_blueprints(flask_app)

    @flask_app.route("/health")
    def health_check():
        """Liveness/readiness endpoint used by the hosting platform.

        A healthy application must be able to reach its configured database;
        otherwise returning HTTP 200 hides an outage from Render/load balancers.
        """
        try:
            db.session.execute(text("SELECT 1"))
            return {"status": "healthy", "database": "ok"}, 200
        except Exception:
            flask_app.logger.exception("Health check database probe failed")
            db.session.rollback()
            return {"status": "unhealthy", "database": "unavailable"}, 503

    return flask_app

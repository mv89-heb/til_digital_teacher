import os

from flask import Flask, jsonify, request
from sqlalchemy import text

from app.extensions import cors, db, limiter, ma, migrate
from app.utils.error_handlers import register_error_handlers


def create_app(config_name=None):
    flask_app = Flask(__name__)

    config_name = config_name or os.getenv("FLASK_ENV", "production")
    from config import config_by_name

    flask_app.config.from_object(config_by_name[config_name])

    db.init_app(flask_app)
    migrate.init_app(flask_app, db)

    configured_origins = flask_app.config.get("CORS_ORIGINS", "")
    if isinstance(configured_origins, str):
        allowed_origins = {
            origin.strip()
            for origin in configured_origins.split(",")
            if origin.strip()
        }
    else:
        allowed_origins = set(configured_origins or [])

    cors.init_app(
        flask_app,
        resources={r"/api/.*": {"origins": list(allowed_origins)}},
        supports_credentials=False,
    )

    @flask_app.before_request
    def handle_api_preflight():
        """Answer API CORS preflight requests explicitly and consistently."""
        if request.method != "OPTIONS" or not request.path.startswith("/api/"):
            return None

        origin = request.headers.get("Origin")
        if origin and origin not in allowed_origins:
            return jsonify({"error": "CORS origin not allowed"}), 403

        response = flask_app.make_response(("", 204))
        if origin:
            response.headers["Access-Control-Allow-Origin"] = origin
            response.headers["Vary"] = "Origin"
        response.headers["Access-Control-Allow-Methods"] = "GET, POST, PUT, PATCH, DELETE, OPTIONS"
        response.headers["Access-Control-Allow-Headers"] = request.headers.get(
            "Access-Control-Request-Headers",
            "Authorization, Content-Type",
        )
        response.headers["Access-Control-Max-Age"] = "600"
        return response

    @flask_app.after_request
    def add_api_cors_headers(response):
        """Ensure API responses expose CORS headers, including error responses."""
        if not request.path.startswith("/api/"):
            return response

        origin = request.headers.get("Origin")
        if origin and origin in allowed_origins:
            response.headers["Access-Control-Allow-Origin"] = origin
            response.headers["Vary"] = "Origin"
            response.headers["Access-Control-Allow-Methods"] = "GET, POST, PUT, PATCH, DELETE, OPTIONS"
            response.headers["Access-Control-Allow-Headers"] = "Authorization, Content-Type"
        return response

    limiter.init_app(flask_app)
    ma.init_app(flask_app)

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
        """Liveness/readiness endpoint used by the hosting platform."""
        try:
            db.session.execute(text("SELECT 1"))
            return {"status": "healthy", "database": "ok"}, 200
        except Exception:
            flask_app.logger.exception("Health check database probe failed")
            db.session.rollback()
            return {"status": "unhealthy", "database": "unavailable"}, 503

    return flask_app

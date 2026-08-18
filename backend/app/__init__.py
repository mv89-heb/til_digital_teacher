import os

from flask import Flask
from sqlalchemy import text

from app.extensions import cors, db, limiter, ma, migrate
from app.utils.error_handlers import register_error_handlers


def create_app(config_name=None):
    app = Flask(__name__)

    config_name = config_name or os.getenv("FLASK_ENV", "development")
    from config import config_by_name

    app.config.from_object(config_by_name[config_name])

    db.init_app(app)
    migrate.init_app(app, db)
    cors.init_app(
        app,
        resources={r"/api/*": {"origins": app.config["CORS_ORIGINS"]}},
        supports_credentials=False,
    )
    limiter.init_app(app)
    ma.init_app(app)

    import app.models  # noqa: F401

    register_error_handlers(app)

    from app.api.admin_routes import admin_bp
    from app.api.auth_routes import auth_bp
    from app.api.learning_routes import learning_bp
    from app.api.practice_routes import practice_bp
    from app.api.question_routes import admin_questions_bp

    app.register_blueprint(auth_bp)
    app.register_blueprint(admin_bp)
    app.register_blueprint(admin_questions_bp)
    app.register_blueprint(learning_bp)
    app.register_blueprint(practice_bp)

    from app.api.exam_registration import register_exam_blueprints
    register_exam_blueprints(app)

    @app.route("/health")
    def health_check():
        """Liveness/readiness endpoint used by the hosting platform.

        A healthy application must be able to reach its configured database;
        otherwise returning HTTP 200 hides an outage from Render/load balancers.
        """
        try:
            db.session.execute(text("SELECT 1"))
            return {"status": "healthy", "database": "ok"}, 200
        except Exception:
            app.logger.exception("Health check database probe failed")
            return {"status": "unhealthy", "database": "unavailable"}, 503

    return app

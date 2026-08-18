import os

from flask import Flask

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

    # Import every model so Flask-Migrate sees the complete metadata.
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

    # Advanced exam engine and content-integrity APIs.
    from app.api.exam_registration import register_exam_blueprints
    register_exam_blueprints(app)

    @app.route("/health")
    def health_check():
        return {"status": "healthy"}

    return app

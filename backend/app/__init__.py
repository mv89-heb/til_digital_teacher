import os

from flask import Flask

from app.extensions import cors, db, ma, migrate
from app.utils.error_handlers import register_error_handlers


def create_app(config_name=None):
    app = Flask(__name__)

    config_name = config_name or os.getenv("FLASK_ENV", "development")
    from config import config_by_name

    app.config.from_object(config_by_name[config_name])

    db.init_app(app)
    migrate.init_app(app, db)
    cors.init_app(app)
    ma.init_app(app)

    # Import models so Flask-Migrate can see them when generating migrations.
    from app.models.answer import Answer  # noqa: F401
    from app.models.audit_log import AuditLog  # noqa: F401
    from app.models.category import Category  # noqa: F401
    from app.models.lesson import Lesson  # noqa: F401
    from app.models.lesson_content import LessonContent  # noqa: F401
    from app.models.practice_attempt import PracticeAttempt  # noqa: F401
    from app.models.question import Question  # noqa: F401
    from app.models.solution_strategy import SolutionStrategy  # noqa: F401
    from app.models.student_level import StudentLevel  # noqa: F401
    from app.models.user import User  # noqa: F401
    from app.models.user_lesson_progress import UserLessonProgress  # noqa: F401
    from app.models.user_progress import UserProgress  # noqa: F401
    from app.models.xp_transaction import XPTransaction  # noqa: F401

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

    @app.route("/health")
    def health_check():
        return {"status": "healthy"}

    return app

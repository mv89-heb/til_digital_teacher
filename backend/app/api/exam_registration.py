"""Centralized registration for the exam-related blueprints.

Import and call register_exam_blueprints(app) from the application factory.
Keeping registration here avoids circular imports in the factory.
"""


def register_exam_blueprints(app):
    from app.api.exam_routes import exam_bp
    from app.api.exam_admin_routes import exam_admin_bp
    from app.api.exam_health_routes import exam_health_bp

    app.register_blueprint(exam_bp)
    app.register_blueprint(exam_admin_bp)
    app.register_blueprint(exam_health_bp)

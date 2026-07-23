from flask import jsonify
from marshmallow import ValidationError
from werkzeug.exceptions import HTTPException

from app.utils.exceptions import AppError


def register_error_handlers(app):
    """Register a single, consistent JSON error format for the whole app.

    Routes should raise AppError(message, status_code) for expected
    business-logic failures (e.g. "email already exists" -> 409) and let
    everything else bubble up here. No route should catch a bare Exception.
    """

    @app.errorhandler(ValidationError)
    def handle_validation_error(err):
        return jsonify({"error": "Validation failed", "details": err.messages}), 422

    @app.errorhandler(AppError)
    def handle_app_error(err):
        return jsonify({"error": err.message}), err.status_code

    @app.errorhandler(ValueError)
    def handle_value_error(err):
        return jsonify({"error": str(err)}), 400

    @app.errorhandler(404)
    def handle_not_found(err):
        return jsonify({"error": "Resource not found"}), 404

    @app.errorhandler(HTTPException)
    def handle_http_exception(err):
        return jsonify({"error": err.description}), err.code

    @app.errorhandler(Exception)
    def handle_unexpected_error(err):
        app.logger.exception("Unhandled exception")
        return jsonify({"error": "Internal server error"}), 500

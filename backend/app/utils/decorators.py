from functools import wraps

from flask import g, jsonify, request

from app.services.auth_service import AuthService
from app.utils.exceptions import AppError


def jwt_required(fn):
    """Require a valid Bearer token; makes the user available as g.current_user."""

    @wraps(fn)
    def wrapper(*args, **kwargs):
        auth_header = request.headers.get("Authorization", "")
        if not auth_header.startswith("Bearer "):
            return jsonify({"error": "Missing authorization token"}), 401

        token = auth_header.split(" ", 1)[1]
        try:
            g.current_user = AuthService.verify_token(token)
        except AppError as err:
            return jsonify({"error": err.message}), err.status_code

        return fn(*args, **kwargs)

    return wrapper


def admin_required(fn):
    """Require a valid token AND role == 'admin'. Always stack under jwt_required."""

    @wraps(fn)
    @jwt_required
    def wrapper(*args, **kwargs):
        if g.current_user.get("role") != "admin":
            return jsonify({"error": "Admin access required"}), 403
        return fn(*args, **kwargs)

    return wrapper

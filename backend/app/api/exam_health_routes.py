from flask import Blueprint, jsonify
from sqlalchemy import text

from app.extensions import db

exam_health_bp = Blueprint("exam_health", __name__, url_prefix="/api")


@exam_health_bp.route("/health", methods=["GET"])
def health():
    try:
        db.session.execute(text("SELECT 1"))
        return jsonify({"status": "ok", "database": "ok"}), 200
    except Exception:
        db.session.rollback()
        return jsonify({"status": "unhealthy", "database": "unavailable"}), 503

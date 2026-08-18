from flask import Blueprint, jsonify

from app.extensions import db

exam_health_bp = Blueprint("exam_health", __name__, url_prefix="/api")


@exam_health_bp.route("/health", methods=["GET"])
def health():
    db.session.execute(db.text("SELECT 1"))
    return jsonify({"status": "ok"}), 200

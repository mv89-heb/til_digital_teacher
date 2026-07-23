from flask import Blueprint, g, jsonify, request

from app.schemas.practice_schema import submit_answer_schema
from app.services.practice_service import PracticeService
from app.services.progress_service import ProgressService
from app.utils.decorators import jwt_required

practice_bp = Blueprint("practice", __name__, url_prefix="/api/learning")


@practice_bp.route("/questions/<int:question_id>/submit", methods=["POST"])
@jwt_required
def submit_answer(question_id):
    data = submit_answer_schema.load(request.get_json() or {})
    result = PracticeService.submit_answer(g.current_user["id"], question_id, data["answer_id"])
    return jsonify(result), 200


@practice_bp.route("/lessons/<int:lesson_id>/complete", methods=["POST"])
@jwt_required
def complete_lesson(lesson_id):
    progress = PracticeService.complete_lesson(g.current_user["id"], lesson_id)
    return jsonify({"progress": progress}), 200


@practice_bp.route("/lessons/<int:lesson_id>/progress", methods=["GET"])
@jwt_required
def get_lesson_progress(lesson_id):
    progress = PracticeService.get_lesson_progress(g.current_user["id"], lesson_id)
    return jsonify({"progress": progress}), 200


@practice_bp.route("/dashboard", methods=["GET"])
@jwt_required
def get_dashboard():
    summary = ProgressService.get_dashboard_summary(g.current_user["id"])
    return jsonify(summary), 200

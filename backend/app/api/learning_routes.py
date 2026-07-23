from flask import Blueprint, g, jsonify, request

from app.schemas.practice_schema import submit_answer_schema
from app.services.learning_service import LearningService
from app.services.practice_service import PracticeService
from app.utils.decorators import jwt_required

learning_bp = Blueprint("learning", __name__, url_prefix="/api/learning")


@learning_bp.route("/categories", methods=["GET"])
def get_categories():
    return jsonify({"categories": LearningService.get_categories_overview()}), 200


@learning_bp.route("/lessons/<int:lesson_id>", methods=["GET"])
def get_lesson(lesson_id):
    lesson = LearningService.get_lesson_detail(lesson_id)
    return jsonify({"lesson": lesson}), 200


@learning_bp.route("/questions/<int:question_id>/submit", methods=["POST"])
@jwt_required
def submit_answer(question_id):
    data = submit_answer_schema.load(request.get_json() or {})
    result = PracticeService.submit_answer(g.current_user["id"], question_id, data["answer_id"])
    return jsonify(result), 200


@learning_bp.route("/lessons/<int:lesson_id>/complete", methods=["POST"])
@jwt_required
def complete_lesson(lesson_id):
    progress = PracticeService.complete_lesson(g.current_user["id"], lesson_id)
    return jsonify({"progress": progress}), 200


@learning_bp.route("/lessons/<int:lesson_id>/progress", methods=["GET"])
@jwt_required
def get_lesson_progress(lesson_id):
    progress = PracticeService.get_lesson_progress(g.current_user["id"], lesson_id)
    return jsonify({"progress": progress}), 200

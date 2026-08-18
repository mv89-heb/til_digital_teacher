from flask import Blueprint, g, jsonify, request

from app.schemas.practice_schema import submit_answer_schema
from app.services.learning_service import LearningService
from app.services.practice_service import PracticeService
from app.services.progress_service import ProgressService
from app.services.teacher_knowledge_service import TeacherKnowledgeService
from app.utils.decorators import jwt_required

learning_bp = Blueprint("learning", __name__, url_prefix="/api/learning")


@learning_bp.route("/categories", methods=["GET"])
def get_categories():
    return jsonify({"categories": LearningService.get_categories_overview()}), 200


@learning_bp.route("/dashboard", methods=["GET"])
@jwt_required
def get_dashboard():
    return jsonify(ProgressService.get_dashboard_summary(g.current_user["id"])), 200


@learning_bp.route("/lessons/<int:lesson_id>", methods=["GET"])
def get_lesson(lesson_id):
    lesson = LearningService.get_lesson_detail(lesson_id)
    return jsonify({"lesson": lesson}), 200


@learning_bp.route("/question-bank", methods=["GET"])
@jwt_required
def get_question_bank():
    return jsonify(
        PracticeService.list_question_bank(
            category_id=request.args.get("category_id", type=int),
            difficulty=request.args.get("difficulty"),
            page=request.args.get("page", default=1, type=int),
            per_page=request.args.get("per_page", default=24, type=int),
            search=request.args.get("search"),
        )
    ), 200


@learning_bp.route("/teacher/teach", methods=["POST"])
@jwt_required
def teacher_teach():
    payload = request.get_json(silent=True) or {}
    query = str(payload.get("query") or "").strip()
    question_id = payload.get("question_id")
    try:
        question_id = int(question_id) if question_id is not None else None
    except (TypeError, ValueError):
        question_id = None
    mode = str(payload.get("mode") or "learn")
    if not query and question_id is None:
        return jsonify({"error": "query or question_id is required"}), 400
    return jsonify(TeacherKnowledgeService.teach(query, question_id=question_id, mode=mode)), 200


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

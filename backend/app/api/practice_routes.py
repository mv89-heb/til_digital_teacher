from flask import Blueprint, g, jsonify, request

from app.schemas.practice_schema import submit_answer_schema
from app.services.adaptive_practice_service import AdaptivePracticeService
from app.services.practice_service import PracticeService
from app.services.progress_service import ProgressService
from app.utils.decorators import jwt_required

practice_bp = Blueprint("practice", __name__, url_prefix="/api/learning")


@practice_bp.route("/practice/questions", methods=["GET"])
@jwt_required
def list_practice_questions():
    limit = request.args.get("limit", default=10, type=int)
    category_id = request.args.get("category_id", type=int)
    difficulty = request.args.get("difficulty")
    mode = request.args.get("mode", default="adaptive")

    if mode == "adaptive":
        selected = AdaptivePracticeService.select(
            user_id=g.current_user["id"],
            category_id=category_id,
            difficulty=difficulty,
            limit=limit,
        )
        return jsonify({
            "questions": [PracticeService._public_question(question) for question in selected["questions"]],
            "count": len(selected["questions"]),
            "mode": "adaptive",
            "target": selected["target"],
            "profile": {
                "attempts_considered": selected["profile"]["attempts_considered"],
                "weakest_skill": selected["profile"]["weakest_skill"],
            },
        }), 200

    result = PracticeService.list_practice_questions(
        user_id=g.current_user["id"],
        category_id=category_id,
        difficulty=difficulty,
        limit=limit,
        mode=mode,
    )
    return jsonify(result), 200


@practice_bp.route("/practice/questions/<int:question_id>", methods=["GET"])
@jwt_required
def get_practice_question(question_id):
    return jsonify({"question": PracticeService.get_practice_question(question_id)}), 200


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

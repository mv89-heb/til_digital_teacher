from flask import Blueprint, g, jsonify, request

from app.schemas.question_schema import (
    answer_schema,
    answer_update_schema,
    question_schema,
    question_update_schema,
)
from app.services.question_service import QuestionService
from app.utils.decorators import admin_required

admin_questions_bp = Blueprint("admin_questions", __name__, url_prefix="/api/admin")


@admin_questions_bp.route("/questions", methods=["GET"])
@admin_required
def list_questions():
    category_id = request.args.get("category_id", type=int)
    lesson_id = request.args.get("lesson_id", type=int)
    return jsonify({"questions": QuestionService.list_questions(category_id, lesson_id)}), 200


@admin_questions_bp.route("/questions", methods=["POST"])
@admin_required
def create_question():
    data = question_schema.load(request.get_json() or {})
    question = QuestionService.create_question(data, g.current_user["id"])
    return jsonify({"question": question}), 201


@admin_questions_bp.route("/questions/<int:question_id>", methods=["GET"])
@admin_required
def get_question(question_id):
    question = QuestionService.get_question(question_id)
    return jsonify({"question": question.to_dict(reveal_answers=True)}), 200


@admin_questions_bp.route("/questions/<int:question_id>", methods=["PUT"])
@admin_required
def update_question(question_id):
    data = question_update_schema.load(request.get_json() or {})
    question = QuestionService.update_question(question_id, data, g.current_user["id"])
    return jsonify({"question": question}), 200


@admin_questions_bp.route("/questions/<int:question_id>", methods=["DELETE"])
@admin_required
def delete_question(question_id):
    QuestionService.delete_question(question_id, g.current_user["id"])
    return jsonify({"message": "Question deleted"}), 200


@admin_questions_bp.route("/questions/<int:question_id>/answers", methods=["POST"])
@admin_required
def add_answer(question_id):
    data = answer_schema.load(request.get_json() or {})
    answer = QuestionService.add_answer(question_id, data, g.current_user["id"])
    return jsonify({"answer": answer}), 201


@admin_questions_bp.route("/answers/<int:answer_id>", methods=["PUT"])
@admin_required
def update_answer(answer_id):
    data = answer_update_schema.load(request.get_json() or {})
    answer = QuestionService.update_answer(answer_id, data, g.current_user["id"])
    return jsonify({"answer": answer}), 200


@admin_questions_bp.route("/answers/<int:answer_id>", methods=["DELETE"])
@admin_required
def delete_answer(answer_id):
    QuestionService.delete_answer(answer_id, g.current_user["id"])
    return jsonify({"message": "Answer deleted"}), 200

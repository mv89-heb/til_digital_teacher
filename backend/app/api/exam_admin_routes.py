from flask import Blueprint, g, jsonify, request

from app.services.content_integrity_service import ContentIntegrityService
from app.services.exam_service import ExamService
from app.services.publish_service import PublishService
from app.utils.decorators import admin_required
from app.utils.exceptions import AppError

exam_admin_bp = Blueprint("exam_admin", __name__, url_prefix="/api/admin/content")


@exam_admin_bp.route("/validate", methods=["GET"])
@admin_required
def validate():
    return jsonify(ContentIntegrityService.validate_all()), 200


@exam_admin_bp.route("/questions/<int:question_id>/publish", methods=["POST"])
@admin_required
def publish_question(question_id):
    question = PublishService.publish_question(question_id)
    return jsonify({"question": question.to_dict(reveal_answers=True)}), 200


@exam_admin_bp.route("/lessons/<int:lesson_id>/publish", methods=["POST"])
@admin_required
def publish_lesson(lesson_id):
    lesson = PublishService.publish_lesson(lesson_id)
    return jsonify({"lesson": lesson.to_dict()}), 200


@exam_admin_bp.route("/exams", methods=["POST"])
@admin_required
def create_exam():
    data = request.get_json() or {}
    required = ("name", "duration_seconds", "sections")
    missing = [field for field in required if field not in data]
    if missing:
        raise AppError(f"Missing fields: {', '.join(missing)}", status_code=400)
    exam = ExamService.create_exam(g.current_user["id"], data)
    return jsonify({"exam": {
        "id": exam.id,
        "name": exam.name,
        "status": exam.status,
        "version": exam.version,
        "duration_seconds": exam.duration_seconds,
    }}), 201


@exam_admin_bp.route("/exams/<int:exam_id>/publish", methods=["POST"])
@admin_required
def publish_exam(exam_id):
    exam = ExamService.publish_exam(exam_id)
    return jsonify({"exam": {
        "id": exam.id,
        "name": exam.name,
        "status": exam.status,
        "version": exam.version,
        "duration_seconds": exam.duration_seconds,
    }}), 200

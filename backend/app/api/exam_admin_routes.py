from flask import Blueprint, g, jsonify

from app.services.content_integrity_service import ContentIntegrityService
from app.services.publish_service import PublishService
from app.utils.decorators import admin_required

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

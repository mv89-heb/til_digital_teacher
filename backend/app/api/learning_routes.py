from flask import Blueprint, g, jsonify, request

from app.schemas.practice_schema import submit_answer_schema
from app.services.learning_service import LearningService
from app.services.practice_service import PracticeService
from app.services.progress_service import ProgressService
from app.services.teacher_knowledge_service import TeacherKnowledgeService
from app.services.teacher_memory_service import TeacherMemoryService
from app.utils.decorators import admin_required, jwt_required

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

    result = TeacherKnowledgeService.teach(
        query,
        question_id=question_id,
        mode=mode,
    )

    topic = result.get("topic")
    question = result.get("question") or {}
    subcategory = question.get("subcategory")
    skill = question.get("skill")
    memory_items = TeacherMemoryService.retrieve(
        query=query,
        topic=topic,
        subcategory=subcategory,
        skill=skill,
        question_id=question_id,
        limit=8,
    )
    result["answer"] = TeacherMemoryService.apply_to_local_answer(
        result.get("answer") or "",
        memory_items,
        mode=mode,
    )
    result["memory"] = {
        "applied": bool(memory_items),
        "count": len(memory_items),
        "items": TeacherMemoryService.context(memory_items),
    }
    TeacherMemoryService.mark_used(memory_items)
    return jsonify(result), 200


@learning_bp.route("/teacher/feedback", methods=["POST"])
@jwt_required
def teacher_feedback():
    payload = request.get_json(silent=True) or {}
    try:
        item = TeacherMemoryService.record(
            user_id=g.current_user["id"],
            payload=payload,
        )
    except ValueError as exc:
        return jsonify({"error": str(exc)}), 400
    return jsonify({
        "message": "המשוב נשמר לבדיקה ויוכל להפוך לכלל הוראה לאחר אישור.",
        "feedback": item.to_dict(),
    }), 201


@learning_bp.route("/teacher/feedback", methods=["GET"])
@admin_required
def list_teacher_feedback():
    status = request.args.get("status", "pending")
    query = TeacherMemoryService.retrieve(query="", limit=20)
    if status != "approved":
        from app.models.teacher_feedback import TeacherFeedback
        query = (
            TeacherFeedback.query
            .filter(TeacherFeedback.status == status)
            .order_by(TeacherFeedback.created_at.desc())
            .limit(50)
            .all()
        )
    return jsonify({"feedback": [item.to_dict() for item in query]}), 200


@learning_bp.route("/teacher/feedback/<int:feedback_id>/review", methods=["POST"])
@admin_required
def review_teacher_feedback(feedback_id):
    payload = request.get_json(silent=True) or {}
    approved = bool(payload.get("approved"))
    confidence = payload.get("confidence")
    try:
        confidence = int(confidence) if confidence is not None else None
    except (TypeError, ValueError):
        confidence = None
    item = TeacherMemoryService.review(
        feedback_id,
        approved=approved,
        confidence=confidence,
    )
    return jsonify({"feedback": item.to_dict()}), 200


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

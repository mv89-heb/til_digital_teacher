from flask import Blueprint, g, jsonify, request

from app.models.exam import Exam
from app.models.exam_result_category import ExamResultCategory
from app.models.exam_section import ExamSection
from app.models.exam_question_pool import ExamQuestionPool
from app.services.exam_answer_service import ExamAnswerService
from app.services.exam_service import ExamService
from app.utils.decorators import jwt_required

exam_bp = Blueprint("exam", __name__, url_prefix="/api/exams")


@exam_bp.route("", methods=["GET"])
@jwt_required
def list_exams():
    """Return published simulations available to the learner."""
    exams = Exam.query.filter_by(status="PUBLISHED").order_by(Exam.created_at.desc(), Exam.id.desc()).all()
    payload = []
    for exam in exams:
        sections = ExamSection.query.filter_by(exam_id=exam.id).order_by(ExamSection.display_order).all()
        payload.append({
            "id": exam.id,
            "name": exam.name,
            "description": exam.description,
            "duration_seconds": exam.duration_seconds,
            "section_count": len(sections),
            "question_count": sum(
                ExamQuestionPool.query.filter_by(exam_section_id=section.id).count()
                for section in sections
            ),
            "sections": [
                {
                    "name": section.name,
                    "category": section.category,
                    "duration_seconds": section.duration_seconds,
                    "question_count": ExamQuestionPool.query.filter_by(exam_section_id=section.id).count(),
                }
                for section in sections
            ],
        })
    return jsonify({"exams": payload}), 200


@exam_bp.route("/<int:exam_id>/sessions", methods=["POST"])
@jwt_required
def start_exam(exam_id):
    session = ExamService.start_session(g.current_user["id"], exam_id)
    return jsonify({"session": ExamService.serialize_session(session)}), 201


@exam_bp.route("/sessions/<int:session_id>", methods=["GET"])
@jwt_required
def get_exam_session(session_id):
    session = ExamService.get_session_for_user(g.current_user["id"], session_id)
    return jsonify({"session": ExamService.serialize_session(session)}), 200


@exam_bp.route("/sessions/<int:session_id>/advance-section", methods=["POST"])
@jwt_required
def advance_exam_section(session_id):
    """Advance exactly one section after the server-side section timer expires."""
    session = ExamService.advance_section(g.current_user["id"], session_id)
    return jsonify({"session": ExamService.serialize_session(session)}), 200


@exam_bp.route("/sessions/<int:session_id>/questions/<int:session_question_id>/view", methods=["POST"])
@jwt_required
def view_question(session_id, session_question_id):
    question = ExamService.mark_question_viewed(
        g.current_user["id"], session_id, session_question_id
    )
    return jsonify({
        "session_question_id": question.id,
        "first_seen_at": question.first_seen_at.isoformat() if question.first_seen_at else None,
        "last_seen_at": question.last_seen_at.isoformat() if question.last_seen_at else None,
    }), 200


@exam_bp.route("/sessions/<int:session_id>/answers", methods=["POST"])
@jwt_required
def submit_answer(session_id):
    data = request.get_json() or {}
    try:
        session_question_id = int(data["session_question_id"])
        answer_id = int(data["answer_id"])
    except (KeyError, TypeError, ValueError):
        return jsonify({"error": "session_question_id and answer_id are required integers"}), 400

    answer = ExamAnswerService.submit(
        g.current_user["id"],
        session_id,
        session_question_id,
        answer_id,
    )
    return jsonify({"answer": {
        "id": answer.id,
        "is_correct": answer.is_correct,
        "score": str(answer.score) if answer.score is not None else None,
        "response_time_ms": answer.response_time_ms,
        "timing_source": "server",
    }}), 200


@exam_bp.route("/sessions/<int:session_id>/submit", methods=["POST"])
@jwt_required
def submit_exam(session_id):
    result = ExamService.submit_session(g.current_user["id"], session_id)
    categories = ExamResultCategory.query.filter_by(result_id=result.id).order_by(ExamResultCategory.category).all()
    return jsonify({"result": {
        "id": result.id,
        "raw_score": str(result.raw_score),
        "weighted_score": str(result.weighted_score),
        "normalized_score": str(result.normalized_score) if result.normalized_score is not None else None,
        "total_questions": result.total_questions,
        "answered_questions": result.answered_questions,
        "correct_answers": result.correct_answers,
        "skipped_questions": result.skipped_questions,
        "total_time_ms": result.total_time_ms,
        "metadata": result.metadata_json or {},
        "categories": [
            {
                "category": row.category,
                "total_questions": row.total_questions,
                "answered_questions": row.answered_questions,
                "correct_answers": row.correct_answers,
                "accuracy": str(row.accuracy) if row.accuracy is not None else None,
                "average_time_ms": row.average_time_ms,
            }
            for row in categories
        ],
    }}), 200

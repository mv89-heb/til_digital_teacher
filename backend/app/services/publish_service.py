from app.extensions import db
from app.models.answer import Answer
from app.models.constants import ContentStatus
from app.models.lesson import Lesson
from app.models.question import Question
from app.models.question_version import QuestionVersion
from app.services.content_integrity_service import ContentIntegrityService
from app.utils.exceptions import AppError


class PublishService:
    @staticmethod
    def _create_question_version(question: Question) -> QuestionVersion:
        latest = (
            QuestionVersion.query.filter_by(question_id=question.id)
            .order_by(QuestionVersion.version_number.desc())
            .first()
        )
        version_number = (latest.version_number + 1) if latest else 1
        answers = (
            Answer.query.filter_by(question_id=question.id)
            .order_by(Answer.order, Answer.id)
            .all()
        )
        snapshot = [
            {
                "id": answer.id,
                "answer_text": answer.answer_text,
                "is_correct": answer.is_correct,
                "explanation_if_selected": answer.explanation_if_selected,
                "order": answer.order,
            }
            for answer in answers
        ]
        version = QuestionVersion(
            question_id=question.id,
            version_number=version_number,
            category_id=question.category_id,
            question_type=question.question_type,
            difficulty=question.difficulty,
            status=ContentStatus.PUBLISHED,
            body=question.body,
            solution_text=question.solution_text,
            question_metadata=question.question_metadata or {},
            answer_snapshot=snapshot,
            recommended_time_seconds=question.recommended_time_seconds,
            created_by=question.created_by,
        )
        db.session.add(version)
        return version

    @staticmethod
    def publish_question(question_id: int) -> Question:
        question = db.session.get(Question, question_id)
        if not question:
            raise AppError("Question not found", status_code=404)
        errors = ContentIntegrityService.validate_question(question)
        if errors:
            raise AppError("Cannot publish question: " + "; ".join(errors), status_code=422)
        question.status = ContentStatus.PUBLISHED
        PublishService._create_question_version(question)
        db.session.commit()
        return question

    @staticmethod
    def publish_lesson(lesson_id: int) -> Lesson:
        lesson = db.session.get(Lesson, lesson_id)
        if not lesson:
            raise AppError("Lesson not found", status_code=404)
        errors = ContentIntegrityService.validate_lesson(lesson)
        if errors:
            raise AppError("Cannot publish lesson: " + "; ".join(errors), status_code=422)
        lesson.status = ContentStatus.PUBLISHED
        db.session.commit()
        return lesson

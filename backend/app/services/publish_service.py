from app.extensions import db
from app.models.constants import ContentStatus
from app.models.question import Question
from app.models.lesson import Lesson
from app.services.content_integrity_service import ContentIntegrityService
from app.utils.exceptions import AppError


class PublishService:
    @staticmethod
    def publish_question(question_id: int) -> Question:
        question = db.session.get(Question, question_id)
        if not question:
            raise AppError("Question not found", status_code=404)
        errors = ContentIntegrityService.validate_question(question)
        if errors:
            raise AppError("Cannot publish question: " + "; ".join(errors), status_code=422)
        question.status = ContentStatus.PUBLISHED
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

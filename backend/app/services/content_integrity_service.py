from collections import defaultdict

from app.models.category import Category
from app.models.constants import ContentStatus
from app.models.lesson import Lesson
from app.models.question import Question
from app.services.question_service import QuestionService


class ContentIntegrityService:
    """Validate publishable content without mutating it."""

    @staticmethod
    def validate_question(question: Question) -> list[str]:
        errors: list[str] = []
        if not question.body:
            errors.append("question body is empty")
        if not question.solution_text:
            errors.append("solution text is empty")
        if not question.answers:
            errors.append("question has no answers")
        elif question.question_type in ("multiple_choice", "single_choice"):
            correct = sum(1 for answer in question.answers if answer.is_correct)
            if correct != 1:
                errors.append(f"multiple-choice question must have exactly one correct answer; found {correct}")
        if question.lesson_id:
            lesson = question.lesson
            if lesson and lesson.category_id != question.category_id:
                errors.append("question category does not match lesson category")
        return errors

    @staticmethod
    def validate_lesson(lesson: Lesson) -> list[str]:
        errors: list[str] = []
        if not lesson.title:
            errors.append("lesson title is empty")
        if lesson.status == ContentStatus.PUBLISHED and not lesson.content_blocks:
            errors.append("published lesson has no content blocks")
        for block in lesson.content_blocks:
            if block.block_type == "embedded_question":
                question_id = (block.content or {}).get("question_id")
                question = Question.query.get(question_id) if question_id else None
                if not question:
                    errors.append(f"embedded question {question_id} does not exist")
                elif question.status != ContentStatus.PUBLISHED:
                    errors.append(f"embedded question {question.id} is not published")
                else:
                    errors.extend([f"question {question.id}: {e}" for e in ContentIntegrityService.validate_question(question)])
        return errors

    @staticmethod
    def validate_all() -> dict:
        result = {"categories": 0, "lessons": 0, "questions": 0, "errors": []}
        for category in Category.query.all():
            result["categories"] += 1
            if not category.name:
                result["errors"].append(f"category {category.id}: name is empty")
        for question in Question.query.all():
            result["questions"] += 1
            result["errors"].extend([f"question {question.id}: {e}" for e in ContentIntegrityService.validate_question(question)])
        for lesson in Lesson.query.all():
            result["lessons"] += 1
            result["errors"].extend([f"lesson {lesson.id}: {e}" for e in ContentIntegrityService.validate_lesson(lesson)])
        result["valid"] = not result["errors"]
        return result

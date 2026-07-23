from app.extensions import db
from app.models.answer import Answer
from app.models.constants import ContentStatus
from app.models.question import Question
from app.services.audit_service import AuditService
from app.utils.exceptions import AppError

_QUESTION_FIELDS = (
    "category_id",
    "lesson_id",
    "question_type",
    "difficulty",
    "status",
    "body",
    "solution_text",
    "recommended_time_seconds",
)


class QuestionService:
    """Admin-context methods always reveal correct answers (admins need to
    see and manage content). The one public-facing path is
    resolve_embedded_blocks(published_only=True), used by LearningService.
    """

    @staticmethod
    def list_questions(category_id: int | None = None, lesson_id: int | None = None) -> list[dict]:
        query = Question.query
        if category_id is not None:
            query = query.filter_by(category_id=category_id)
        if lesson_id is not None:
            query = query.filter_by(lesson_id=lesson_id)
        return [q.to_dict(reveal_answers=True) for q in query.order_by(Question.id).all()]

    @staticmethod
    def get_question(question_id: int, published_only: bool = False) -> Question:
        question = db.session.get(Question, question_id)
        if not question or (published_only and question.status != ContentStatus.PUBLISHED):
            raise AppError("Question not found", status_code=404)
        return question

    @staticmethod
    def create_question(data: dict, admin_user_id: int) -> dict:
        answers_data = data.get("answers", [])
        correct_count = sum(1 for a in answers_data if a.get("is_correct"))
        if correct_count > 1:
            raise AppError("A question can have at most one correct answer", status_code=422)

        question = Question(
            question_metadata=data.get("metadata", {}),
            **{field: data[field] for field in _QUESTION_FIELDS if field in data},
        )
        db.session.add(question)
        db.session.flush()  # assign question.id before creating answers

        for index, answer_data in enumerate(answers_data, start=1):
            db.session.add(
                Answer(
                    question_id=question.id,
                    answer_text=answer_data["answer_text"],
                    is_correct=answer_data.get("is_correct", False),
                    explanation_if_selected=answer_data.get("explanation_if_selected"),
                    order=answer_data.get("order", index),
                )
            )

        db.session.commit()

        AuditService.log(
            admin_user_id, "create", "Question", question.id, {"after": question.to_dict(reveal_answers=True)}
        )
        return question.to_dict(reveal_answers=True)

    @staticmethod
    def update_question(question_id: int, data: dict, admin_user_id: int) -> dict:
        question = QuestionService.get_question(question_id)
        before = question.to_dict(reveal_answers=True)

        if "metadata" in data:
            data = {**data, "question_metadata": data.pop("metadata")}
        for field in (*_QUESTION_FIELDS, "question_metadata"):
            if field in data:
                setattr(question, field, data[field])

        db.session.commit()

        AuditService.log(
            admin_user_id,
            "update",
            "Question",
            question.id,
            {"before": before, "after": question.to_dict(reveal_answers=True)},
        )
        return question.to_dict(reveal_answers=True)

    @staticmethod
    def delete_question(question_id: int, admin_user_id: int) -> None:
        question = QuestionService.get_question(question_id)
        before = question.to_dict(reveal_answers=True)

        db.session.delete(question)
        db.session.commit()

        AuditService.log(admin_user_id, "delete", "Question", question_id, {"before": before})

    # --- answers ---

    @staticmethod
    def _reject_second_correct_answer(question_id: int, exclude_answer_id: int | None = None) -> None:
        query = Answer.query.filter_by(question_id=question_id, is_correct=True)
        if exclude_answer_id is not None:
            query = query.filter(Answer.id != exclude_answer_id)
        if query.first():
            raise AppError("Question already has a correct answer marked", status_code=409)

    @staticmethod
    def add_answer(question_id: int, data: dict, admin_user_id: int) -> dict:
        QuestionService.get_question(question_id)  # 404 if missing
        if data.get("is_correct"):
            QuestionService._reject_second_correct_answer(question_id)

        answer = Answer(
            question_id=question_id,
            answer_text=data["answer_text"],
            is_correct=data.get("is_correct", False),
            explanation_if_selected=data.get("explanation_if_selected"),
            order=data.get("order", 0),
        )
        db.session.add(answer)
        db.session.commit()

        AuditService.log(admin_user_id, "create", "Answer", answer.id, {"after": answer.to_dict(reveal=True)})
        return answer.to_dict(reveal=True)

    @staticmethod
    def get_answer(answer_id: int) -> Answer:
        answer = db.session.get(Answer, answer_id)
        if not answer:
            raise AppError("Answer not found", status_code=404)
        return answer

    @staticmethod
    def update_answer(answer_id: int, data: dict, admin_user_id: int) -> dict:
        answer = QuestionService.get_answer(answer_id)
        before = answer.to_dict(reveal=True)

        if data.get("is_correct"):
            QuestionService._reject_second_correct_answer(answer.question_id, exclude_answer_id=answer.id)

        for field in ("answer_text", "is_correct", "explanation_if_selected", "order"):
            if field in data:
                setattr(answer, field, data[field])

        db.session.commit()

        AuditService.log(
            admin_user_id, "update", "Answer", answer.id, {"before": before, "after": answer.to_dict(reveal=True)}
        )
        return answer.to_dict(reveal=True)

    @staticmethod
    def delete_answer(answer_id: int, admin_user_id: int) -> None:
        answer = QuestionService.get_answer(answer_id)
        before = answer.to_dict(reveal=True)

        db.session.delete(answer)
        db.session.commit()

        AuditService.log(admin_user_id, "delete", "Answer", answer_id, {"before": before})

    # --- embedding resolution, used by LessonService (validation) and
    # LearningService / admin lesson GET (enrichment) ---

    @staticmethod
    def resolve_embedded_blocks(content_blocks: list[dict], published_only: bool) -> list[dict]:
        """Given serialized LessonContent blocks, attach the resolved Question
        onto any embedded_question block as block["question"]. The stored
        `content` stays {"question_id": N} — this only affects the API
        response, never what's persisted.

        published_only=True is the public-facing context: answers are NEVER
        revealed here (reveal_answers=False always, regardless of the flag) —
        correctness is only ever disclosed through PracticeService.submit_answer,
        after the student has actually submitted a choice. published_only=False
        (admin content review) still gets full answer visibility.
        """
        resolved = []
        for block in content_blocks:
            block = dict(block)
            if block.get("type") == "embedded_question":
                question_id = (block.get("content") or {}).get("question_id")
                question = db.session.get(Question, question_id) if question_id else None
                if question and (not published_only or question.status == ContentStatus.PUBLISHED):
                    block["question"] = question.to_dict(include_answers=True, reveal_answers=not published_only)
                else:
                    block["question"] = None
            resolved.append(block)
        return resolved

from datetime import datetime, timezone

from sqlalchemy import func

from app.extensions import db
from app.models.answer import Answer
from app.models.category import Category
from app.models.constants import ContentStatus
from app.models.lesson import Lesson
from app.models.practice_attempt import PracticeAttempt
from app.models.question import Question
from app.models.user_lesson_progress import UserLessonProgress
from app.services.progress_service import ProgressService
from app.services.xp_service import XPService
from app.utils.exceptions import AppError

XP_PER_CORRECT_ANSWER = 10
XP_LESSON_COMPLETED = 50


class PracticeService:
    @staticmethod
    def list_practice_questions(
        user_id: int,
        category_id: int | None = None,
        difficulty: str | None = None,
        limit: int = 10,
        mode: str = "adaptive",
    ) -> dict:
        """Return published questions for the student-facing practice pool.

        Correctness and solution data are deliberately stripped by
        Question.to_dict(reveal_answers=False). The adaptive mode uses the
        student's recent accuracy to choose a target difficulty, while
        retaining a deterministic fallback so a sparse bank still produces
        questions.
        """
        limit = max(1, min(limit, 50))
        if mode not in {"adaptive", "all"}:
            raise AppError("Invalid practice mode", status_code=400)
        if difficulty and difficulty not in {"easy", "medium", "exam"}:
            raise AppError("Invalid difficulty", status_code=400)

        query = Question.query.filter(Question.status == ContentStatus.PUBLISHED)

        if category_id is not None:
            category = db.session.get(Category, category_id)
            if not category:
                raise AppError("Category not found", status_code=404)

            # The seeded bank uses one parent level for subcategories. Include
            # the selected category and its direct children so the main
            # category cards work without duplicating questions.
            child_ids = [row.id for row in Category.query.filter_by(parent_id=category_id).all()]
            query = query.filter(Question.category_id.in_([category_id, *child_ids]))

        target_difficulty = difficulty
        if mode == "adaptive" and target_difficulty is None:
            recent = (
                PracticeAttempt.query.filter_by(user_id=user_id)
                .order_by(PracticeAttempt.created_at.desc())
                .limit(20)
                .all()
            )
            if not recent:
                target_difficulty = "medium"
            else:
                accuracy = sum(1 for attempt in recent if attempt.is_correct) / len(recent)
                target_difficulty = "easy" if accuracy < 0.55 else "exam" if accuracy >= 0.80 else "medium"

        if target_difficulty:
            difficulty_query = query.filter(Question.difficulty == target_difficulty)
            if difficulty_query.first() is not None:
                query = difficulty_query

        # Prefer questions the student has not answered yet. If the bank is
        # smaller than the requested limit, fill the remainder from all
        # published questions matching the same pool.
        attempted_subquery = db.session.query(PracticeAttempt.question_id).filter(
            PracticeAttempt.user_id == user_id
        )
        fresh = query.filter(~Question.id.in_(attempted_subquery)).order_by(func.random()).limit(limit).all()

        if len(fresh) < limit:
            selected_ids = [question.id for question in fresh]
            remainder_query = query
            if selected_ids:
                remainder_query = remainder_query.filter(~Question.id.in_(selected_ids))
            remainder = remainder_query.order_by(func.random()).limit(limit - len(fresh)).all()
            questions = fresh + remainder
        else:
            questions = fresh

        return {
            "questions": [PracticeService._public_question(question) for question in questions],
            "count": len(questions),
            "mode": mode,
            "target_difficulty": target_difficulty,
        }

    @staticmethod
    def get_practice_question(question_id: int) -> dict:
        question = db.session.get(Question, question_id)
        if not question or question.status != ContentStatus.PUBLISHED:
            raise AppError("Question not found", status_code=404)
        return PracticeService._public_question(question)

    @staticmethod
    def _public_question(question: Question) -> dict:
        """Serialize a question for a student before an answer is submitted."""
        data = question.to_dict(include_answers=True, reveal_answers=False)
        metadata = question.question_metadata or {}
        data["bank_key"] = metadata.get("bank_key")
        data["main_category"] = metadata.get("main_category")
        data["subcategory"] = metadata.get("subcategory")
        data["skill"] = metadata.get("skill")
        data["difficulty_level"] = metadata.get("difficulty_level")
        data["tags"] = metadata.get("tags", [])
        data["visual_data"] = metadata.get("visual_data") or metadata.get("visual")
        return data

    @staticmethod
    def submit_answer(user_id: int, question_id: int, answer_id: int) -> dict:
        """The only place answer-correctness is decided.

        The client sends an answer_id; the server looks up is_correct itself
        and returns the verdict + explanation. Correctness is never trusted
        from, or precomputed on, the client.
        """
        question = db.session.get(Question, question_id)
        if not question or question.status != ContentStatus.PUBLISHED:
            raise AppError("Question not found", status_code=404)

        answer = db.session.get(Answer, answer_id)
        if not answer or answer.question_id != question_id:
            raise AppError("Answer does not belong to this question", status_code=422)

        is_correct = answer.is_correct

        already_earned_xp = (
            is_correct
            and PracticeAttempt.query.filter_by(
                user_id=user_id, question_id=question_id, is_correct=True
            ).first()
            is not None
        )
        xp_earned = XP_PER_CORRECT_ANSWER if (is_correct and not already_earned_xp) else 0

        attempt = PracticeAttempt(
            user_id=user_id,
            question_id=question_id,
            answer_id=answer_id,
            is_correct=is_correct,
            xp_earned=xp_earned,
        )
        db.session.add(attempt)
        db.session.commit()

        new_xp_total = None
        if xp_earned:
            new_xp_total = XPService.award(
                user_id, xp_earned, "question_correct", "Question", question_id
            )

        ProgressService.record_practice_attempt(user_id, question.category_id, is_correct, xp_earned)

        correct_answer = next((a for a in question.answers if a.is_correct), None)

        return {
            "is_correct": is_correct,
            "correct_answer_id": correct_answer.id if correct_answer else None,
            "explanation": answer.explanation_if_selected,
            "solution_text": question.solution_text,
            "xp_earned": xp_earned,
            "xp_total": new_xp_total,
        }

    @staticmethod
    def _get_or_create_progress(user_id: int, lesson_id: int) -> UserLessonProgress:
        progress = UserLessonProgress.query.filter_by(user_id=user_id, lesson_id=lesson_id).first()
        if not progress:
            progress = UserLessonProgress(user_id=user_id, lesson_id=lesson_id)
            db.session.add(progress)
            db.session.commit()
        return progress

    @staticmethod
    def get_lesson_progress(user_id: int, lesson_id: int) -> dict:
        progress = UserLessonProgress.query.filter_by(user_id=user_id, lesson_id=lesson_id).first()
        if not progress:
            return {
                "user_id": user_id,
                "lesson_id": lesson_id,
                "completed": False,
                "completed_at": None,
                "xp_earned": 0,
                "last_viewed_at": None,
            }
        return progress.to_dict()

    @staticmethod
    def complete_lesson(user_id: int, lesson_id: int) -> dict:
        lesson = db.session.get(Lesson, lesson_id)
        if not lesson or lesson.status != ContentStatus.PUBLISHED:
            raise AppError("Lesson not found", status_code=404)

        progress = PracticeService._get_or_create_progress(user_id, lesson_id)
        progress.last_viewed_at = datetime.now(timezone.utc)

        if progress.completed_at is None:
            progress.completed_at = datetime.now(timezone.utc)
            progress.xp_earned = XP_LESSON_COMPLETED
            db.session.commit()
            XPService.award(user_id, XP_LESSON_COMPLETED, "lesson_completed", "Lesson", lesson_id)
            ProgressService.record_lesson_completion(user_id, lesson.category_id, XP_LESSON_COMPLETED)
        else:
            db.session.commit()

        return progress.to_dict()

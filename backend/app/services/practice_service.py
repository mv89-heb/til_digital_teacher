from datetime import datetime, timezone

from app.extensions import db
from app.models.answer import Answer
from app.models.constants import ContentStatus
from app.models.lesson import Lesson
from app.models.practice_attempt import PracticeAttempt
from app.models.question import Question
from app.models.user_lesson_progress import UserLessonProgress
from app.services.progress_service import ProgressService
from app.services.xp_service import XPService
from app.utils.exceptions import AppError

XP_PER_CORRECT_ANSWER = 10
XP_PER_LESSON_COMPLETED = 50


class PracticeService:
    @staticmethod
    def submit_answer(user_id: int, question_id: int, answer_id: int) -> dict:
        """The only place answer-correctness is decided. The client sends an
        answer_id; the server looks up is_correct itself and returns the
        verdict + explanation — the correct answer is never trusted from,
        or precomputed on, the client.
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
            progress.xp_earned = XP_PER_LESSON_COMPLETED
            db.session.commit()
            XPService.award(user_id, XP_PER_LESSON_COMPLETED, "lesson_completed", "Lesson", lesson_id)
            ProgressService.record_lesson_completion(user_id, lesson.category_id, XP_PER_LESSON_COMPLETED)
        else:
            db.session.commit()  # persist last_viewed_at even if already completed

        return progress.to_dict()

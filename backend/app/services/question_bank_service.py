"""Question-bank selection and calibration helpers.

The selector is intentionally separate from the exam-session persistence layer:
exam creation can use it to build a balanced pool, while practice mode can use
it for a smaller adaptive batch.
"""

from collections import Counter

from sqlalchemy import and_, func, not_, select

from app.extensions import db
from app.models.category import Category
from app.models.constants import ContentStatus
from app.models.exam_session import ExamSession
from app.models.question import Question
from app.models.session_question import SessionQuestion


DIFFICULTY_WEIGHTS = {
    1: 0.10,
    2: 0.20,
    3: 0.40,
    4: 0.20,
    5: 0.10,
}


class QuestionBankService:
    """Select questions while balancing category, difficulty and exposure."""

    @staticmethod
    def _recent_question_ids(user_id: int, recent_sessions: int = 5) -> set[int]:
        stmt = (
            select(SessionQuestion.question_id)
            .join(ExamSession, ExamSession.id == SessionQuestion.session_id)
            .where(ExamSession.user_id == user_id)
            .order_by(ExamSession.created_at.desc())
            .limit(max(1, recent_sessions) * 100)
        )
        return {row[0] for row in db.session.execute(stmt).all()}

    @staticmethod
    def _candidates(user_id: int, category_type: str, excluded_ids: set[int]) -> list[Question]:
        stmt = (
            select(Question)
            .join(Category, Category.id == Question.category_id)
            .where(
                Category.type == category_type,
                Question.status == ContentStatus.PUBLISHED,
            )
            .order_by(func.random())
        )
        questions = list(db.session.scalars(stmt).all())
        if excluded_ids:
            fresh = [q for q in questions if q.id not in excluded_ids]
            if fresh:
                return fresh
        return questions

    @staticmethod
    def _difficulty_level(question: Question) -> int:
        metadata = question.question_metadata or {}
        try:
            return max(1, min(5, int(metadata.get("difficulty_level", 3))))
        except (TypeError, ValueError):
            return 3

    @classmethod
    def select_balanced(
        cls,
        user_id: int,
        category_type: str,
        count: int,
        *,
        exclude_recent: bool = True,
        target_level: int | None = None,
    ) -> list[Question]:
        """Return a randomized, difficulty-balanced batch.

        The requested target level is used as a soft preference, not a hard
        filter, so small banks remain usable. Recently seen questions are
        excluded when enough unseen candidates exist.
        """
        if count <= 0:
            return []

        recent_ids = cls._recent_question_ids(user_id) if exclude_recent else set()
        candidates = cls._candidates(user_id, category_type, recent_ids)

        if target_level is not None:
            target_level = max(1, min(5, target_level))
            candidates.sort(key=lambda q: abs(cls._difficulty_level(q) - target_level))

        selected: list[Question] = []
        remaining = candidates[:]
        target_counts = Counter()
        for level, weight in DIFFICULTY_WEIGHTS.items():
            target_counts[level] = round(count * weight)
        while sum(target_counts.values()) < count:
            target_counts[3] += 1
        while sum(target_counts.values()) > count:
            if target_counts[3] > 0:
                target_counts[3] -= 1
            else:
                break

        # First satisfy the blueprint by difficulty.
        for level in range(1, 6):
            wanted = target_counts[level]
            bucket = [q for q in remaining if cls._difficulty_level(q) == level]
            take = bucket[:wanted]
            selected.extend(take)
            taken_ids = {q.id for q in take}
            remaining = [q for q in remaining if q.id not in taken_ids]

        # Fill shortages from the remaining candidates.
        selected_ids = {q.id for q in selected}
        selected.extend(q for q in remaining if q.id not in selected_ids)
        selected = selected[:count]

        # Final shuffle keeps the difficulty sequence from becoming obvious.
        import random
        random.shuffle(selected)
        return selected

    @classmethod
    def select_simulation(
        cls,
        user_id: int,
        blueprint: dict,
    ) -> list[Question]:
        """Build a standard simulation from a category/difficulty blueprint."""
        selected: list[Question] = []
        for category_type, category_count in blueprint.get("distribution", {}).items():
            batch = cls.select_balanced(
                user_id,
                category_type,
                int(category_count),
                exclude_recent=True,
            )
            selected.extend(batch)

        import random
        random.shuffle(selected)
        return selected

    @staticmethod
    def build_default_blueprint(total_questions: int = 45) -> dict:
        """Return the default 3-section simulation blueprint."""
        per_category = total_questions // 3
        remainder = total_questions - per_category * 3
        distribution = {
            "quantitative": per_category,
            "verbal": per_category,
            "figural": per_category,
        }
        distribution["quantitative"] += remainder
        return {
            "total_questions": total_questions,
            "distribution": distribution,
            "difficulty_distribution": DIFFICULTY_WEIGHTS.copy(),
        }

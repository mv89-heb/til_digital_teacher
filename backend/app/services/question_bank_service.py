"""Question-bank selection and calibration helpers.

The selector is intentionally separate from the exam-session persistence layer:
exam creation can use it to build a balanced pool, while practice mode can use
it for a smaller adaptive batch.
"""

from collections import Counter
import random

from sqlalchemy import func, select

from app.extensions import db
from app.models.category import Category
from app.models.constants import ContentStatus
from app.models.exam_session import ExamSession
from app.models.question import Question
from app.models.session_question import SessionQuestion


DIFFICULTY_WEIGHTS = {1: 0.10, 2: 0.20, 3: 0.40, 4: 0.20, 5: 0.10}


class QuestionBankService:
    """Select questions while balancing category, difficulty and exposure."""

    @staticmethod
    def _recent_question_ids(user_id: int, recent_sessions: int = 5) -> set[int]:
        """Return all question ids used by the user's most recent sessions."""
        session_ids = list(
            db.session.scalars(
                select(ExamSession.id)
                .where(ExamSession.user_id == user_id)
                .order_by(ExamSession.created_at.desc(), ExamSession.id.desc())
                .limit(max(1, recent_sessions))
            ).all()
        )
        if not session_ids:
            return set()
        return set(
            db.session.scalars(
                select(SessionQuestion.question_id).where(SessionQuestion.session_id.in_(session_ids))
            ).all()
        )

    @staticmethod
    def _candidates(user_id: int, category_type: str, excluded_ids: set[int]) -> list[Question]:
        stmt = (
            select(Question)
            .join(Category, Category.id == Question.category_id)
            .where(Category.type == category_type, Question.status == ContentStatus.PUBLISHED)
            .order_by(func.random())
        )
        questions = list(db.session.scalars(stmt).all())
        if excluded_ids:
            fresh = [q for q in questions if q.id not in excluded_ids]
            if len(fresh) >= 1:
                return fresh
        return questions

    @staticmethod
    def _difficulty_level(question: Question) -> int:
        metadata = question.question_metadata or {}
        try:
            return max(1, min(5, int(metadata.get("difficulty_level", 3))))
        except (TypeError, ValueError):
            return 3

    @staticmethod
    def _target_counts(count: int) -> Counter:
        """Largest-remainder allocation of the 10/20/40/20/10 blueprint."""
        raw = {level: count * weight for level, weight in DIFFICULTY_WEIGHTS.items()}
        targets = Counter({level: int(value) for level, value in raw.items()})
        remaining = count - sum(targets.values())
        ranked = sorted(raw, key=lambda level: (raw[level] - int(raw[level]), level), reverse=True)
        for level in ranked[:remaining]:
            targets[level] += 1
        return targets

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

        Recent questions are excluded whenever the bank contains enough fresh
        candidates. If the bank is temporarily exhausted, the service falls
        back to the complete published pool instead of returning too few items.
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
        target_counts = cls._target_counts(count)

        for level in range(1, 6):
            wanted = target_counts[level]
            bucket = [q for q in remaining if cls._difficulty_level(q) == level]
            random.shuffle(bucket)
            take = bucket[:wanted]
            selected.extend(take)
            taken_ids = {q.id for q in take}
            remaining = [q for q in remaining if q.id not in taken_ids]

        selected_ids = {q.id for q in selected}
        random.shuffle(remaining)
        selected.extend(q for q in remaining if q.id not in selected_ids)
        random.shuffle(selected)
        return selected[:count]

    @classmethod
    def select_simulation(cls, user_id: int, blueprint: dict) -> list[Question]:
        """Build a standard simulation from a category distribution blueprint."""
        selected: list[Question] = []
        used_ids: set[int] = set()
        for category_type, category_count in blueprint.get("distribution", {}).items():
            batch = cls.select_balanced(user_id, category_type, int(category_count), exclude_recent=True)
            batch = [q for q in batch if q.id not in used_ids]
            used_ids.update(q.id for q in batch)
            selected.extend(batch)

        random.shuffle(selected)
        return selected

    @staticmethod
    def build_default_blueprint(total_questions: int = 45) -> dict:
        """Return the default 3-section simulation blueprint."""
        if total_questions <= 0:
            raise ValueError("total_questions must be positive")
        per_category, remainder = divmod(total_questions, 3)
        distribution = {"quantitative": per_category, "verbal": per_category, "figural": per_category}
        distribution["quantitative"] += remainder
        return {
            "total_questions": total_questions,
            "distribution": distribution,
            "difficulty_distribution": DIFFICULTY_WEIGHTS.copy(),
        }

"""Question-bank selection and calibration helpers.

The selector is intentionally separate from the exam-session persistence layer:
exam creation can use it to build a balanced pool, while practice mode can use
it for a smaller adaptive batch.
"""

from collections import Counter
import random

from sqlalchemy import select

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
                select(SessionQuestion.question_id)
                .where(SessionQuestion.session_id.in_(session_ids))
            ).all()
        )

    @staticmethod
    def _candidates(user_id: int, category_type: str, excluded_ids: set[int]) -> list[Question]:
        stmt = (
            select(Question)
            .join(Category, Category.id == Question.category_id)
            .where(Category.type == category_type, Question.status == ContentStatus.PUBLISHED)
        )
        questions = list(db.session.scalars(stmt).all())
        random.shuffle(questions)
        if not excluded_ids:
            return questions
        fresh = [q for q in questions if q.id not in excluded_ids]
        return fresh if fresh else questions

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
        ranked = sorted(
            raw,
            key=lambda level: (raw[level] - int(raw[level]), -level),
            reverse=True,
        )
        for level in ranked[:remaining]:
            targets[level] += 1
        return targets

    @classmethod
    def _take_by_difficulty(
        cls,
        candidates: list[Question],
        count: int,
        target_level: int | None = None,
    ) -> list[Question]:
        if count <= 0 or not candidates:
            return []

        buckets = {level: [] for level in range(1, 6)}
        for question in candidates:
            buckets[cls._difficulty_level(question)].append(question)
        for bucket in buckets.values():
            random.shuffle(bucket)

        if target_level is not None:
            target_level = max(1, min(5, target_level))
            level_order = sorted(
                range(1, 6),
                key=lambda level: (abs(level - target_level), random.random()),
            )
            selected = []
            for level in level_order:
                selected.extend(buckets[level][: count - len(selected)])
                if len(selected) >= count:
                    break
            random.shuffle(selected)
            return selected[:count]

        targets = cls._target_counts(count)
        selected = []
        for level in range(1, 6):
            selected.extend(buckets[level][:targets[level]])

        selected_ids = {q.id for q in selected}
        remaining = [q for q in candidates if q.id not in selected_ids]
        random.shuffle(remaining)
        selected.extend(remaining[: max(0, count - len(selected))])
        random.shuffle(selected)
        return selected[:count]

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

        Recent questions are excluded whenever fresh questions exist. If the
        pool is exhausted, the complete published pool is used as a fallback.
        """
        if count <= 0:
            return []
        recent_ids = cls._recent_question_ids(user_id) if exclude_recent else set()
        candidates = cls._candidates(user_id, category_type, recent_ids)
        return cls._take_by_difficulty(candidates, count, target_level)

    @classmethod
    def select_simulation(cls, user_id: int, blueprint: dict) -> list[Question]:
        """Build a simulation with category quotas and balanced difficulty."""
        distribution = blueprint.get("distribution") or {}
        total = int(blueprint.get("total_questions") or sum(int(v) for v in distribution.values()))
        if total <= 0:
            return []

        recent_ids = cls._recent_question_ids(user_id)
        selected = []
        used_ids = set()

        for category_type, category_count in distribution.items():
            quota = int(category_count)
            if quota <= 0:
                continue
            candidates = cls._candidates(user_id, category_type, recent_ids)
            batch = cls._take_by_difficulty(candidates, quota)
            for question in batch:
                if question.id not in used_ids:
                    selected.append(question)
                    used_ids.add(question.id)

        # Never duplicate a question. If one section was short, fill from the
        # other published pools while preserving the requested total when the
        # database contains enough unique questions.
        if len(selected) < total:
            all_candidates = []
            for category_type in distribution:
                all_candidates.extend(cls._candidates(user_id, category_type, recent_ids))
            random.shuffle(all_candidates)
            for question in all_candidates:
                if len(selected) >= total:
                    break
                if question.id not in used_ids:
                    selected.append(question)
                    used_ids.add(question.id)

        random.shuffle(selected)
        return selected[:total]

    @staticmethod
    def build_default_blueprint(total_questions: int = 45) -> dict:
        if total_questions <= 0:
            raise ValueError("total_questions must be positive")
        per_category, remainder = divmod(total_questions, 3)
        distribution = {
            "quantitative": per_category + remainder,
            "verbal": per_category,
            "figural": per_category,
        }
        return {
            "total_questions": total_questions,
            "distribution": distribution,
            "difficulty_distribution": DIFFICULTY_WEIGHTS.copy(),
        }

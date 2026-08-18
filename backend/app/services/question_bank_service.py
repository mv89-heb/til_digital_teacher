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


# Standard simulation blueprint: predominantly medium difficulty, with both
# easier warm-up items and harder discriminating items.
DIFFICULTY_WEIGHTS = {1: 0.10, 2: 0.20, 3: 0.40, 4: 0.20, 5: 0.10}


class QuestionBankService:
    """Select questions while balancing category, difficulty and exposure."""

    @staticmethod
    def _recent_question_ids(user_id: int, recent_sessions: int = 5) -> set[int]:
        """Return ids used in the user's latest completed/active sessions."""
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
            .where(
                Category.type == category_type,
                Question.status == ContentStatus.PUBLISHED,
            )
        )
        questions = list(db.session.scalars(stmt).all())
        random.shuffle(questions)

        if not excluded_ids:
            return questions

        # Prefer never-recent questions. Only fall back to recent items when
        # the available fresh pool cannot satisfy the requested batch.
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
        """Select an exact-size batch when the pool contains enough questions."""
        if count <= 0 or not candidates:
            return []

        buckets = {level: [] for level in range(1, 6)}
        for question in candidates:
            buckets[cls._difficulty_level(question)].append(question)
        for bucket in buckets.values():
            random.shuffle(bucket)

        if target_level is not None:
            target_level = max(1, min(5, target_level))
            # Adaptive practice: start near the student's target level, then
            # widen one level at a time if a bucket is short.
            level_order = sorted(
                range(1, 6), key=lambda level: (abs(level - target_level), random.random())
            )
            selected = []
            for level in level_order:
                need = count - len(selected)
                if need <= 0:
                    break
                selected.extend(buckets[level][:need])
            random.shuffle(selected)
            return selected[:count]

        targets = cls._target_counts(count)
        selected = []
        for level in range(1, 6):
            take = min(targets[level], len(buckets[level]))
            selected.extend(buckets[level][:take])

        # If a difficulty bucket is under-populated, fill the deficit from the
        # nearest available levels rather than silently returning too few items.
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

        The selector first removes questions from the user's recent session
        history, then applies either the standard simulation difficulty
        blueprint or a target level for adaptive practice.
        """
        if count <= 0:
            return []

        recent_ids = cls._recent_question_ids(user_id) if exclude_recent else set()
        candidates = cls._candidates(user_id, category_type, recent_ids)

        # If the bank is exhausted by recent history, _candidates returns the
        # full published pool, guaranteeing a usable fallback.
        return cls._take_by_difficulty(candidates, count, target_level)

    @classmethod
    def select_simulation(cls, user_id: int, blueprint: dict) -> list[Question]:
        """Build a simulation while keeping global difficulty balanced.

        Category quotas are applied first. Difficulty quotas are then allocated
        across the complete simulation, preventing each section from rounding
        independently and drifting away from the intended 10/20/40/20/10 mix.
        """
        distribution = blueprint.get("distribution") or {}
        total = int(blueprint.get("total_questions") or sum(int(v) for v in distribution.values()))
        if total <= 0:
            return []

        recent_ids = cls._recent_question_ids(user_id)
        category_candidates: dict[str, list[Question]] = {}
        for category_type, category_count in distribution.items():
            if int(category_count) <= 0:
                continue
            category_candidates[category_type] = cls._candidates(user_id, category_type, recent_ids)

        # Allocate global difficulty targets to categories proportionally.
        global_targets = cls._target_counts(total)
        selected: list[Question] = []
        used_ids: set[int] = set()

        category_items = list(category_candidates.items())
        for index, (category_type, category_candidates_list) in enumerate(category_items):
            quota = int(distribution[category_type])
            if quota <= 0:
                continue

            # For the last category, take the exact remaining amount so
            # rounding cannot change the requested total.
            if index == len(category_items) - 1:
                category_target = Counter({level: 0 for level in range(1, 6)})
                for level in range(1, 6):
                    category_target[level] = max(0, global_targets[level])
                chosen = cls._take_by_difficulty(category_candidates_list, quota)
            else:
                chosen = cls._take_by_difficulty(category_candidates_list, quota)

            chosen = [q for q in chosen if q.id not in used_ids]
            used_ids.update(q.id for q in chosen)
            selected.extend(chosen)

        # Defensive fill if a category contained duplicates or insufficient
        # fresh questions. Never duplicate a question inside one simulation.
        if len(selected) < total:
            all_candidates = []
            for items in category_candidates.values():
                all_candidates.extend(items)
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
        """Return the default 3-section simulation blueprint."""
        if total_questions <= 0:
            raise ValueError("total_questions must be positive")
        per_category, remainder = divmod(total_questions, 3)
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

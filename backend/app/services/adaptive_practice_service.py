from collections import defaultdict

from sqlalchemy import func

from app.extensions import db
from app.models.constants import ContentStatus
from app.models.practice_attempt import PracticeAttempt
from app.models.question import Question


class AdaptivePracticeService:
    """Select practice questions from existing attempt history.

    The selector is deterministic and explainable. It never reads or returns
    answer keys; public question serialization remains owned by PracticeService.
    """

    DIFFICULTY_ORDER = {"easy": 0, "medium": 1, "exam": 2}

    @classmethod
    def profile(cls, user_id: int) -> dict:
        attempts = (
            PracticeAttempt.query.filter_by(user_id=user_id)
            .order_by(PracticeAttempt.created_at.desc())
            .limit(100)
            .all()
        )
        by_skill = defaultdict(lambda: {"attempted": 0, "correct": 0, "last_question_id": None})
        by_category = defaultdict(lambda: {"attempted": 0, "correct": 0})

        for attempt in attempts:
            question = db.session.get(Question, attempt.question_id)
            if not question:
                continue
            metadata = question.question_metadata or {}
            skill = metadata.get("skill") or metadata.get("subcategory") or metadata.get("main_category") or f"category:{question.category_id}"
            row = by_skill[skill]
            row["attempted"] += 1
            row["correct"] += int(bool(attempt.is_correct))
            if row["last_question_id"] is None:
                row["last_question_id"] = question.id

            cat = by_category[question.category_id]
            cat["attempted"] += 1
            cat["correct"] += int(bool(attempt.is_correct))

        skills = []
        for skill, row in by_skill.items():
            accuracy = row["correct"] / row["attempted"] if row["attempted"] else 0
            skills.append({"skill": skill, **row, "accuracy_percent": round(accuracy * 100)})
        skills.sort(key=lambda item: (item["accuracy_percent"], -item["attempted"], item["skill"]))

        return {
            "attempts_considered": len(attempts),
            "skills": skills,
            "weakest_skill": skills[0] if skills else None,
            "categories": {
                str(category_id): {
                    **row,
                    "accuracy_percent": round(100 * row["correct"] / row["attempted"]) if row["attempted"] else 0,
                }
                for category_id, row in by_category.items()
            },
        }

    @classmethod
    def select(cls, user_id: int, limit: int = 10, category_id: int | None = None, difficulty: str | None = None) -> dict:
        limit = max(1, min(limit, 50))
        profile = cls.profile(user_id)
        weakest = profile.get("weakest_skill")

        query = Question.query.filter(Question.status == ContentStatus.PUBLISHED)
        if category_id is not None:
            query = query.filter(Question.category_id == category_id)
        if difficulty in cls.DIFFICULTY_ORDER:
            query = query.filter(Question.difficulty == difficulty)

        # Pull a bounded candidate set, then score it in Python so JSON metadata
        # can be used safely without database-specific JSON operators.
        candidates = query.order_by(func.random()).limit(max(limit * 8, 80)).all()
        recent_ids = {
            attempt.question_id
            for attempt in PracticeAttempt.query.filter_by(user_id=user_id)
            .order_by(PracticeAttempt.created_at.desc())
            .limit(8)
            .all()
        }

        weakest_name = weakest["skill"] if weakest else None
        scored = []
        for question in candidates:
            metadata = question.question_metadata or {}
            skill = metadata.get("skill") or metadata.get("subcategory") or metadata.get("main_category") or f"category:{question.category_id}"
            skill_stats = next((item for item in profile["skills"] if item["skill"] == skill), None)
            accuracy = skill_stats["accuracy_percent"] if skill_stats else None
            score = 0
            reason = "תרגול מאוזן"
            if skill == weakest_name:
                score += 100
                reason = "חיזוק החולשה שזוהתה"
            if question.id in recent_ids:
                score -= 60
            if accuracy is not None:
                score += max(0, 60 - accuracy)
            if question.difficulty == "medium":
                score += 5
            elif question.difficulty == "easy" and accuracy is not None and accuracy < 55:
                score += 15
            elif question.difficulty == "exam" and accuracy is not None and accuracy >= 80:
                score += 15
            scored.append((score, question, reason))

        scored.sort(key=lambda item: (-item[0], item[1].id))
        selected = [item for item in scored if item[1].id not in recent_ids][:limit]
        if len(selected) < limit:
            selected = scored[:limit]

        target = {
            "skill": weakest_name,
            "reason": selected[0][2] if selected else "אין מספיק שאלות זמינות",
            "accuracy_percent": weakest.get("accuracy_percent") if weakest else None,
        }
        return {
            "questions": [item[1] for item in selected],
            "target": target,
            "profile": profile,
        }

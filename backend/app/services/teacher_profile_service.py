from collections import defaultdict

from app.models.practice_attempt import PracticeAttempt
from app.models.question import Question


class TeacherProfileService:
    """Build a lightweight adaptive profile from existing practice data.

    No additional student-profile table is required: the profile is derived
    from PracticeAttempt + Question metadata, keeping one source of truth.
    """

    @staticmethod
    def build(user_id: int, limit: int = 120) -> dict:
        attempts = (
            PracticeAttempt.query
            .filter(PracticeAttempt.user_id == user_id)
            .order_by(PracticeAttempt.created_at.desc())
            .limit(limit)
            .all()
        )
        if not attempts:
            return {
                "attempts": 0,
                "accuracy": None,
                "strengths": [],
                "weaknesses": [],
                "focus": None,
            }

        question_ids = {attempt.question_id for attempt in attempts}
        questions = {
            question.id: question
            for question in Question.query.filter(Question.id.in_(question_ids)).all()
        }

        buckets = defaultdict(lambda: {"correct": 0, "wrong": 0})
        for attempt in attempts:
            question = questions.get(attempt.question_id)
            metadata = (question.question_metadata or {}) if question else {}
            skill = metadata.get("skill") or metadata.get("subcategory") or metadata.get("main_category") or "כללי"
            bucket = buckets[str(skill)]
            if attempt.is_correct:
                bucket["correct"] += 1
            else:
                bucket["wrong"] += 1

        scored = []
        for skill, values in buckets.items():
            total = values["correct"] + values["wrong"]
            accuracy = values["correct"] / total if total else 0
            scored.append({
                "skill": skill,
                "attempts": total,
                "accuracy": round(accuracy * 100),
            })

        scored.sort(key=lambda item: (item["accuracy"], -item["attempts"]))
        accuracy = sum(1 for item in attempts if item.is_correct) / len(attempts)
        weaknesses = [item for item in scored if item["attempts"] >= 2 and item["accuracy"] < 70][:5]
        strengths = [item for item in reversed(scored) if item["attempts"] >= 2 and item["accuracy"] >= 80][:5]

        return {
            "attempts": len(attempts),
            "accuracy": round(accuracy * 100),
            "strengths": strengths,
            "weaknesses": weaknesses,
            "focus": weaknesses[0]["skill"] if weaknesses else None,
        }

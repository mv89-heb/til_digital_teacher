from app.extensions import db
from app.models.practice_attempt import PracticeAttempt
from app.models.user_progress import UserProgress


class PracticeIntegrityService:
    @staticmethod
    def duplicate_xp_credits() -> list[dict]:
        """Report questions where a user has more than one XP-bearing attempt."""
        rows = (
            db.session.query(
                PracticeAttempt.user_id,
                PracticeAttempt.question_id,
                db.func.count(PracticeAttempt.id).label("credits"),
            )
            .filter(PracticeAttempt.xp_earned > 0)
            .group_by(PracticeAttempt.user_id, PracticeAttempt.question_id)
            .having(db.func.count(PracticeAttempt.id) > 1)
            .all()
        )
        return [
            {"user_id": user_id, "question_id": question_id, "credits": credits}
            for user_id, question_id, credits in rows
        ]

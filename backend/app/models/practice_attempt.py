from app.extensions import db
from app.models.mixins import TimestampMixin


class PracticeAttempt(db.Model, TimestampMixin):
    __tablename__ = "practice_attempts"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False, index=True)
    question_id = db.Column(db.Integer, db.ForeignKey("questions.id"), nullable=False, index=True)
    answer_id = db.Column(db.Integer, db.ForeignKey("answers.id"), nullable=False)
    is_correct = db.Column(db.Boolean, nullable=False)
    xp_earned = db.Column(db.Integer, default=0, nullable=False)

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "user_id": self.user_id,
            "question_id": self.question_id,
            "answer_id": self.answer_id,
            "is_correct": self.is_correct,
            "xp_earned": self.xp_earned,
            "created_at": self.created_at.isoformat(),
        }

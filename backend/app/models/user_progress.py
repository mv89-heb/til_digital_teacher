from app.extensions import db
from app.models.mixins import TimestampMixin


class UserProgress(db.Model, TimestampMixin):
    """Category-level rollup for one user. Derived/cached data — PracticeAttempt
    and UserLessonProgress remain the source of truth; this table exists so
    the dashboard doesn't have to run a full aggregate query on every load.
    Kept in sync exclusively by ProgressService, called right after each
    PracticeAttempt/lesson-completion event (mirrors XPService/User.xp_total).
    """

    __tablename__ = "user_progress"
    __table_args__ = (db.UniqueConstraint("user_id", "category_id", name="uq_user_progress"),)

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False, index=True)
    category_id = db.Column(db.Integer, db.ForeignKey("categories.id"), nullable=False, index=True)
    questions_attempted = db.Column(db.Integer, default=0, nullable=False)
    questions_correct = db.Column(db.Integer, default=0, nullable=False)
    lessons_completed = db.Column(db.Integer, default=0, nullable=False)
    xp_earned = db.Column(db.Integer, default=0, nullable=False)
    last_practiced_at = db.Column(db.DateTime, nullable=True)

    def to_dict(self) -> dict:
        accuracy = (
            round(100 * self.questions_correct / self.questions_attempted)
            if self.questions_attempted
            else 0
        )
        return {
            "id": self.id,
            "user_id": self.user_id,
            "category_id": self.category_id,
            "questions_attempted": self.questions_attempted,
            "questions_correct": self.questions_correct,
            "accuracy_percent": accuracy,
            "lessons_completed": self.lessons_completed,
            "xp_earned": self.xp_earned,
            "last_practiced_at": self.last_practiced_at.isoformat() if self.last_practiced_at else None,
        }

from datetime import datetime, timezone

from app.extensions import db
from app.models.mixins import TimestampMixin


class UserLessonProgress(db.Model, TimestampMixin):
    __tablename__ = "user_lesson_progress"
    __table_args__ = (db.UniqueConstraint("user_id", "lesson_id", name="uq_user_lesson_progress"),)

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False, index=True)
    lesson_id = db.Column(db.Integer, db.ForeignKey("lessons.id"), nullable=False, index=True)
    completed_at = db.Column(db.DateTime, nullable=True)
    xp_earned = db.Column(db.Integer, default=0, nullable=False)
    last_viewed_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "user_id": self.user_id,
            "lesson_id": self.lesson_id,
            "completed": self.completed_at is not None,
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
            "xp_earned": self.xp_earned,
            "last_viewed_at": self.last_viewed_at.isoformat() if self.last_viewed_at else None,
        }

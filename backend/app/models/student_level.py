from app.extensions import db
from app.models.constants import StudentLevelValue
from app.models.mixins import TimestampMixin


class StudentLevel(db.Model, TimestampMixin):
    """Derived classification, recomputed by ProgressService._calculate_level()
    every time UserProgress changes. Never written to directly elsewhere.
    """

    __tablename__ = "student_levels"
    __table_args__ = (db.UniqueConstraint("user_id", "category_id", name="uq_student_level"),)

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False, index=True)
    category_id = db.Column(db.Integer, db.ForeignKey("categories.id"), nullable=False, index=True)
    level = db.Column(db.String(20), default=StudentLevelValue.BEGINNER, nullable=False)

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "user_id": self.user_id,
            "category_id": self.category_id,
            "level": self.level,
            "updated_at": self.updated_at.isoformat(),
        }

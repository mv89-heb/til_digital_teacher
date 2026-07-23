from app.extensions import db
from app.models.mixins import TimestampMixin


class SolutionStrategy(db.Model, TimestampMixin):
    """A fast-exam-solving strategy for a whole category (e.g. all number-series
    questions), not a single lesson — the same shortcut applies across many
    questions of that type, so duplicating it per-lesson would drift out of sync.

    Each rich-text field uses the shape {"format": "markdown", "body": "..."}.
    """

    __tablename__ = "solution_strategies"

    id = db.Column(db.Integer, primary_key=True)
    category_id = db.Column(db.Integer, db.ForeignKey("categories.id"), nullable=False, index=True)
    identification_tips = db.Column(db.JSON, nullable=False)
    normal_method = db.Column(db.JSON, nullable=False)
    fast_method = db.Column(db.JSON, nullable=False)
    shortcut_text = db.Column(db.JSON, nullable=True)
    target_time_seconds = db.Column(db.Integer, nullable=True)

    category = db.relationship("Category")

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "category_id": self.category_id,
            "identification_tips": self.identification_tips,
            "normal_method": self.normal_method,
            "fast_method": self.fast_method,
            "shortcut_text": self.shortcut_text,
            "target_time_seconds": self.target_time_seconds,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
        }

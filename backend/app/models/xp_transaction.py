from app.extensions import db
from app.models.mixins import TimestampMixin


class XPTransaction(db.Model, TimestampMixin):
    """Append-only XP ledger. User.xp_total is a denormalized running sum,
    kept in sync by XPService.award() — never written to directly elsewhere.
    """

    __tablename__ = "xp_transactions"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False, index=True)
    amount = db.Column(db.Integer, nullable=False)
    reason = db.Column(db.String(50), nullable=False)  # e.g. "question_correct", "lesson_completed"
    related_entity_type = db.Column(db.String(50), nullable=True)
    related_entity_id = db.Column(db.Integer, nullable=True)

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "user_id": self.user_id,
            "amount": self.amount,
            "reason": self.reason,
            "related_entity_type": self.related_entity_type,
            "related_entity_id": self.related_entity_id,
            "created_at": self.created_at.isoformat(),
        }

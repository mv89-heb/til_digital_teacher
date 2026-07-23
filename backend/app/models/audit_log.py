from datetime import datetime, timezone

from app.extensions import db


class AuditLog(db.Model):
    """Immutable record of an admin change, for accountability and rollback context.

    Written only through AuditService.log() — never updated or deleted.
    """

    __tablename__ = "audit_logs"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False, index=True)
    action = db.Column(db.String(20), nullable=False)  # create | update | delete
    entity_type = db.Column(db.String(50), nullable=False, index=True)  # e.g. "Question"
    entity_id = db.Column(db.Integer, nullable=False)
    changes = db.Column(db.JSON, nullable=True)  # {"before": {...}, "after": {...}}
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc), index=True)

    def to_dict(self):
        return {
            "id": self.id,
            "user_id": self.user_id,
            "action": self.action,
            "entity_type": self.entity_type,
            "entity_id": self.entity_id,
            "changes": self.changes,
            "created_at": self.created_at.isoformat(),
        }

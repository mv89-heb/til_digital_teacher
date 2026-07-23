from app.extensions import db
from app.models.audit_log import AuditLog


class AuditService:
    @staticmethod
    def log(user_id: int, action: str, entity_type: str, entity_id: int, changes: dict | None = None) -> AuditLog:
        """Record one admin change. Call this from any service that mutates
        admin-managed content (Question, Lesson, Category, Test, ...).

        action: "create" | "update" | "delete"
        changes: optional {"before": {...}, "after": {...}} snapshot
        """
        entry = AuditLog(
            user_id=user_id,
            action=action,
            entity_type=entity_type,
            entity_id=entity_id,
            changes=changes,
        )
        db.session.add(entry)
        db.session.commit()
        return entry

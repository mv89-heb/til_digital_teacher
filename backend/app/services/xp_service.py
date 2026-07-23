from app.extensions import db
from app.models.user import User
from app.models.xp_transaction import XPTransaction


class XPService:
    @staticmethod
    def award(
        user_id: int,
        amount: int,
        reason: str,
        related_entity_type: str | None = None,
        related_entity_id: int | None = None,
    ) -> int:
        """Record an XP transaction and bump the user's running total.
        Returns the user's new xp_total."""
        transaction = XPTransaction(
            user_id=user_id,
            amount=amount,
            reason=reason,
            related_entity_type=related_entity_type,
            related_entity_id=related_entity_id,
        )
        db.session.add(transaction)

        user = db.session.get(User, user_id)
        user.xp_total = (user.xp_total or 0) + amount

        db.session.commit()
        return user.xp_total

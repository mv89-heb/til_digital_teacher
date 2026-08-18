from app.extensions import db
from app.models.user import User
from app.models.xp_transaction import XPTransaction


class XPReconciliationService:
    @staticmethod
    def reconcile_user(user_id: int) -> dict:
        user = db.session.get(User, user_id)
        if not user:
            raise ValueError("User not found")
        calculated = sum((tx.amount or 0) for tx in XPTransaction.query.filter_by(user_id=user_id).all())
        before = user.xp_total or 0
        if before != calculated:
            user.xp_total = calculated
            db.session.commit()
        return {"user_id": user_id, "before": before, "after": calculated, "changed": before != calculated}

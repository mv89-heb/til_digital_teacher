from app.extensions import db
from app.models.solution_strategy import SolutionStrategy
from app.services.audit_service import AuditService
from app.utils.exceptions import AppError


class SolutionStrategyService:
    @staticmethod
    def list_strategies(category_id: int | None = None) -> list[dict]:
        query = SolutionStrategy.query
        if category_id is not None:
            query = query.filter_by(category_id=category_id)
        return [s.to_dict() for s in query.all()]

    @staticmethod
    def get_strategy(strategy_id: int) -> SolutionStrategy:
        strategy = db.session.get(SolutionStrategy, strategy_id)
        if not strategy:
            raise AppError("Solution strategy not found", status_code=404)
        return strategy

    @staticmethod
    def create_strategy(data: dict, admin_user_id: int) -> dict:
        strategy = SolutionStrategy(
            category_id=data["category_id"],
            identification_tips=data["identification_tips"],
            normal_method=data["normal_method"],
            fast_method=data["fast_method"],
            shortcut_text=data.get("shortcut_text"),
            target_time_seconds=data.get("target_time_seconds"),
        )
        db.session.add(strategy)
        db.session.commit()

        AuditService.log(
            admin_user_id, "create", "SolutionStrategy", strategy.id, {"after": strategy.to_dict()}
        )
        return strategy.to_dict()

    @staticmethod
    def update_strategy(strategy_id: int, data: dict, admin_user_id: int) -> dict:
        strategy = SolutionStrategyService.get_strategy(strategy_id)
        before = strategy.to_dict()

        for field in (
            "category_id",
            "identification_tips",
            "normal_method",
            "fast_method",
            "shortcut_text",
            "target_time_seconds",
        ):
            if field in data:
                setattr(strategy, field, data[field])

        db.session.commit()

        AuditService.log(
            admin_user_id,
            "update",
            "SolutionStrategy",
            strategy.id,
            {"before": before, "after": strategy.to_dict()},
        )
        return strategy.to_dict()

    @staticmethod
    def delete_strategy(strategy_id: int, admin_user_id: int) -> None:
        strategy = SolutionStrategyService.get_strategy(strategy_id)
        before = strategy.to_dict()

        db.session.delete(strategy)
        db.session.commit()

        AuditService.log(
            admin_user_id, "delete", "SolutionStrategy", strategy_id, {"before": before}
        )

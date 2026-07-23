from app.extensions import db
from app.models.category import Category
from app.services.audit_service import AuditService
from app.utils.exceptions import AppError

_FIELDS = ("name", "description", "type", "icon", "thumbnail_url", "status", "parent_id", "order")


class CategoryService:
    @staticmethod
    def list_categories() -> list[dict]:
        categories = Category.query.order_by(Category.order).all()
        return [c.to_dict() for c in categories]

    @staticmethod
    def get_category(category_id: int) -> Category:
        category = db.session.get(Category, category_id)
        if not category:
            raise AppError("Category not found", status_code=404)
        return category

    @staticmethod
    def create_category(data: dict, admin_user_id: int) -> dict:
        category = Category(**{field: data[field] for field in _FIELDS if field in data})
        db.session.add(category)
        db.session.commit()

        AuditService.log(
            admin_user_id, "create", "Category", category.id, {"after": category.to_dict()}
        )
        return category.to_dict()

    @staticmethod
    def update_category(category_id: int, data: dict, admin_user_id: int) -> dict:
        category = CategoryService.get_category(category_id)
        before = category.to_dict()

        for field in _FIELDS:
            if field in data:
                setattr(category, field, data[field])

        db.session.commit()

        AuditService.log(
            admin_user_id,
            "update",
            "Category",
            category.id,
            {"before": before, "after": category.to_dict()},
        )
        return category.to_dict()

    @staticmethod
    def delete_category(category_id: int, admin_user_id: int) -> None:
        category = CategoryService.get_category(category_id)
        before = category.to_dict()

        db.session.delete(category)
        db.session.commit()

        AuditService.log(admin_user_id, "delete", "Category", category_id, {"before": before})

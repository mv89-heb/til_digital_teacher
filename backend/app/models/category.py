from app.extensions import db
from app.models.constants import ContentStatus
from app.models.mixins import TimestampMixin


class Category(db.Model, TimestampMixin):
    __tablename__ = "categories"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), nullable=False)
    description = db.Column(db.Text, nullable=True)
    type = db.Column(db.String(20), nullable=False, index=True)  # see CategoryType
    icon = db.Column(db.String(50), nullable=True)  # e.g. a lucide-react icon name or emoji
    thumbnail_url = db.Column(db.String(255), nullable=True)
    status = db.Column(db.String(20), default=ContentStatus.DRAFT, nullable=False, index=True)
    parent_id = db.Column(db.Integer, db.ForeignKey("categories.id"), nullable=True)
    order = db.Column(db.Integer, default=0, nullable=False)

    children = db.relationship(
        "Category", backref=db.backref("parent", remote_side=[id]), cascade="all"
    )
    lessons = db.relationship(
        "Lesson", back_populates="category", cascade="all, delete-orphan", order_by="Lesson.order"
    )

    def to_dict(self, include_children: bool = False) -> dict:
        data = {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "type": self.type,
            "icon": self.icon,
            "thumbnail_url": self.thumbnail_url,
            "status": self.status,
            "parent_id": self.parent_id,
            "order": self.order,
            "lesson_count": len(self.lessons),
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
        }
        if include_children:
            data["children"] = [c.to_dict() for c in self.children]
        return data

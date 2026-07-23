from app.extensions import db
from app.models.constants import ContentStatus
from app.models.mixins import TimestampMixin


class Lesson(db.Model, TimestampMixin):
    __tablename__ = "lessons"

    id = db.Column(db.Integer, primary_key=True)
    category_id = db.Column(db.Integer, db.ForeignKey("categories.id"), nullable=False, index=True)
    title = db.Column(db.String(200), nullable=False)
    slug = db.Column(db.String(220), nullable=False, unique=True, index=True)
    description = db.Column(db.Text, nullable=True)
    status = db.Column(db.String(20), default=ContentStatus.DRAFT, nullable=False, index=True)
    difficulty_level = db.Column(db.String(20), nullable=True)  # see LessonDifficulty
    estimated_duration = db.Column(db.Integer, nullable=True)  # minutes
    icon = db.Column(db.String(50), nullable=True)
    thumbnail_url = db.Column(db.String(255), nullable=True)
    order = db.Column(db.Integer, default=0, nullable=False)

    category = db.relationship("Category", back_populates="lessons")
    content_blocks = db.relationship(
        "LessonContent",
        back_populates="lesson",
        cascade="all, delete-orphan",
        order_by="LessonContent.order",
    )

    def to_dict(self, include_content: bool = True) -> dict:
        data = {
            "id": self.id,
            "title": self.title,
            "slug": self.slug,
            "description": self.description,
            "status": self.status,
            "difficulty_level": self.difficulty_level,
            "estimated_duration": self.estimated_duration,
            "icon": self.icon,
            "thumbnail_url": self.thumbnail_url,
            "order": self.order,
            "total_blocks": len(self.content_blocks),
            "category": {
                "id": self.category.id,
                "name": self.category.name,
                "type": self.category.type,
            },
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
        }
        if include_content:
            data["content_blocks"] = [block.to_dict() for block in self.content_blocks]
        return data

from app.extensions import db
from app.models.mixins import TimestampMixin


class LessonContent(db.Model, TimestampMixin):
    """One content block within a lesson.

    Two independent axes, both plain strings (not DB enums) so new values
    never require a migration:
      - section: the block's pedagogical role (see LessonSection)
      - block_type: the block's rendering format (see BlockType)

    `content` is JSON and its shape depends on block_type, e.g.:
      text     -> {"format": "markdown", "body": "..."}
      image    -> {"url": "...", "alt": "...", "caption": "..."}
      video    -> {"url": "...", "caption": "..."}
      table    -> {"headers": [...], "rows": [[...], ...]}
      formula  -> {"latex": "..."}
      interactive       -> {"component": "...", "props": {...}}
      embedded_question -> {"question_id": 123}

    `metadata` is a free-form JSON bag for anything that isn't part of the
    rendered content itself (author notes, tags, etc.) — kept separate so
    `content` stays a clean, renderable payload for the frontend.
    """

    __tablename__ = "lesson_contents"

    id = db.Column(db.Integer, primary_key=True)
    lesson_id = db.Column(db.Integer, db.ForeignKey("lessons.id"), nullable=False, index=True)
    section = db.Column(db.String(30), nullable=False, index=True)
    block_type = db.Column(db.String(30), nullable=False)
    order = db.Column(db.Integer, default=0, nullable=False)
    content = db.Column(db.JSON, nullable=False)
    block_metadata = db.Column(db.JSON, default=dict)

    lesson = db.relationship("Lesson", back_populates="content_blocks")

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "lesson_id": self.lesson_id,
            "section": self.section,
            "type": self.block_type,
            "order": self.order,
            "content": self.content,
            "metadata": self.block_metadata or {},
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
        }

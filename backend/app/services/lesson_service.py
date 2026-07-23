from app.extensions import db
from app.models.constants import BlockType
from app.models.lesson import Lesson
from app.models.lesson_content import LessonContent
from app.services.audit_service import AuditService
from app.services.question_service import QuestionService
from app.utils.block_content import validate_block_content
from app.utils.exceptions import AppError
from app.utils.slugify import slugify

_LESSON_FIELDS = (
    "category_id",
    "title",
    "description",
    "status",
    "difficulty_level",
    "estimated_duration",
    "icon",
    "thumbnail_url",
    "order",
)


def _unique_slug(base_text: str, exclude_lesson_id: int | None = None) -> str:
    base_slug = slugify(base_text)
    slug = base_slug
    suffix = 2
    while True:
        query = Lesson.query.filter_by(slug=slug)
        if exclude_lesson_id is not None:
            query = query.filter(Lesson.id != exclude_lesson_id)
        if not query.first():
            return slug
        slug = f"{base_slug}-{suffix}"
        suffix += 1


class LessonService:
    @staticmethod
    def list_lessons(category_id: int | None = None) -> list[dict]:
        query = Lesson.query
        if category_id is not None:
            query = query.filter_by(category_id=category_id)
        lessons = query.order_by(Lesson.order).all()
        return [lesson.to_dict(include_content=False) for lesson in lessons]

    @staticmethod
    def get_lesson(lesson_id: int) -> Lesson:
        lesson = db.session.get(Lesson, lesson_id)
        if not lesson:
            raise AppError("Lesson not found", status_code=404)
        return lesson

    @staticmethod
    def create_lesson(data: dict, admin_user_id: int) -> dict:
        requested_slug = data.get("slug")
        if requested_slug:
            slug = slugify(requested_slug)
            if Lesson.query.filter_by(slug=slug).first():
                raise AppError(f"Slug '{slug}' is already in use", status_code=409)
        else:
            slug = _unique_slug(data["title"])

        lesson = Lesson(
            slug=slug,
            **{field: data[field] for field in _LESSON_FIELDS if field in data},
        )
        db.session.add(lesson)
        db.session.commit()

        AuditService.log(
            admin_user_id, "create", "Lesson", lesson.id, {"after": lesson.to_dict()}
        )
        return lesson.to_dict()

    @staticmethod
    def update_lesson(lesson_id: int, data: dict, admin_user_id: int) -> dict:
        lesson = LessonService.get_lesson(lesson_id)
        before = lesson.to_dict()

        if "slug" in data and data["slug"]:
            new_slug = slugify(data["slug"])
            if Lesson.query.filter(Lesson.slug == new_slug, Lesson.id != lesson.id).first():
                raise AppError(f"Slug '{new_slug}' is already in use", status_code=409)
            lesson.slug = new_slug

        for field in _LESSON_FIELDS:
            if field in data:
                setattr(lesson, field, data[field])

        db.session.commit()

        AuditService.log(
            admin_user_id, "update", "Lesson", lesson.id, {"before": before, "after": lesson.to_dict()}
        )
        return lesson.to_dict()

    @staticmethod
    def delete_lesson(lesson_id: int, admin_user_id: int) -> None:
        lesson = LessonService.get_lesson(lesson_id)
        before = lesson.to_dict()

        db.session.delete(lesson)
        db.session.commit()

        AuditService.log(admin_user_id, "delete", "Lesson", lesson_id, {"before": before})

    # --- content blocks ---

    @staticmethod
    def add_content_block(lesson_id: int, data: dict, admin_user_id: int) -> dict:
        LessonService.get_lesson(lesson_id)  # 404 if lesson missing
        validate_block_content(data["block_type"], data["content"])
        if data["block_type"] == BlockType.EMBEDDED_QUESTION:
            QuestionService.get_question(data["content"]["question_id"])  # 404 if question missing

        block = LessonContent(
            lesson_id=lesson_id,
            section=data["section"],
            block_type=data["block_type"],
            order=data.get("order", 0),
            content=data["content"],
            block_metadata=data.get("metadata", {}),
        )
        db.session.add(block)
        db.session.commit()

        AuditService.log(
            admin_user_id, "create", "LessonContent", block.id, {"after": block.to_dict()}
        )
        return block.to_dict()

    @staticmethod
    def get_content_block(block_id: int) -> LessonContent:
        block = db.session.get(LessonContent, block_id)
        if not block:
            raise AppError("Lesson content block not found", status_code=404)
        return block

    @staticmethod
    def update_content_block(block_id: int, data: dict, admin_user_id: int) -> dict:
        block = LessonService.get_content_block(block_id)
        before = block.to_dict()

        if "block_type" in data or "content" in data:
            effective_type = data.get("block_type", block.block_type)
            effective_content = data.get("content", block.content)
            validate_block_content(effective_type, effective_content)
            if effective_type == BlockType.EMBEDDED_QUESTION:
                QuestionService.get_question(effective_content["question_id"])  # 404 if missing

        if "metadata" in data:
            data = {**data, "block_metadata": data.pop("metadata")}
        for field in ("section", "block_type", "order", "content", "block_metadata"):
            if field in data:
                setattr(block, field, data[field])

        db.session.commit()

        AuditService.log(
            admin_user_id,
            "update",
            "LessonContent",
            block.id,
            {"before": before, "after": block.to_dict()},
        )
        return block.to_dict()

    @staticmethod
    def delete_content_block(block_id: int, admin_user_id: int) -> None:
        block = LessonService.get_content_block(block_id)
        before = block.to_dict()

        db.session.delete(block)
        db.session.commit()

        AuditService.log(admin_user_id, "delete", "LessonContent", block_id, {"before": before})

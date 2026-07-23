from app.extensions import db
from app.models.category import Category
from app.models.constants import ContentStatus
from app.models.lesson import Lesson
from app.services.question_service import QuestionService
from app.utils.exceptions import AppError


class LearningService:
    """Public, read-only, unauthenticated. Only PUBLISHED content is ever
    returned here — draft/archived content is visible only through the
    admin API. (Gap found during Stage 1 finalization audit: the original
    implementation returned all content regardless of status.)
    """

    @staticmethod
    def get_categories_overview() -> list[dict]:
        categories = (
            Category.query.filter_by(parent_id=None, status=ContentStatus.PUBLISHED)
            .order_by(Category.order)
            .all()
        )
        result = []
        for category in categories:
            published_lessons = [
                lesson for lesson in category.lessons if lesson.status == ContentStatus.PUBLISHED
            ]
            result.append(
                {
                    "id": category.id,
                    "name": category.name,
                    "description": category.description,
                    "type": category.type,
                    "icon": category.icon,
                    "thumbnail_url": category.thumbnail_url,
                    "order": category.order,
                    "status": category.status,
                    "lesson_count": len(published_lessons),
                    "lessons": [lesson.to_dict(include_content=False) for lesson in published_lessons],
                }
            )
        return result

    @staticmethod
    def get_lesson_detail(lesson_id: int) -> dict:
        lesson = db.session.get(Lesson, lesson_id)
        if not lesson or lesson.status != ContentStatus.PUBLISHED:
            raise AppError("Lesson not found", status_code=404)

        data = lesson.to_dict(include_content=True)
        data["content_blocks"] = QuestionService.resolve_embedded_blocks(
            data["content_blocks"], published_only=True
        )
        return data

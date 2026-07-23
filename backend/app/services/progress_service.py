from datetime import datetime, timezone

from app.extensions import db
from app.models.category import Category
from app.models.constants import ContentStatus, StudentLevelValue
from app.models.lesson import Lesson
from app.models.student_level import StudentLevel
from app.models.user import User
from app.models.user_lesson_progress import UserLessonProgress
from app.models.user_progress import UserProgress

MIN_ATTEMPTS_FOR_RATING = 5
ADVANCED_MIN_ATTEMPTS = 15


class ProgressService:
    """Keeps UserProgress/StudentLevel in sync (called from PracticeService
    right after each PracticeAttempt / lesson completion — same pattern as
    XPService keeping User.xp_total in sync with XPTransaction), and
    assembles the read-only dashboard summary.
    """

    @staticmethod
    def _get_or_create_progress(user_id: int, category_id: int) -> UserProgress:
        progress = UserProgress.query.filter_by(user_id=user_id, category_id=category_id).first()
        if not progress:
            progress = UserProgress(user_id=user_id, category_id=category_id)
            db.session.add(progress)
            db.session.flush()
        return progress

    @staticmethod
    def _get_or_create_level(user_id: int, category_id: int) -> StudentLevel:
        level = StudentLevel.query.filter_by(user_id=user_id, category_id=category_id).first()
        if not level:
            level = StudentLevel(user_id=user_id, category_id=category_id)
            db.session.add(level)
            db.session.flush()
        return level

    @staticmethod
    def _calculate_level(attempted: int, correct: int) -> str:
        """Simple, documented heuristic based on accuracy + volume.
        Does not yet factor in solving time or hint usage — neither is
        tracked anywhere in the system yet (see Stage 4 planning notes).
        """
        if attempted < MIN_ATTEMPTS_FOR_RATING:
            return StudentLevelValue.BEGINNER

        accuracy = correct / attempted
        if accuracy < 0.5:
            return StudentLevelValue.BASIC
        if accuracy < 0.7:
            return StudentLevelValue.INTERMEDIATE
        if accuracy < 0.9:
            return StudentLevelValue.EXAM_READY
        if attempted >= ADVANCED_MIN_ATTEMPTS:
            return StudentLevelValue.ADVANCED
        return StudentLevelValue.EXAM_READY

    @staticmethod
    def record_practice_attempt(user_id: int, category_id: int, is_correct: bool, xp_earned: int) -> None:
        progress = ProgressService._get_or_create_progress(user_id, category_id)
        progress.questions_attempted += 1
        if is_correct:
            progress.questions_correct += 1
        progress.xp_earned += xp_earned
        progress.last_practiced_at = datetime.now(timezone.utc)

        level = ProgressService._get_or_create_level(user_id, category_id)
        level.level = ProgressService._calculate_level(progress.questions_attempted, progress.questions_correct)

        db.session.commit()

    @staticmethod
    def record_lesson_completion(user_id: int, category_id: int, xp_earned: int) -> None:
        progress = ProgressService._get_or_create_progress(user_id, category_id)
        progress.lessons_completed += 1
        progress.xp_earned += xp_earned
        db.session.commit()

    @staticmethod
    def get_dashboard_summary(user_id: int) -> dict:
        user = db.session.get(User, user_id)

        categories = (
            Category.query.filter_by(parent_id=None, status=ContentStatus.PUBLISHED)
            .order_by(Category.order)
            .all()
        )
        progress_by_category = {p.category_id: p for p in UserProgress.query.filter_by(user_id=user_id).all()}
        level_by_category = {lv.category_id: lv for lv in StudentLevel.query.filter_by(user_id=user_id).all()}

        category_summaries = []
        total_attempted = 0
        total_correct = 0
        total_lessons_completed = 0
        total_lessons_available = 0

        for category in categories:
            lessons_total = Lesson.query.filter_by(
                category_id=category.id, status=ContentStatus.PUBLISHED
            ).count()
            progress = progress_by_category.get(category.id)
            level = level_by_category.get(category.id)

            attempted = progress.questions_attempted if progress else 0
            correct = progress.questions_correct if progress else 0
            lessons_completed = progress.lessons_completed if progress else 0
            category_xp = progress.xp_earned if progress else 0

            category_summaries.append(
                {
                    "category_id": category.id,
                    "name": category.name,
                    "icon": category.icon,
                    "type": category.type,
                    "questions_attempted": attempted,
                    "questions_correct": correct,
                    "accuracy_percent": round(100 * correct / attempted) if attempted else 0,
                    "lessons_completed": lessons_completed,
                    "lessons_total": lessons_total,
                    "xp_earned": category_xp,
                    "level": level.level if level else StudentLevelValue.BEGINNER,
                }
            )

            total_attempted += attempted
            total_correct += correct
            total_lessons_completed += lessons_completed
            total_lessons_available += lessons_total

        lesson_progress_rows = (
            UserLessonProgress.query.filter_by(user_id=user_id)
            .order_by(UserLessonProgress.last_viewed_at.desc())
            .all()
        )
        in_progress = []
        completed = []
        continue_learning = None

        for row in lesson_progress_rows:
            lesson = db.session.get(Lesson, row.lesson_id)
            if not lesson or lesson.status != ContentStatus.PUBLISHED:
                continue

            entry = {
                "lesson_id": lesson.id,
                "title": lesson.title,
                "category_name": lesson.category.name,
                "last_viewed_at": row.last_viewed_at.isoformat() if row.last_viewed_at else None,
            }
            if row.completed_at:
                completed.append({**entry, "completed_at": row.completed_at.isoformat()})
            else:
                in_progress.append(entry)
                if continue_learning is None:
                    continue_learning = entry

        return {
            "xp_total": user.xp_total or 0,
            "categories": category_summaries,
            "in_progress_lessons": in_progress,
            "completed_lessons": completed,
            "continue_learning": continue_learning,
            "stats": {
                "total_questions_attempted": total_attempted,
                "total_questions_correct": total_correct,
                "overall_accuracy_percent": round(100 * total_correct / total_attempted)
                if total_attempted
                else 0,
                "total_lessons_completed": total_lessons_completed,
                "total_lessons_available": total_lessons_available,
            },
        }

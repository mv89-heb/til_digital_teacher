"""Idempotent demo-data seed for Render/Neon deployments.

The Render service currently invokes this script before Gunicorn. The script
therefore upgrades the configured database first, then creates the minimal
published learning content required by the application. It never drops data.
"""

import os

from flask_migrate import upgrade
from werkzeug.security import generate_password_hash

from app import create_app
from app.extensions import db
from app.models.answer import Answer
from app.models.category import Category
from app.models.constants import (
    BlockType,
    CategoryType,
    ContentStatus,
    LessonDifficulty,
    LessonSection,
    QuestionDifficulty,
)
from app.models.lesson import Lesson
from app.models.lesson_content import LessonContent
from app.models.question import Question
from app.models.user import User
from app.utils.slugify import slugify

ADMIN_EMAIL = "admin@til-teacher.local"
ADMIN_PASSWORD = os.getenv("SEED_ADMIN_PASSWORD", "Admin12345!")


def _rich(body: str) -> dict:
    return {"format": "markdown", "body": body.strip()}


def _answers(options: list[tuple[str, bool, str]]) -> list[Answer]:
    return [
        Answer(
            answer_text=text,
            is_correct=is_correct,
            explanation_if_selected=_rich(explanation),
            order=index,
        )
        for index, (text, is_correct, explanation) in enumerate(options, start=1)
    ]


def seed_demo_data() -> dict:
    """Create the admin, published quantitative category and demo lesson."""
    admin = User.query.filter_by(email=ADMIN_EMAIL).first()
    if not admin:
        admin = User(
            email=ADMIN_EMAIL,
            password_hash=generate_password_hash(ADMIN_PASSWORD),
            role="admin",
        )
        db.session.add(admin)
        db.session.flush()

    category = Category.query.filter_by(
        name="חשיבה כמותית", type=CategoryType.QUANTITATIVE
    ).first()

    if category is None:
        category = Category(
            name="חשיבה כמותית",
            description="שאלות מספרים, אחוזים, יחסים וסדרות — הבסיס הכמותי של מבחן תיל.",
            type=CategoryType.QUANTITATIVE,
            icon="calculator",
            status=ContentStatus.PUBLISHED,
            order=1,
        )
        db.session.add(category)
        db.session.flush()

    lesson = Lesson.query.filter_by(
        category_id=category.id,
        slug=slugify("סדרות מספרים – מציאת האיבר הבא"),
    ).first()

    if lesson is None:
        lesson = Lesson(
            category_id=category.id,
            title="סדרות מספרים – מציאת האיבר הבא",
            slug=slugify("סדרות מספרים – מציאת האיבר הבא"),
            description="לומדים לזהות את החוק שמניע סדרת מספרים ולמצוא את האיבר הבא במהירות.",
            status=ContentStatus.PUBLISHED,
            difficulty_level=LessonDifficulty.BEGINNER,
            estimated_duration=12,
            icon="trending-up",
            order=1,
        )
        db.session.add(lesson)
        db.session.flush()

        blocks = [
            (
                LessonSection.SIMPLE_EXPLANATION,
                """
סדרת מספרים היא רשימת מספרים שפועלת לפי חוק מסוים.
התחילו בבדיקת ההפרש בין שני איברים סמוכים, ואז ודאו שהחוק ממשיך גם בזוג הבא.
""",
            ),
            (
                LessonSection.NORMAL_EXPLANATION,
                """
הסוגים הנפוצים הם סדרה חשבונית עם הפרש קבוע, סדרה הנדסית עם יחס קבוע,
סדרה שבה ההפרשים עצמם משתנים לפי חוק, וסדרה מתחלפת שבה יש שני תת-רצפים.
""",
            ),
            (
                LessonSection.SOLVED_EXAMPLE,
                """
3, 7, 11, 15, ?

ההפרש הוא 4 בכל פעם, ולכן האיבר הבא הוא 19.
""",
            ),
            (
                LessonSection.NORMAL_METHOD,
                """
1. בדקו הפרשים.
2. אם הם אינם קבועים, בדקו יחס.
3. אם גם היחס אינו קבוע, בדקו את סדרת ההפרשים או שני תת-רצפים.
""",
            ),
            (
                LessonSection.FAST_METHOD,
                """
בתרגול מתוזמן אפשר לחשב הפרש ראשון, לבדוק את האפשרויות ולוודא עם איבר נוסף
רק אם התשובה אינה חד-משמעית.
""",
            ),
            (
                LessonSection.COMMON_MISTAKES,
                """
אל תניחו שהחוק ממשיך רק משום שהוא מתאים לשני האיברים הראשונים.
בדקו לפחות זוג נוסף, והיזהרו מסימנים של סדרה מתחלפת.
""",
            ),
            (
                LessonSection.SUMMARY,
                """
זכרו: הפרש → יחס → הפרשי-הפרשים → תת-רצפים.
המטרה היא לזהות את החוק במהירות ובדיוק.
""",
            ),
        ]

        for order, (section, body) in enumerate(blocks, start=1):
            db.session.add(
                LessonContent(
                    lesson_id=lesson.id,
                    section=section,
                    block_type=BlockType.TEXT,
                    order=order,
                    content=_rich(body),
                    block_metadata={},
                )
            )

        questions = [
            Question(
                category_id=category.id,
                lesson_id=lesson.id,
                difficulty=QuestionDifficulty.EASY,
                status=ContentStatus.PUBLISHED,
                body=_rich("מהו האיבר הבא: 2, 5, 8, 11, ?"),
                solution_text=_rich("ההפרש הקבוע הוא 3, לכן 11 + 3 = 14."),
                recommended_time_seconds=8,
                answers=_answers([
                    ("14", True, "נכון. ההפרש הקבוע הוא 3."),
                    ("13", False, "בדקו את ההפרש בין האיברים."),
                    ("15", False, "ההפרש אינו 4."),
                    ("12", False, "ההפרש אינו 1."),
                ]),
            ),
            Question(
                category_id=category.id,
                lesson_id=lesson.id,
                difficulty=QuestionDifficulty.EASY,
                status=ContentStatus.PUBLISHED,
                body=_rich("מהו האיבר הבא: 3, 6, 12, 24, ?"),
                solution_text=_rich("כל איבר מוכפל ב-2, לכן התשובה היא 48."),
                recommended_time_seconds=10,
                answers=_answers([
                    ("48", True, "נכון. היחס הקבוע הוא 2."),
                    ("36", False, "בדקו יחס ולא הפרש."),
                    ("30", False, "הסדרה אינה פועלת בחיבור קבוע."),
                    ("50", False, "24 כפול 2 הוא 48."),
                ]),
            ),
            Question(
                category_id=category.id,
                lesson_id=lesson.id,
                difficulty=QuestionDifficulty.MEDIUM,
                status=ContentStatus.PUBLISHED,
                body=_rich("מהו האיבר הבא: 1, 4, 9, 16, ?"),
                solution_text=_rich("אלה ריבועים: 1², 2², 3², 4², ולכן הבא הוא 5² = 25."),
                recommended_time_seconds=15,
                answers=_answers([
                    ("25", True, "נכון."),
                    ("20", False, "בדקו את סדרת הריבועים."),
                    ("22", False, "ההפרשים הם 3, 5, 7 ואז 9."),
                    ("24", False, "האיבר הבא הוא 25."),
                ]),
            ),
            Question(
                category_id=category.id,
                lesson_id=lesson.id,
                difficulty=QuestionDifficulty.MEDIUM,
                status=ContentStatus.PUBLISHED,
                body=_rich("מהו האיבר הבא: 100, 90, 81, 73, ?"),
                solution_text=_rich("ההפרשים הם 10-, 9-, 8-, ולכן הבא הוא 7-: התשובה 66."),
                recommended_time_seconds=15,
                answers=_answers([
                    ("66", True, "נכון."),
                    ("65", False, "ההפרש הבא הוא 7-."),
                    ("64", False, "ההפרשים משתנים."),
                    ("70", False, "צריך להפחית 7."),
                ]),
            ),
            Question(
                category_id=category.id,
                lesson_id=lesson.id,
                difficulty=QuestionDifficulty.EXAM,
                status=ContentStatus.PUBLISHED,
                body=_rich("מהו האיבר הבא: 2, 10, 4, 8, 6, 6, ?"),
                solution_text=_rich("בתת-הרצף האי-זוגי: 2, 4, 6, ולכן הבא הוא 8."),
                recommended_time_seconds=20,
                answers=_answers([
                    ("8", True, "נכון. הפרידו למקומות זוגיים ואי-זוגיים."),
                    ("4", False, "זה לא האיבר הבא בתת-הרצף האי-זוגי."),
                    ("10", False, "זה שייך לתת-הרצף השני."),
                    ("2", False, "התת-רצף האי-זוגי עולה ב-2."),
                ]),
            ),
        ]
        db.session.add_all(questions)

    db.session.commit()
    return {
        "admin_email": ADMIN_EMAIL,
        "category_id": category.id,
        "lesson_id": lesson.id,
        "already_seeded": False,
    }


if __name__ == "__main__":
    # Render executes seed.py before Gunicorn. Use the real DATABASE_URL
    # supplied by Render/Neon, but do not require a production JWT secret for
    # this non-serving migration/seed process.
    app = create_app("development")
    with app.app_context():
        print("Running database migrations...")
        upgrade()
        print("Database migrations complete.")
        print("Seed complete:", seed_demo_data())

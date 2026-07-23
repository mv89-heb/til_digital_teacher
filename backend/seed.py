"""Seed demo data: one full quantitative-reasoning lesson + solution strategy.

Usage:
    FLASK_ENV=development DATABASE_URL=... python seed.py

Idempotent: safe to run more than once — it checks for the admin user and the
seed category before creating anything, so re-running never duplicates data.
"""

import os

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
from app.models.solution_strategy import SolutionStrategy
from app.models.user import User
from app.utils.slugify import slugify

ADMIN_EMAIL = "admin@til-teacher.local"
ADMIN_PASSWORD = os.getenv("SEED_ADMIN_PASSWORD", "Admin12345!")


def _rich(body: str) -> dict:
    return {"format": "markdown", "body": body.strip()}


def seed_demo_data() -> dict:
    """Create the admin user, demo category, one full lesson, and one
    solution strategy — unless they already exist. Returns a summary dict.
    """
    admin = User.query.filter_by(email=ADMIN_EMAIL).first()
    if not admin:
        admin = User(
            email=ADMIN_EMAIL,
            password_hash=generate_password_hash(ADMIN_PASSWORD),
            role="admin",
        )
        db.session.add(admin)
        db.session.commit()

    category = Category.query.filter_by(name="חשיבה כמותית", type=CategoryType.QUANTITATIVE).first()
    if category:
        return {
            "admin_email": ADMIN_EMAIL,
            "category_id": category.id,
            "lesson_id": category.lessons[0].id if category.lessons else None,
            "already_seeded": True,
        }

    category = Category(
        name="חשיבה כמותית",
        description="שאלות מספרים, אחוזים, יחסים וסדרות — הבסיס הכמותי של מבחן תיל.",
        type=CategoryType.QUANTITATIVE,
        icon="calculator",
        status=ContentStatus.PUBLISHED,
        order=1,
    )
    db.session.add(category)
    db.session.commit()

    lesson = Lesson(
        category_id=category.id,
        title="סדרות מספרים – מציאת האיבר הבא",
        slug=slugify("סדרות מספרים – מציאת האיבר הבא"),
        description="לומדים לזהות את החוק שמניע סדרת מספרים, ולמצוא את האיבר הבא במהירות תחת לחץ זמן.",
        status=ContentStatus.PUBLISHED,
        difficulty_level=LessonDifficulty.BEGINNER,
        estimated_duration=12,
        icon="trending-up",
        order=1,
    )
    db.session.add(lesson)
    db.session.commit()

    blocks = [
        (
            LessonSection.SIMPLE_EXPLANATION,
            """
סדרת מספרים היא רשימת מספרים שמסודרים לפי חוק קבוע וברור. המשימה שלך היא לגלות
מהו החוק הזה, ואז להשתמש בו כדי למצוא את המספר הבא בסדרה.

הדרך הכי פשוטה להתחיל: תסתכל על שני המספרים הראשונים בסדרה, ותשאל את עצמך —
**"מה עשיתי כדי לעבור מהמספר הראשון לשני?"** הוספתי מספר קבוע? הכפלתי? חיסרתי?

לאחר מכן תבדוק: **האם אותו דבר בדיוק קורה גם בין המספר השני לשלישי?**
אם כן — מצאת את החוק, ואפשר להמשיך אותו הלאה כדי למצוא את התשובה.
""",
        ),
        (
            LessonSection.NORMAL_EXPLANATION,
            """
ברוב שאלות הסדרות במבחן, החוק שייך לאחד מכמה סוגים נפוצים:

1. **סדרה חשבונית (הפרש קבוע)** — בין כל שני איברים סמוכים יש תמיד את אותו הפרש.
   לדוגמה: 2, 5, 8, 11 — כל פעם מוסיפים 3.

2. **סדרה הנדסית (יחס קבוע)** — כל איבר מתקבל מהקודם על ידי הכפלה באותו מספר.
   לדוגמה: 3, 6, 12, 24 — כל פעם מכפילים ב-2.

3. **סדרה עם הפרשים משתנים באופן קבוע** — ההפרש עצמו גדל או קטן לפי חוק.
   לדוגמה: 1, 2, 4, 7, 11 — ההפרשים הם 1, 2, 3, 4 (כל הפרש גדול באחד מהקודם).

4. **סדרה מתחלפת (זוגי/אי-זוגי)** — יש שני חוקים שונים, אחד למקומות הזוגיים
   ואחד למקומות האי-זוגיים בסדרה.

חשוב להבין: לא כל סדרה היא חשבונית. אם ההפרש בין האיברים הראשונים לא קבוע,
אל תוותרו מיד — בדקו יחס (חילוק), ואם גם זה לא עובד, בדקו את ההפרשים בין ההפרשים.
""",
        ),
        (
            LessonSection.SOLVED_EXAMPLE,
            """
**שאלה:** מהו האיבר הבא בסדרה: 3, 7, 11, 15, ?

**שלב 1 — בדיקת הפרש בין שני האיברים הראשונים:**
7 − 3 = 4

**שלב 2 — בדיקה שההפרש חוזר על עצמו:**
11 − 7 = 4
15 − 11 = 4

ההפרש קבוע ושווה ל-4 לאורך כל הסדרה — זו סדרה חשבונית.

**שלב 3 — הפעלת החוק על האיבר האחרון:**
15 + 4 = **19**

**תשובה: 19**
""",
        ),
        (
            LessonSection.NORMAL_METHOD,
            """
כדי לפתור כל שאלת סדרה בצורה שיטתית ובטוחה:

1. חשבו את ההפרש בין כל זוג איברים סמוכים בסדרה (לא רק בין הראשונים).
2. אם כל ההפרשים שווים — זו סדרה חשבונית. הוסיפו את ההפרש לאיבר האחרון.
3. אם ההפרשים לא שווים — בדקו את **היחס** בין האיברים (חלקו איבר באיבר שלפניו).
   אם היחס קבוע — זו סדרה הנדסית. הכפילו את האיבר האחרון ביחס.
4. אם גם היחס לא קבוע — כתבו את רשימת ההפרשים בנפרד ובדקו אם *הם* יוצרים
   חוק (סדרה של הפרשים).
5. אם יש חשד לסדרה מתחלפת — הפרידו את הסדרה לשני תת-רצפים (מקומות אי-זוגיים
   ומקומות זוגיים) ובדקו כל אחד בנפרד.
""",
        ),
        (
            LessonSection.FAST_METHOD,
            """
במבחן יש לחץ זמן, ואתם לא צריכים להוכיח את החוק — רק למצוא את התשובה הנכונה
מתוך האפשרויות שכבר נתונות לכם.

**קיצור הדרך:**
1. חשבו רק את ההפרש הראשון (בין האיבר הראשון לשני).
2. הוסיפו אותו לאיבר האחרון בסדרה וקבלו תשובה משוערת.
3. חפשו את התשובה הזו ברשימת האפשרויות. אם היא שם — **סמנו ועברו הלאה מיד**,
   אין צורך לבדוק את שאר ההפרשים.
4. רק אם התשובה המשוערת **לא** מופיעה באפשרויות, או שיש שתי אפשרויות קרובות —
   אז חוזרים לשיטה הרגילה ובודקים הפרש שני ושלישי.

**זמן יעד: 5–10 שניות** לשאלת סדרה חשבונית פשוטה.
""",
        ),
        (
            LessonSection.COMMON_MISTAKES,
            """
- **בדיקת הפרש אחד בלבד ועצירה** — תלמידים רבים בודקים רק את ההפרש בין
  האיבר הראשון לשני, ומניחים שהוא נכון לכל הסדרה בלי לוודא עם זוג נוסף.
  זה מסוכן כי לפעמים שני האיברים הראשונים "מתחזים" לחוק שלא ממשיך הלאה.

- **התעלמות מסדרות מתחלפות** — אם ההפרשים לא עקביים, תלמידים מוותרים
  ומנחשים, במקום לבדוק אם יש שני חוקים נפרדים למקומות זוגיים ואי-זוגיים.

- **טעויות סימן** — כשההפרש שלילי (הסדרה יורדת), קל לטעות ולחבר במקום לחסר.

- **בדיקה כפולה שלא נחוצה** — מצד שני, בזבוז זמן על אימות שלוש וארבע פעמים
  כשהתשובה כבר ברורה מהאפשרויות פוגע בזמן שנשאר לשאלות אחרות.
""",
        ),
        (
            LessonSection.SUMMARY,
            """
**מה למדנו בשיעור הזה:**

- סדרת מספרים נשלטת על ידי חוק קבוע — לרוב הפרש קבוע (חשבונית) או יחס קבוע (הנדסית).
- שיטת העבודה: בדקו הפרש, ואם לא קבוע — בדקו יחס, ואם לא — בדקו הפרש של הפרשים.
- במבחן: חשבו הפרש ראשון, חפשו אותו באפשרויות, ורק אם צריך — המשיכו לוודא.
- זמן יעד לשאלה כזו: כ-5–10 שניות.

בשיעור הבא נתרגל יחד כמה סדרות מסוגים שונים, כולל סדרות מתחלפות ומורכבות יותר.
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

    # --- practice questions: 5 real number-series questions, matching the
    # patterns taught above (arithmetic, geometric, second-difference /
    # squares, shrinking differences, alternating). 3 are embedded directly
    # into the lesson as guided-practice blocks; 2 stay in the question pool
    # (linked via lesson_id) for future independent-practice / test reuse.

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

    q1 = Question(
        category_id=category.id,
        lesson_id=lesson.id,
        difficulty=QuestionDifficulty.EASY,
        status=ContentStatus.PUBLISHED,
        body=_rich("מהו האיבר הבא בסדרה: 2, 5, 8, 11, ?"),
        solution_text=_rich(
            "ההפרש בין כל שני איברים סמוכים הוא 3 (5−2=3, 8−5=3, 11−8=3) — "
            "סדרה חשבונית. מוסיפים 3 לאיבר האחרון: 11+3=14."
        ),
        recommended_time_seconds=8,
        answers=_answers(
            [
                ("14", True, "בדיוק — זיהית שההפרש הקבוע הוא 3 והפעלת אותו נכון על 11."),
                ("13", False, "קרוב, אבל בדקי/בדוק שוב את ההפרש — הוא 3 ולא 2 בין כל שני איברים."),
                ("15", False, "כאן ההפרש שהופעל היה 4 במקום 3. חשוב/י שוב על ההפרש בין 8 ל-11."),
                ("12", False, "זה ההפרש הראשון (2) שהופעל בטעות פעמיים על 11 במקום ההפרש האמיתי, 3."),
            ]
        ),
    )

    q2 = Question(
        category_id=category.id,
        lesson_id=lesson.id,
        difficulty=QuestionDifficulty.EASY,
        status=ContentStatus.PUBLISHED,
        body=_rich("מהו האיבר הבא בסדרה: 3, 6, 12, 24, ?"),
        solution_text=_rich(
            "ההפרשים בין האיברים אינם קבועים (3, 6, 12) — זו לא סדרה חשבונית. "
            "בודקים יחס: 6/3=2, 12/6=2, 24/12=2 — יחס קבוע, סדרה הנדסית. "
            "מכפילים את האיבר האחרון ב-2: 24×2=48."
        ),
        recommended_time_seconds=10,
        answers=_answers(
            [
                ("48", True, "מדויק — זיהית שזו סדרה הנדסית עם יחס 2, לא חשבונית."),
                ("36", False, "כך מתקבל אם מוסיפים 12 (ההפרש האחרון) במקום להכפיל ביחס הקבוע 2."),
                ("30", False, "בדקי/בדוק שוב — כאן בוצע חיבור של 6 בלבד, אבל ההפרשים בסדרה זו לא קבועים."),
                ("50", False, "קרוב לתשובה הנכונה אך לא מדויק — ודא/י את הכפל: 24×2, לא 24+26."),
            ]
        ),
    )

    q3 = Question(
        category_id=category.id,
        lesson_id=lesson.id,
        difficulty=QuestionDifficulty.MEDIUM,
        status=ContentStatus.PUBLISHED,
        body=_rich("מהו האיבר הבא בסדרה: 1, 4, 9, 16, ?"),
        solution_text=_rich(
            "ההפרשים בין האיברים הם 3, 5, 7 — לא קבועים, אבל *הם עצמם* עולים ב-2 בכל פעם "
            "(סדרת הפרשים). ההפרש הבא יהיה 7+2=9, ולכן האיבר הבא: 16+9=25. "
            "(שימו לב: זו גם סדרת הריבועים 1²,2²,3²,4²,5²)."
        ),
        recommended_time_seconds=15,
        answers=_answers(
            [
                ("25", True, "כל הכבוד — זיהית את סדרת ההפרשים העולים, וגם שזו סדרת ריבועים."),
                ("20", False, "כאן הופעל הפרש קבוע של 4 בטעות. בסדרה הזו ההפרשים עצמם גדלים."),
                ("22", False, "קרוב, אבל בדקי/בדוק את סדרת ההפרשים (3,5,7) — ההפרש הבא הוא 9, לא 6."),
                ("24", False, "זה מתקבל מתוספת 8 בלבד; ההפרש הנכון הבא בסדרת ההפרשים הוא 9."),
            ]
        ),
    )

    q4 = Question(
        category_id=category.id,
        lesson_id=lesson.id,
        difficulty=QuestionDifficulty.MEDIUM,
        status=ContentStatus.PUBLISHED,
        body=_rich("מהו האיבר הבא בסדרה: 100, 90, 81, 73, ?"),
        solution_text=_rich(
            "ההפרשים הם −10, −9, −8 — כל הפרש קטן (בערכו) ב-1 מקודמו. "
            "ההפרש הבא יהיה −7, ולכן האיבר הבא: 73−7=66."
        ),
        recommended_time_seconds=15,
        answers=_answers(
            [
                ("66", True, "מדויק — זיהית שההפרשים עצמם עולים בהדרגה (−10,−9,−8,−7)."),
                ("65", False, "קרוב, אבל בדקי/בדוק את ההפרש הבא בסדרת ההפרשים — הוא −7, לא −8."),
                ("64", False, "כאן הופעל הפרש קבוע של −9 על כל הסדרה, אבל ההפרשים כאן משתנים."),
                ("70", False, "בדקי/בדוק שוב — כאן הופחת רק 3, אבל דפוס ההפרשים דורש הפחתה של 7."),
            ]
        ),
    )

    q5 = Question(
        category_id=category.id,
        lesson_id=lesson.id,
        difficulty=QuestionDifficulty.EXAM,
        status=ContentStatus.PUBLISHED,
        body=_rich("מהו האיבר הבא בסדרה: 2, 10, 4, 8, 6, 6, ?"),
        solution_text=_rich(
            "ההפרשים בין איברים סמוכים אינם עקביים — סימן לסדרה מתחלפת. "
            "מפרידים לשני תת-רצפים: המקומות האי-זוגיים (1,3,5,7): 2, 4, 6, ? — עולה ב-2, "
            "כך שהאיבר הבא הוא 8. (המקומות הזוגיים 10, 8, 6 יורדים ב-2 בנפרד, ומאששים שזו סדרה מתחלפת)."
        ),
        recommended_time_seconds=20,
        answers=_answers(
            [
                ("8", True, "בדיוק — הפרדת נכון לשני תת-רצפים וזיהית שהאי-זוגי עולה ב-2."),
                ("4", False, "זה ההפרש שהופעל על תת-הרצף הלא נכון (הזוגי במקום האי-זוגי)."),
                ("10", False, "קרוב מבחינת הכיוון, אך זה ערך מתת-הרצף השני (הזוגי), לא הרצף שמבוקש."),
                ("2", False, "בדקי/בדוק שוב — כך מתקבל אם מתעלמים מהעלייה בתת-הרצף האי-זוגי."),
            ]
        ),
    )

    for question in (q1, q2, q3, q4, q5):
        db.session.add(question)
    db.session.commit()

    guided_practice_blocks = [
        (q1, "תרגלו את מה שלמדתם: זיהוי הפרש קבוע בסדרה חשבונית פשוטה."),
        (q3, "אתגר קצת יותר גדול: סדרת הפרשים שעצמה עולה בקצב קבוע."),
        (q5, "ברמת מבחן: סדרה מתחלפת עם שני תת-רצפים נפרדים."),
    ]
    for order, (question, note) in enumerate(guided_practice_blocks, start=7):
        db.session.add(
            LessonContent(
                lesson_id=lesson.id,
                section=LessonSection.GUIDED_PRACTICE,
                block_type=BlockType.EMBEDDED_QUESTION,
                order=order,
                content={"question_id": question.id},
                block_metadata={"note": note},
            )
        )

    # summary now comes after the guided-practice questions
    db.session.query(LessonContent).filter_by(
        lesson_id=lesson.id, section=LessonSection.SUMMARY
    ).update({"order": 10})

    strategy = SolutionStrategy(
        category_id=category.id,
        identification_tips=_rich(
            "מזהים שאלת סדרת מספרים כשנתונה רשימת 4-6 מספרים ומבוקש למצוא את "
            "האיבר הבא, האיבר החסר באמצע, או האיבר הקודם."
        ),
        normal_method=_rich(
            "חשבו הפרש בין כל זוג איברים סמוכים; אם קבוע זו סדרה חשבונית, "
            "אחרת בדקו יחס (סדרה הנדסית), ואם גם זה לא קבוע בדקו הפרש של הפרשים."
        ),
        fast_method=_rich(
            "חשבו רק את ההפרש הראשון, הפעילו אותו על האיבר האחרון, וחפשו את "
            "התוצאה באפשרויות התשובה. אמתו עם הפרש נוסף רק אם יש שתי אפשרויות קרובות."
        ),
        shortcut_text=_rich("הפרש ראשון → הפעלה על האיבר האחרון → השוואה לאפשרויות."),
        target_time_seconds=8,
    )
    db.session.add(strategy)
    db.session.commit()

    return {
        "admin_email": ADMIN_EMAIL,
        "category_id": category.id,
        "lesson_id": lesson.id,
        "solution_strategy_id": strategy.id,
        "question_ids": [q.id for q in (q1, q2, q3, q4, q5)],
        "already_seeded": False,
    }


if __name__ == "__main__":
    app = create_app(os.getenv("FLASK_ENV", "development"))
    with app.app_context():
        summary = seed_demo_data()
        print("Seed complete:", summary)

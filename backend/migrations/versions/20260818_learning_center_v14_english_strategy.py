"""Expand learning center: English and exam strategy curriculum.

Revision ID: 20260818_lc_v14
Revises: 20260818_learning_center_v13

Idempotent content migration: inserts only when the lesson slug does not already exist.
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy import text

revision = "20260818_lc_v14"
down_revision = "20260818_learning_center_v13"
branch_labels = None
depends_on = None


def _category_id(conn, name):
    row = conn.execute(text("SELECT id FROM categories WHERE name=:name LIMIT 1"), {"name": name}).first()
    return row[0] if row else None


def _add_lesson(conn, category_id, slug, title, description, difficulty, duration, order_no):
    if not category_id:
        return 0
    exists = conn.execute(text("SELECT 1 FROM lessons WHERE slug=:slug LIMIT 1"), {"slug": slug}).first()
    if exists:
        return 0
    conn.execute(text("""INSERT INTO lessons
        (category_id,title,slug,description,status,difficulty_level,estimated_duration,"order",created_at,updated_at)
        VALUES (:category_id,:title,:slug,:description,'PUBLISHED',:difficulty,:duration,:order,NOW(),NOW())"""), {
        "category_id": category_id, "title": title, "slug": slug,
        "description": description, "difficulty": difficulty,
        "duration": duration, "order": order_no,
    })
    return 1


def upgrade():
    conn = op.get_bind()
    categories = {
        "english": _category_id(conn, "אנגלית"),
        "strategy": _category_id(conn, "אסטרטגיית מבחן"),
    }
    lessons = [
        ("english", "english-vocabulary-context", "אוצר מילים בהקשר", "איך להבין מילה חדשה לפי המשפט, שורש, הקשר ומסיחים.", "BEGINNER", 20, 1),
        ("english", "english-sentence-completion", "השלמת משפטים באנגלית", "זיהוי קשרים לוגיים ובחירת המילה המתאימה ביותר.", "INTERMEDIATE", 25, 2),
        ("english", "english-reading-main-idea", "הבנת הנקרא: רעיון מרכזי", "איתור הטענה המרכזית בלי להילכד בפרטים משניים.", "INTERMEDIATE", 25, 3),
        ("english", "english-reading-inference", "הבנת הנקרא: הסקה", "הסקת מסקנות שנובעות מהטקסט בלבד.", "ADVANCED", 30, 4),
        ("english", "english-grammar-essentials", "דקדוק חיוני למבחן", "זמנים, מילות קישור, התאמה ומבנים נפוצים.", "INTERMEDIATE", 25, 5),
        ("english", "english-connectors", "מילות קישור והיגיון", "because, although, however, therefore ועוד — לפי משמעות ולא לפי שינון בלבד.", "INTERMEDIATE", 20, 6),
        ("english", "english-speed-reading", "קריאה מהירה ומדויקת", "סריקה חכמה של קטע, מילות מפתח והימנעות מקריאה חוזרת מיותרת.", "ADVANCED", 20, 7),
        ("english", "english-trap-answers", "מסיחים באנגלית", "איך לזהות תשובה שנשמעת טוב אך אינה נתמכת במשפט או בקטע.", "ADVANCED", 20, 8),
        ("strategy", "strategy-time-management", "ניהול זמן במבחן", "חלוקת זמן, נקודות עצירה והחלטה מתי לדלג.", "BEGINNER", 20, 1),
        ("strategy", "strategy-elimination", "שיטת האלימינציה", "צמצום אפשרויות בצורה שיטתית גם כשלא יודעים מיד את התשובה.", "BEGINNER", 20, 2),
        ("strategy", "strategy-question-classification", "זיהוי סוג השאלה", "זיהוי מהיר של סוג המשימה לפני התחלת הפתרון.", "INTERMEDIATE", 20, 3),
        ("strategy", "strategy-fast-vs-deep", "מתי לפתור מהר ומתי לעומק", "בחירת עומק הפתרון לפי קושי, זמן וערך השאלה.", "INTERMEDIATE", 20, 4),
        ("strategy", "strategy-avoid-rushing", "דיוק תחת לחץ", "איך להימנע מטעויות קריאה וחישוב כשנותרו מעט שניות.", "INTERMEDIATE", 20, 5),
        ("strategy", "strategy-guessing", "קבלת החלטה כשלא בטוחים", "שימוש במידע הקיים, אלימינציה ובחירה מושכלת במקום תקיעות.", "ADVANCED", 20, 6),
        ("strategy", "strategy-review-without-backtracking", "בדיקה בלי לבזבז זמן", "מתי לבדוק תשובה ומתי להתקדם, בהתאם למגבלות הסימולציה.", "ADVANCED", 20, 7),
        ("strategy", "strategy-full-section-drills", "תרגול פרק מלא", "סימולציית פרק עם שעון, מעבר אוטומטי וניתוח טעויות.", "ADVANCED", 35, 8),
        ("strategy", "strategy-error-log", "יומן טעויות חכם", "מיון טעויות לפי ידע, הבנה, זמן, חישוב או בחירת אסטרטגיה.", "ADVANCED", 25, 9),
    ]
    for key, slug, title, desc, difficulty, duration, order_no in lessons:
        _add_lesson(conn, categories[key], slug, title, desc, difficulty, duration, order_no)


def downgrade():
    conn = op.get_bind()
    slugs = [
        "english-vocabulary-context", "english-sentence-completion", "english-reading-main-idea",
        "english-reading-inference", "english-grammar-essentials", "english-connectors",
        "english-speed-reading", "english-trap-answers", "strategy-time-management",
        "strategy-elimination", "strategy-question-classification", "strategy-fast-vs-deep",
        "strategy-avoid-rushing", "strategy-guessing", "strategy-review-without-backtracking",
        "strategy-full-section-drills", "strategy-error-log",
    ]
    conn.execute(text("DELETE FROM lessons WHERE slug = ANY(:slugs)"), {"slugs": slugs})

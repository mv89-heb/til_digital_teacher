"""Add an advanced second layer to the Learning Center.

Revision ID: 20260818_learning_center_v12
Revises: 20260818_learning_center_v11
"""
import json
from alembic import op
import sqlalchemy as sa

revision = "20260818_learning_center_v12"
down_revision = "20260818_learning_center_v11"
branch_labels = None
depends_on = None

LESSONS = {
    "quantitative": [
        ("אחוזים – סדרת שינויים", "לחשב שינויים עוקבים ולמצוא את הגורם המצטבר"),
        ("יחסים – חלוקה מורכבת", "לפרק יחס למנות ולבנות משוואה קצרה"),
        ("ממוצע משוקלל", "לחשב ממוצע כאשר לקבוצות יש משקל שונה"),
        ("סדרות – הפרשים משתנים", "לזהות חוק מתוך סדרת הפרשים"),
        ("סדרות – שני תתי־רצפים", "להפריד איברים במקומות זוגיים ואי־זוגיים"),
        ("מהירות ממוצעת", "להבדיל בין ממוצע מהירויות לבין מהירות ממוצעת במסלול"),
        ("הספק משולב", "לשלב שני קצבי עבודה ולמצוא זמן משותף"),
        ("בעיות כמותיות – קיצור דרך", "לבחור חישוב מינימלי תחת מגבלת זמן"),
    ],
    "verbal": [
        ("אנלוגיות – קשר מופשט", "להבחין בין קשרים קרובים ולבחור את המקביל המדויק"),
        ("אנלוגיות – כיוון הקשר", "לבדוק שהיחס פועל באותו כיוון בשני הזוגות"),
        ("השלמת משפטים – שלילה", "לזהות מבנים של שלילה והסתייגות"),
        ("השלמת משפטים – רצף רעיוני", "לעקוב אחרי הקשר בין כמה חלקי משפט"),
        ("הבנת הנקרא – הסקה עקיפה", "להסיק רק מה שניתן לבסס מהטקסט"),
        ("הבנת הנקרא – משמעות בהקשר", "לקבוע משמעות של מילה לפי הקטע"),
        ("הבנת הנקרא – רעיון מרכזי", "לזקק את הרעיון המרכזי מפרטים מסיחים"),
        ("מילולי – אסטרטגיית זמן", "לשלב סריקה, אלימינציה ובדיקת תשובה"),
    ],
    "figural": [
        ("סיבובים – שינוי נקודת מבט", "לחשב סיבוב כאשר נקודת הייחוס משתנה"),
        ("סיבובים – רצף ארוך", "לצמצם רצף סיבובים באמצעות מחזוריות"),
        ("מטריצות – חוק שורה ועמודה", "לבדוק חוק אופקי ואנכי לפני בחירת תא חסר"),
        ("מטריצות – שני משתנים", "לעקוב במקביל אחרי כיוון ומספר רכיבים"),
        ("קוביות – שלוש פאות נראות", "להסיק מיקום של פאות לפי שכנות"),
        ("קוביות – מסלול סיבוב", "לעקוב אחרי פאה נבחרת לאורך כמה סיבובים"),
        ("דפוסים – שינוי מצטבר", "לזהות שינוי שנוסף בכל שלב"),
        ("צורני – אלימינציה חזותית", "לפסול מסיחים לפי כלל יחיד לפני חישוב מלא"),
    ],
    "logic": [
        ("תנאים – הכרחי ומספיק", "להבדיל בין תנאי הכרחי לתנאי מספיק"),
        ("תנאים – שרשרת מסקנות", "לבצע כמה הסקות ברצף בלי להפוך כיוון"),
        ("סדר ישיבה – אילוצים מרובים", "לשלב כמה מגבלות מיקום"),
        ("התאמות – טבלת אפשרויות", "לבנות טבלת פסילות בצורה שיטתית"),
        ("לוגיקה – סתירה", "לזהות הנחה שמובילה לסתירה"),
        ("לוגיקה – אפשרות לעומת ודאות", "להבחין בין מה שחייב להיות נכון למה שיכול להיות נכון"),
        ("לוגיקה – אלימינציה מתקדמת", "לצמצם אפשרויות לפי הרמז החזק ביותר"),
        ("לוגיקה – סימולציית מבחן", "לפתור בעיות מורכבות בקצב של מבחן אמיתי"),
    ],
}

CATEGORIES = {
    "quantitative": ("חשיבה כמותית", "quantitative", 1),
    "verbal": ("חשיבה מילולית", "verbal", 2),
    "figural": ("חשיבה מרחבית וצורנית", "figural", 3),
    "logic": ("חשיבה לוגית", "logic", 4),
}

SECTIONS = [
    ("simple_explanation", "הסבר פשוט"),
    ("normal_explanation", "הסבר מלא"),
    ("solved_example", "דוגמה פתורה"),
    ("normal_method", "שיטת פתרון"),
    ("fast_method", "שיטה מהירה"),
    ("common_mistakes", "טעויות נפוצות"),
    ("guided_practice", "תרגול מודרך"),
    ("summary", "סיכום"),
]


def _category(conn, key):
    name, typ, order = CATEGORIES[key]
    return conn.execute(sa.text("""
        SELECT id FROM categories
        WHERE name=:name AND type=:typ AND parent_id IS NULL
        LIMIT 1
    """), {"name": name, "typ": typ}).scalar()


def _block(conn, lesson_id, section, order, body, metadata):
    conn.execute(sa.text("""
        INSERT INTO lesson_contents
            (lesson_id, section, block_type, "order", content,
             block_metadata, created_at, updated_at)
        VALUES
            (:lesson_id, :section, 'text', :order,
             CAST(:content AS JSON), CAST(:metadata AS JSON), NOW(), NOW())
    """), {
        "lesson_id": lesson_id,
        "section": section,
        "order": order,
        "content": json.dumps({"format": "markdown", "body": body}, ensure_ascii=False),
        "metadata": json.dumps(metadata, ensure_ascii=False),
    })


def upgrade():
    conn = op.get_bind()
    created = 0
    blocks = 0

    for key, items in LESSONS.items():
        category_id = _category(conn, key)
        if not category_id:
            continue

        for index, (title, goal) in enumerate(items, start=1):
            slug = f"learning-v12-{key}-{index:02d}"
            exists = conn.execute(
                sa.text("SELECT id FROM lessons WHERE slug=:slug LIMIT 1"),
                {"slug": slug},
            ).scalar()
            if exists:
                continue

            lesson_id = conn.execute(sa.text("""
                INSERT INTO lessons
                    (category_id, title, slug, description, status,
                     difficulty_level, estimated_duration, icon, "order",
                     created_at, updated_at)
                VALUES
                    (:category_id, :title, :slug, :description, 'published',
                     'advanced', 18, 'brain', :order, NOW(), NOW())
                RETURNING id
            """), {
                "category_id": category_id,
                "title": title,
                "slug": slug,
                "description": goal,
                "order": 100 + index,
            }).scalar_one()
            created += 1

            bodies = [
                f"# {title}\n\n{goal}. בשלב הזה עוברים מתרגול בסיסי לפתרון מדויק ומהיר.",
                f"העיקרון המרכזי: {goal}. עובדים לפי כלל אחד בכל פעם ומוודאים שהכלל מסביר את כל הנתונים.",
                "דוגמה פתורה: מתחילים מהנתונים החשובים, מסמנים את הקשר המרכזי, פותרים בצעד הקצר ביותר ורק אז בודקים את האפשרויות.",
                "שיטת פתרון: 1. קראו את השאלה. 2. הגדירו את החוק. 3. פסלו אפשרויות שאינן עומדות בחוק. 4. בדקו את התשובה מול הנתונים.",
                "שיטה מהירה: חפשו קודם את הסימן המבדיל בין המסיחים. אם כלל אחד פוסל שלוש אפשרויות, אין צורך לפתור את כולן עד הסוף.",
                "טעויות נפוצות: בחירת תשובה שנראית נכונה אך אינה מסבירה את כל הנתונים, התעלמות מכיוון הקשר, וחישוב ארוך כשקיימת דרך קצרה.",
                "תרגול מודרך: פתרו שאלה אחת לאט, הסבירו לעצמכם מה החוק, ואז פתרו שאלה דומה שוב עם יעד זמן קצר יותר.",
                "סיכום: המטרה היא לא רק להגיע לתשובה אלא לזהות את החוק במהירות, לפסול מסיחים ולשמור על דיוק תחת זמן.",
            ]
            for order, ((section, section_title), body) in enumerate(zip(SECTIONS, bodies), start=1):
                _block(conn, lesson_id, section, order, f"## {section_title}\n\n{body}", {
                    "curriculum_version": "v12",
                    "domain": key,
                    "lesson_goal": goal,
                })
                blocks += 1

    print({"migration": "learning_center_v12", "lessons_created": created, "blocks_created": blocks})


def downgrade():
    conn = op.get_bind()
    ids = conn.execute(sa.text("""
        SELECT id FROM lessons WHERE slug LIKE 'learning-v12-%'
    """)).scalars().all()
    for lesson_id in ids:
        conn.execute(sa.text("DELETE FROM lesson_contents WHERE lesson_id=:lesson_id"), {"lesson_id": lesson_id})
        conn.execute(sa.text("DELETE FROM lessons WHERE id=:lesson_id"), {"lesson_id": lesson_id})

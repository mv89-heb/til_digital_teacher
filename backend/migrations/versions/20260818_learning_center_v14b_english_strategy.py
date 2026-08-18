"""Expand learning center: English and exam strategy curriculum."""
from alembic import op
from sqlalchemy import text

revision = "20260818_lc_v14b"
down_revision = "20260818_lc_v14"
branch_labels = None
depends_on = None


def _category_id(conn, names):
    for name in names:
        row = conn.execute(text("SELECT id FROM categories WHERE name=:name LIMIT 1"), {"name": name}).first()
        if row:
            return row[0]
    return None


def _add(conn, cid, slug, title, desc, difficulty, duration, order_no):
    if not cid or conn.execute(text("SELECT 1 FROM lessons WHERE slug=:slug LIMIT 1"), {"slug": slug}).first():
        return
    conn.execute(text("""INSERT INTO lessons
        (category_id,title,slug,description,status,difficulty_level,estimated_duration,"order",created_at,updated_at)
        VALUES (:cid,:title,:slug,:desc,'PUBLISHED',:difficulty,:duration,:ord,NOW(),NOW())"""),
        {"cid":cid,"title":title,"slug":slug,"desc":desc,"difficulty":difficulty,"duration":duration,"ord":order_no})


def upgrade():
    conn = op.get_bind()
    eng = _category_id(conn, ["אנגלית", "English"])
    strat = _category_id(conn, ["אסטרטגיית מבחן", "אסטרטגיה", "Test Strategy"])
    rows = [
        (eng,"english-vocabulary-context","אוצר מילים בהקשר","הבנת מילים לפי הקשר ומסיחים.","BEGINNER",20,1),
        (eng,"english-sentence-completion","השלמת משפטים באנגלית","קשרים לוגיים ובחירת המילה המתאימה.","INTERMEDIATE",25,2),
        (eng,"english-reading-main-idea","הבנת הנקרא: רעיון מרכזי","איתור הטענה המרכזית.","INTERMEDIATE",25,3),
        (eng,"english-reading-inference","הבנת הנקרא: הסקה","מסקנות שנובעות מהטקסט בלבד.","ADVANCED",30,4),
        (eng,"english-grammar-essentials","דקדוק חיוני למבחן","זמנים, התאמה ומבנים נפוצים.","INTERMEDIATE",25,5),
        (eng,"english-connectors","מילות קישור והיגיון","מילות קישור לפי משמעות.","INTERMEDIATE",20,6),
        (eng,"english-speed-reading","קריאה מהירה ומדויקת","סריקה חכמה ומילות מפתח.","ADVANCED",20,7),
        (eng,"english-trap-answers","מסיחים באנגלית","זיהוי תשובה שאינה נתמכת בטקסט.","ADVANCED",20,8),
        (strat,"strategy-time-management","ניהול זמן במבחן","חלוקת זמן והחלטה מתי לדלג.","BEGINNER",20,1),
        (strat,"strategy-elimination","שיטת האלימינציה","צמצום אפשרויות בצורה שיטתית.","BEGINNER",20,2),
        (strat,"strategy-question-classification","זיהוי סוג השאלה","זיהוי מהיר של סוג המשימה.","INTERMEDIATE",20,3),
        (strat,"strategy-fast-vs-deep","מתי לפתור מהר ומתי לעומק","בחירת עומק הפתרון לפי קושי וזמן.","INTERMEDIATE",20,4),
        (strat,"strategy-avoid-rushing","דיוק תחת לחץ","מניעת טעויות קריאה וחישוב.","INTERMEDIATE",20,5),
        (strat,"strategy-guessing","קבלת החלטה כשלא בטוחים","אלימינציה ובחירה מושכלת.","ADVANCED",20,6),
        (strat,"strategy-review-without-backtracking","בדיקה בלי לבזבז זמן","מתי לבדוק ומתי להתקדם.","ADVANCED",20,7),
        (strat,"strategy-full-section-drills","תרגול פרק מלא","סימולציית פרק עם שעון וניתוח טעויות.","ADVANCED",35,8),
        (strat,"strategy-error-log","יומן טעויות חכם","מיון טעויות לפי מקור הטעות.","ADVANCED",25,9),
    ]
    for row in rows:
        _add(conn, *row)


def downgrade():
    conn = op.get_bind()
    for slug in ["english-vocabulary-context","english-sentence-completion","english-reading-main-idea","english-reading-inference","english-grammar-essentials","english-connectors","english-speed-reading","english-trap-answers","strategy-time-management","strategy-elimination","strategy-question-classification","strategy-fast-vs-deep","strategy-avoid-rushing","strategy-guessing","strategy-review-without-backtracking","strategy-full-section-drills","strategy-error-log"]:
        conn.execute(text("DELETE FROM lessons WHERE slug=:slug"), {"slug":slug})

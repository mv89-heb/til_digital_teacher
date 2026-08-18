"""Expand the calibrated TIL question bank with additional original items.

Revision ID: 20260818_question_bank_v2
Revises: 20260818_question_bank_v1
"""

import json

from alembic import op
import sqlalchemy as sa

revision = "20260818_question_bank_v2"
down_revision = "20260818_question_bank_v1"
branch_labels = None
depends_on = None


def _cat(conn, name, typ, parent_name):
    parent = conn.execute(sa.text("SELECT id FROM categories WHERE name=:n AND type=:t AND parent_id IS NULL LIMIT 1"), {"n": parent_name, "t": typ}).scalar()
    return conn.execute(sa.text("SELECT id FROM categories WHERE name=:n AND type=:t AND parent_id=:p LIMIT 1"), {"n": name, "t": typ, "p": parent}).scalar()


def _add(conn, category_id, p):
    if conn.execute(sa.text("SELECT 1 FROM questions WHERE question_metadata ->> 'bank_key'=:k LIMIT 1"), {"k": p["key"]}).first():
        return
    meta = {
        "bank_key": p["key"],
        "main_category": p["main"],
        "subcategory": p["sub"],
        "skill": p["skill"],
        "difficulty_level": p["level"],
        "tags": p.get("tags", []),
        "visual": p.get("visual"),
        "psychometrics": {"a": None, "b": None, "c": None},
        "quality": {"review_status": "APPROVED", "single_correct_answer": True, "source": "original_til_bank_v2"},
    }
    qid = conn.execute(sa.text("""
        INSERT INTO questions (category_id, question_type, difficulty, status, body, solution_text,
        recommended_time_seconds, question_metadata, created_at, updated_at)
        VALUES (:cid,'multiple_choice','exam','published',CAST(:body AS JSON),CAST(:solution AS JSON),:secs,CAST(:meta AS JSON),NOW(),NOW()) RETURNING id
    """), {
        "cid": category_id,
        "body": json.dumps({"format":"markdown","body":p["body"]}, ensure_ascii=False),
        "solution": json.dumps({"format":"markdown","body":p["solution"]}, ensure_ascii=False),
        "secs": p["secs"], "meta": json.dumps(meta, ensure_ascii=False),
    }).scalar_one()
    snap = []
    for i, (text, correct, explanation) in enumerate(p["answers"], 1):
        aid = conn.execute(sa.text("""
            INSERT INTO answers (question_id, answer_text, is_correct, explanation_if_selected, "order", created_at, updated_at)
            VALUES (:qid,:text,:correct,CAST(:exp AS JSON),:ord,NOW(),NOW()) RETURNING id
        """), {"qid":qid,"text":text,"correct":correct,"exp":json.dumps({"format":"markdown","body":explanation}, ensure_ascii=False),"ord":i}).scalar_one()
        snap.append({"id":aid,"answer_text":text,"is_correct":correct,"explanation_if_selected":{"format":"markdown","body":explanation},"order":i})
    conn.execute(sa.text("""
        INSERT INTO question_versions (question_id,version_number,category_id,question_type,difficulty,status,body,solution_text,question_metadata,answer_snapshot,recommended_time_seconds,created_at)
        SELECT :qid,1,category_id,question_type,difficulty,status,body,solution_text,question_metadata,CAST(:snap AS JSONB),recommended_time_seconds,NOW()
        FROM questions WHERE id=:qid
    """), {"qid":qid,"snap":json.dumps(snap, ensure_ascii=False)})


def upgrade():
    conn = op.get_bind()
    cats = {
        "q_percent": _cat(conn,"אחוזים ושינויים","quantitative","חשיבה כמותית"),
        "q_rate": _cat(conn,"יחס והספק","quantitative","חשיבה כמותית"),
        "q_seq": _cat(conn,"סדרות מספרים","quantitative","חשיבה כמותית"),
        "v_ana": _cat(conn,"אנלוגיות","verbal","חשיבה מילולית"),
        "v_sent": _cat(conn,"השלמת משפטים","verbal","חשיבה מילולית"),
        "v_read": _cat(conn,"הבנת הנקרא","verbal","חשיבה מילולית"),
        "f_rot": _cat(conn,"סיבוב צורות","figural","חשיבה מרחבית וצורנית"),
        "f_mat": _cat(conn,"מטריצות צורניות","figural","חשיבה מרחבית וצורנית"),
        "f_cube": _cat(conn,"קוביות ומרחב","figural","חשיבה מרחבית וצורנית"),
    }
    A=lambda *x: (x[0],x[1],x[2],x[3])
    qs = [
      ("q_percent",{"key":"QB-Q-004","main":"quantitative","sub":"percentages","skill":"successive_change","level":2,"secs":40,"body":"מחיר של 250 ש״ח הוזל ב־20%. מה המחיר החדש?","solution":"20% מ־250 הם 50, ולכן 250−50=200.","answers":[("180",False,"חישוב שגוי של 28% הנחה."),("200",True,"250×0.8=200."),("210",False,"ההנחה היא 50 ש״ח."),("225",False,"זה משקף 10% הנחה.")]}),
      ("q_percent",{"key":"QB-Q-005","main":"quantitative","sub":"percentages","skill":"reverse_percent","level":5,"secs":60,"body":"לאחר הנחה של 15% מחירו של מוצר הוא 340 ש״ח. מה היה מחירו המקורי?","solution":"340 הם 85% מהמחיר המקורי. לכן 340/0.85=400.","answers":[("370",False,"340/0.92 אינו היחס המתאים."),("390",False,"המחיר המקורי חייב להיות גדול יותר."),("400",True,"400×0.85=340."),("415",False,"אינו נותן 340 לאחר 15% הנחה.")]}),
      ("q_rate",{"key":"QB-Q-006","main":"quantitative","sub":"rates","skill":"average_speed","level":3,"secs":55,"body":"רוכב נסע 30 ק״מ במהירות 60 קמ״ש ועוד 30 ק״מ במהירות 30 קמ״ש. מה הייתה מהירותו הממוצעת לכל הדרך?","solution":"הזמן הוא 0.5+1=1.5 שעות. המרחק 60 ק״מ, ולכן הממוצע 60/1.5=40 קמ״ש.","answers":[("30",False,"זה רק המהירות בקטע השני."),("40",True,"ממוצע מהירות מחושב לפי מרחק כולל חלקי זמן כולל."),("45",False,"זהו ממוצע חשבוני של המהירויות, שאינו מתאים כאן."),("50",False,"אינו תואם לזמן הכולל.")]}),
      ("q_rate",{"key":"QB-Q-007","main":"quantitative","sub":"rates","skill":"proportions","level":1,"secs":35,"body":"אם 4 מחברות עולות 28 ש״ח, כמה יעלו 7 מחברות באותו מחיר ליחידה?","solution":"מחברת עולה 7 ש״ח. שבע מחברות עולות 49 ש״ח.","answers":[("42",False,"זה מחיר של 6 מחברות."),("49",True,"28/4=7 ואז 7×7=49."),("52",False,"אין שינוי במחיר ליחידה."),("56",False,"זה מחיר של 8 מחברות.")]}),
      ("q_seq",{"key":"QB-Q-008","main":"quantitative","sub":"sequences","skill":"alternating_pattern","level":5,"secs":55,"body":"מהו המספר הבא: 3, 6, 12, 24, 48, ?","solution":"כל איבר מוכפל פי 2. לכן 48×2=96.","answers":[("72",False,"זהו חיבור 24 בלבד."),("84",False,"אין כלל כזה בסדרה."),("96",True,"הכלל הוא כפל ב־2."),("108",False,"אינו תואם לדפוס.")]}),
      ("q_seq",{"key":"QB-Q-009","main":"quantitative","sub":"sequences","skill":"mixed_pattern","level":2,"secs":40,"body":"מהו המספר הבא: 5, 8, 12, 17, 23, ?","solution":"ההפרשים הם 3,4,5,6, ולכן הבא הוא 7. התשובה 30.","answers":[("29",False,"הפרש 6 ממשיך את האיבר הקודם בלבד."),("30",True,"23+7=30."),("31",False,"נדרש הפרש 8, לא 7."),("32",False,"אינו מתאים לדפוס ההפרשים.")]}),
      ("v_ana",{"key":"QB-V-003","main":"verbal","sub":"analogies","skill":"part_whole","level":1,"secs":30,"body":"פרק : ספר — מהו הזוג הדומה ביותר?","solution":"פרק הוא חלק מספר, כפי שגלגל הוא חלק ממכונית.","answers":[("גלגל : מכונית",True,"זהו יחס חלק־שלם."),("מורה : כיתה",False,"זהו אדם ומקום/קבוצה."),("עץ : יער",False,"זהו פרט וקבוצה, אך בכיוון יחסי שונה מהניסוח כאן."),("מפתח : דלת",False,"זהו כלי ומושא שימוש.")]}),
      ("v_ana",{"key":"QB-V-004","main":"verbal","sub":"analogies","skill":"cause_effect","level":4,"secs":45,"body":"גשם : מטרייה — מהו הזוג בעל היחס הדומה ביותר?","solution":"מטרייה היא אמצעי התמודדות עם גשם; מסנן הוא אמצעי להתמודדות עם חלקיקים לא רצויים.","answers":[("שמש : משקפי שמש",True,"משקפי שמש משמשים כהגנה מפני השמש."),("מים : כוס",False,"כלי קיבול."),("שלג : הר",False,"תופעה ומקום."),("רוח : ענן",False,"אין אותו יחס תפקודי.")]}),
      ("v_sent",{"key":"QB-V-005","main":"verbal","sub":"sentence_completion","skill":"logical_connectors","level":2,"secs":40,"body":"הספר היה קצר מאוד, ______ הוא הצליח להציג את הנושא בצורה ______ ומעמיקה.","solution":"למרות הקיצור, ההצגה הייתה בהירה ומעמיקה.","answers":[("לכן / שטחית",False,"המשמעות סותרת את המשפט."),("אך / בהירה",True,"ניגוד בין אורך הספר לאיכות ההצגה."),("משום כך / חלקית",False,"אין קשר סיבתי כזה."),("אף כי / מבולבלת",False,"לא מתאים להמשך.")]}),
      ("v_sent",{"key":"QB-V-006","main":"verbal","sub":"sentence_completion","skill":"precision","level":5,"secs":55,"body":"הוועדה לא דחתה את ההצעה על הסף; ______ היא ביקשה מן המציע ______ אותה בכמה נקודות מהותיות.","solution":"הוועדה לא דחתה, אלא ביקשה לשנות/לתקן. לכן 'במקום זאת' ו'לתקן' מתאימים.","answers":[("במקום זאת / לתקן",True,"זהו הקשר הלוגי המדויק."),("למרות זאת / לאשר",False,"אישור אינו משתמע."),("משום כך / להסתיר",False,"הקשר אינו סיבתי כזה."),("אף על פי כן / לבטל",False,"סותר את המשפט הראשון.")]}),
      ("v_read",{"key":"QB-V-007","main":"verbal","sub":"reading","skill":"main_idea","level":3,"secs":55,"body":"טקסט: 'חוקרים מצאו כי הפסקות קצרות במהלך משימה ממושכת אינן בהכרח מפחיתות תפוקה. כאשר ההפסקה מתוזמנת היטב, היא עשויה לשפר ריכוז ולהפחית טעויות.' מהי הטענה המרכזית?","solution":"הטענה היא שהפסקות קצרות ומתוזמנות עשויות לשפר ביצוע במשימה ממושכת.","answers":[("כל הפסקה מפחיתה תפוקה",False,"הטקסט אומר להפך לגבי הפסקות מתוזמנות."),("הפסקות מתוזמנות עשויות לשפר ביצוע",True,"זו מסקנת הטקסט."),("ריכוז אינו קשור לטעויות",False,"הטקסט מקשר ביניהם."),("משימות ממושכות תמיד גורמות לטעויות",False,"זו טענה גורפת שלא נאמרה.")]}),
      ("v_read",{"key":"QB-V-008","main":"verbal","sub":"reading","skill":"inference","level":4,"secs":60,"body":"טקסט: 'העיר הרחיבה את שבילי האופניים. בשנה הראשונה נרשמה עלייה במספר הרוכבים, אך במקביל נמדדה ירידה קלה בנסיעות קצרות ברכב.' איזו מסקנה נתמכת ביותר?","solution":"הנתונים תומכים בכך שהרחבת השבילים לוותה ביותר רכיבה ובפחות נסיעות קצרות ברכב.","answers":[("כל הנהגים עברו לאופניים",False,"אין בסיס לטענה גורפת."),("הרחבת השבילים לוותה בשינוי בדפוסי הנסיעה",True,"זו מסקנה זהירה מהנתונים."),("העיר ביטלה את התחבורה הציבורית",False,"לא נאמר."),("רכיבה תמיד מהירה יותר מנהיגה",False,"לא נבדק בטקסט.")]}),
      ("f_rot",{"key":"QB-F-001","main":"figural","sub":"rotation","skill":"rotation_90","level":1,"secs":35,"body":"צורה: חץ המצביע למעלה. אם מסובבים אותה ב־90° עם כיוון השעון, לאיזה כיוון יצביע החץ?","solution":"סיבוב עם כיוון השעון של 90° מעביר למעלה לימין.","visual":{"format":"svg","svg":"<svg viewBox='0 0 120 80'><path d='M60 10 L80 35 L68 35 L68 70 L52 70 L52 35 L40 35 Z' fill='none' stroke='currentColor' stroke-width='4'/></svg>'},"answers":[("למעלה",False,"זהו הכיוון לפני הסיבוב."),("ימינה",True,"סיבוב 90° עם כיוון השעון מעביר למעלה לימין."),("למטה",False,"זהו סיבוב של 180°."),("שמאלה",False,"זהו סיבוב של 90° נגד כיוון השעון.")] }),
      ("f_rot",{"key":"QB-F-002","main":"figural","sub":"rotation","skill":"rotation_180","level":3,"secs":45,"body":"צורה מורכבת משני משולשים: אחד פונה למעלה ואחד פונה ימינה. לאחר סיבוב של 180°, לאיזה כיוונים יפנו המשולשים?","solution":"בסיבוב 180° כל כיוון מתהפך: למעלה הופך למטה וימינה הופך לשמאלה.","visual":{"format":"instruction","render":"two_triangles_up_right_rotate_180"},"answers":[("למעלה ולימין",False,"זהו המצב המקורי."),("למטה ולשמאל",True,"שני הכיוונים מתהפכים ב־180°."),("למטה ולימין",False,"רק אחד מהכיוונים התהפך."),("למעלה ולשמאל",False,"רק אחד מהכיוונים התהפך.")] }),
      ("f_mat",{"key":"QB-F-003","main":"figural","sub":"matrix","skill":"row_sequence","level":4,"secs":55,"body":"במטריצה 3×3, בכל שורה המספר בתוך העיגול גדל ב־2 משמאל לימין. השורה האחרונה היא 3, 5, ?. מה חסר?","solution":"הכלל הוא תוספת 2, לכן 5+2=7.","visual":{"format":"matrix","cells":[[1,3,5],[2,4,6],[3,5,null]],"rule":"+2 across each row"},"answers":[("6",False,"הפרש של 1 אינו הכלל."),("7",True,"5+2=7."),("8",False,"נדרשת תוספת 3."),("9",False,"נדרשת תוספת 4.")] }),
      ("f_mat",{"key":"QB-F-004","main":"figural","sub":"matrix","skill":"alternating_shape","level":5,"secs":65,"body":"במטריצה 3×3, כל שורה מכילה עיגול, משולש וריבוע בסדר מחזורי; כל שורה מתחילה בצורה הבאה בסבב. איזו צורה צריכה להופיע בתא האחרון?","solution":"השורה הראשונה מתחילה בעיגול, השנייה במשולש והשלישית בריבוע. לכן השורה השלישית היא ריבוע, עיגול, משולש.","visual":{"format":"matrix","cells":[["circle","triangle","square"],["triangle","square","circle"],["square","circle",null]],"rule":"cyclic shift"},"answers":[("עיגול",False,"זהו התא האמצעי בשורה השלישית."),("משולש",True,"זהו המשך הסבב המחזורי."),("ריבוע",False,"זהו התא הראשון בשורה השלישית."),("כוכב",False,"צורה זו אינה חלק מהכלל.")] }),
      ("f_cube",{"key":"QB-F-005","main":"figural","sub":"cube","skill":"opposite_faces","level":2,"secs":45,"body":"בקובייה, פאה A נמצאת מול B. פאה C נמצאת מול D. אם A היא הפאה העליונה, איזו פאה אינה יכולה להיות צמודה ל-A?","solution":"פאה שמול A אינה יכולה להיות צמודה אליה. לכן B אינה יכולה להיות צמודה ל-A.","visual":{"format":"cube","faces":{"A":"top","B":"bottom","C":"front","D":"back","E":"left","F":"right"}},"answers":[("B",True,"פאות נגדיות אינן צמודות."),("C",False,"C יכולה להיות קדמית ולכן צמודה ל-A."),("E",False,"E יכולה להיות שמאלית וצמודה ל-A."),("F",False,"F יכולה להיות ימנית וצמודה ל-A.")] }),
      ("f_cube",{"key":"QB-F-006","main":"figural","sub":"cube","skill":"net_folding","level":5,"secs":70,"body":"פריסת קובייה מורכבת מארבעה ריבועים בשורה, עם ריבוע אחד מעל השני משני צדי השורה. איזה זוג פאות חייב להיות נגדיות לאחר הקיפול?","solution":"בפריסה תקנית של ארבע פאות רצופות, הפאות הראשונה והשלישית בשורה מתקפלות לפאות נגדיות.","visual":{"format":"cube_net","layout":[["A","B","C","D"],[null,"E",null,null],[null,"F",null,null]]},"answers":[("A ו־B",False,"פאות סמוכות בפריסה."),("A ו־C",True,"הן מתקפלות לפאות נגדיות."),("B ו־E",False,"הן יכולות להיות סמוכות."),("C ו־D",False,"הן סמוכות בפריסה.")] }),
    ]
    for cat_key, p in qs:
        _add(conn, cats[cat_key], p)


def downgrade():
    conn = op.get_bind()
    keys = [f"QB-{prefix}-{i:03d}" for prefix, start, end in [("Q",4,9),("V",3,8),("F",1,6)]]
    for key in keys:
        qid = conn.execute(sa.text("SELECT id FROM questions WHERE question_metadata ->> 'bank_key'=:k"), {"k":key}).scalar()
        if qid:
            conn.execute(sa.text("DELETE FROM question_versions WHERE question_id=:id"), {"id":qid})
            conn.execute(sa.text("DELETE FROM answers WHERE question_id=:id"), {"id":qid})
            conn.execute(sa.text("DELETE FROM questions WHERE id=:id"), {"id":qid})

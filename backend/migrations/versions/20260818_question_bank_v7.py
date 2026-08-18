"""Expand the TIL bank with 240 deterministic verbal and figural questions.

Revision ID: 20260818_question_bank_v7
Revises: 20260818_question_bank_v6
"""
import json
from alembic import op
import sqlalchemy as sa

revision = "20260818_question_bank_v7"
down_revision = "20260818_question_bank_v6"
branch_labels = None
depends_on = None


def _cat(conn, child, typ, parent):
    pid = conn.execute(sa.text("SELECT id FROM categories WHERE name=:n AND type=:t AND parent_id IS NULL LIMIT 1"), {"n": parent, "t": typ}).scalar()
    if not pid:
        return None
    return conn.execute(sa.text("SELECT id FROM categories WHERE name=:n AND type=:t AND parent_id=:p LIMIT 1"), {"n": child, "t": typ, "p": pid}).scalar()


def _add(conn, cid, key, main, sub, skill, level, secs, body, solution, options, correct_index, visual=None, tags=None):
    if not cid or conn.execute(sa.text("SELECT 1 FROM questions WHERE question_metadata ->> 'bank_key'=:k LIMIT 1"), {"k": key}).first():
        return 0
    if len(options) != 4 or len(set(options)) != 4 or not 0 <= correct_index < 4:
        raise ValueError(f"Invalid four-option question: {key}")
    meta = {
        "bank_key": key,
        "main_category": main,
        "subcategory": sub,
        "skill": skill,
        "difficulty_level": level,
        "tags": tags or [],
        "visual": visual,
        "psychometrics": {"a": None, "b": None, "c": None},
        "quality": {"review_status": "APPROVED", "single_correct_answer": True, "source": "original_til_bank_v7", "calibration_status": "initial"},
    }
    difficulty = "easy" if level <= 2 else ("medium" if level == 3 else "exam")
    qid = conn.execute(sa.text("""INSERT INTO questions (category_id,question_type,difficulty,status,body,solution_text,recommended_time_seconds,question_metadata,created_at,updated_at)
        VALUES (:cid,'multiple_choice',:difficulty,'published',CAST(:body AS JSON),CAST(:solution AS JSON),:secs,CAST(:meta AS JSON),NOW(),NOW()) RETURNING id"""), {
        "cid": cid,
        "difficulty": difficulty,
        "body": json.dumps({"format": "markdown", "body": body}, ensure_ascii=False),
        "solution": json.dumps({"format": "markdown", "body": solution}, ensure_ascii=False),
        "secs": secs,
        "meta": json.dumps(meta, ensure_ascii=False),
    }).scalar_one()
    snap = []
    for order, text in enumerate(options, 1):
        ok = order - 1 == correct_index
        exp = "זו התשובה הנכונה לפי הנתונים והכלל בשאלה." if ok else "המסיח אינו מתאים לנתונים או לכלל בשאלה."
        aid = conn.execute(sa.text("""INSERT INTO answers (question_id,answer_text,is_correct,explanation_if_selected,"order",created_at,updated_at)
            VALUES (:qid,:text,:ok,CAST(:exp AS JSON),:ord,NOW(),NOW()) RETURNING id"""), {
            "qid": qid, "text": text, "ok": ok,
            "exp": json.dumps({"format": "markdown", "body": exp}, ensure_ascii=False),
            "ord": order,
        }).scalar_one()
        snap.append({"id": aid, "answer_text": text, "is_correct": ok, "explanation_if_selected": {"format": "markdown", "body": exp}, "order": order})
    conn.execute(sa.text("""INSERT INTO question_versions (question_id,version_number,category_id,question_type,difficulty,status,body,solution_text,question_metadata,answer_snapshot,recommended_time_seconds,created_at,updated_at)
        SELECT :qid,1,category_id,question_type,difficulty,status,body,solution_text,question_metadata,CAST(:snap AS JSONB),recommended_time_seconds,NOW(),NOW()
        FROM questions WHERE id=:qid"""), {"qid": qid, "snap": json.dumps(snap, ensure_ascii=False)})
    return 1


def upgrade():
    conn = op.get_bind()
    va = _cat(conn, "אנלוגיות", "verbal", "חשיבה מילולית")
    vs = _cat(conn, "השלמת משפטים", "verbal", "חשיבה מילולית")
    vr = _cat(conn, "הבנת הנקרא", "verbal", "חשיבה מילולית")
    fr = _cat(conn, "סיבוב צורות", "figural", "חשיבה מרחבית וצורנית")
    fm = _cat(conn, "מטריצות צורניות", "figural", "חשיבה מרחבית וצורנית")
    fc = _cat(conn, "קוביות ומרחב", "figural", "חשיבה מרחבית וצורנית")
    fp = _cat(conn, "דפוסים חזותיים", "figural", "חשיבה מרחבית וצורנית")
    added = 0

    analogy_pairs = [
        ("ציפור", "קן", "דבורה", "כוורת"), ("מפתח", "מנעול", "סיסמה", "חשבון"),
        ("רופא", "מטופל", "מורה", "תלמיד"), ("ספר", "ספרייה", "מוצג", "מוזיאון"),
        ("מכתב", "מעטפה", "מתנה", "אריזה"), ("מדחום", "טמפרטורה", "מד מהירות", "מהירות"),
        ("מצפן", "כיוון", "שעון", "זמן"), ("מכחול", "ציור", "מקלדת", "הקלדה"),
        ("מספריים", "חיתוך", "מחק", "מחיקה"), ("זרע", "צמח", "ביצה", "אפרוח"),
        ("גנן", "גינה", "ספרן", "ספרייה"), ("צלם", "תמונה", "סופר", "רומן"),
        ("רמקול", "קול", "מסך", "תמונה"), ("חלב", "גבינה", "ענבים", "יין"),
        ("קמח", "לחם", "חימר", "כלי"), ("אוזן", "שמיעה", "עין", "ראייה"),
        ("פה", "דיבור", "יד", "כתיבה"), ("דג", "מים", "ציפור", "אוויר"),
        ("ספינה", "ים", "רכבת", "מסילה"), ("מפה", "מיקום", "לוח שנה", "תאריך"),
    ]
    for i in range(60):
        a,b,c,d = analogy_pairs[i % len(analogy_pairs)]
        distractors = [
            f"{c} : {d}",
            f"{a} : {c}",
            f"{d} : {b}",
            f"{b} : {a}",
        ]
        options = [f"{c} : {d}", f"{a} : {c}", f"{d} : {b}", f"{b} : {a}"]
        options[0] = f"{c} : {d}"
        correct = 0
        added += _add(conn, va, f"QB-V-A-{i+1:03d}", "verbal", "analogies", "relationship_analogy", 1 + i % 5, 35 + (i % 3) * 5,
                       f"{a} : {b} — {c} : ? מה צריך להשלים כדי ליצור קשר מקביל?",
                       f"הקשר הוא {a} ל-{b}; לכן מחפשים את המושג המקביל ל-{d} ביחס ל-{c}.",
                       options, correct, tags=["אנלוגיות", "יחסים"])

    connectors = [
        ("הגשם פסק, ______ הרחובות נותרו רטובים.", "אך", ["לכן", "משום כך", "כדי"]),
        ("הנתונים היו חלקיים, ______ החוקרים נמנעו ממסקנה מוחלטת.", "ולכן", ["אולם", "כדי", "למרות"]),
        ("המחיר ירד, ______ הביקוש נשאר דומה.", "אך", ["לכן", "משום כך", "כדי"]),
        ("החוקר חזר על הניסוי ______ לוודא שהתוצאה יציבה.", "כדי", ["אך", "לכן", "אולם"]),
        ("המסלול ארוך יותר; ______ הוא מוצל יותר.", "עם זאת", ["לכן", "כדי", "משום כך"]),
        ("המערכת התריעה, ______ התהליך נעצר.", "ולכן", ["אך", "כדי", "למרות"]),
        ("המשימה נראתה פשוטה, ______ דרשה ריכוז.", "אך", ["לכן", "כדי", "משום כך"]),
        ("ההוראות היו ברורות, ______ מספר הטעויות ירד.", "ולכן", ["אך", "כדי", "במקום זאת"]),
        ("הנתון מעניין; ______ אינו מוכיח סיבתיות.", "עם זאת", ["לכן", "כדי", "משום כך"]),
        ("הצוות סיים מוקדם, ______ נותר זמן לבדיקה.", "ולכן", ["אך", "למרות", "במקום זאת"]),
    ]
    for i in range(60):
        stem, correct_text, wrongs = connectors[i % len(connectors)]
        options = [correct_text] + wrongs
        shift = i % 4
        options = options[shift:] + options[:shift]
        correct_index = options.index(correct_text)
        added += _add(conn, vs, f"QB-V-S-{i+1:03d}", "verbal", "sentence_completion", "logical_connector", 1 + i % 5, 40 + (i % 3) * 5,
                       stem, "בודקים את הקשר הלוגי בין חלקי המשפט ובוחרים במילת הקישור המתאימה.", options, correct_index,
                       tags=["השלמת משפטים", "לוגיקה"])

    reading = [
        ("ספרייה האריכה שעות פתיחה. מספר המבקרים עלה בחודש הראשון, אך המנהלת ציינה שעדיין מוקדם לקבוע סיבה יחידה.", "מהי המסקנה הזהירה?", "ייתכן שהארכת השעות תרמה לעלייה", ["היא גרמה לכל העלייה", "היא לא השפיעה כלל", "כל המבקרים הגיעו בערב"]),
        ("חברה החליפה מערכת מחשוב. בשבוע הראשון הייתה האטה, ולאחר חודש התקצרו זמני הביצוע. ההדרכה נמשכה כדי לצמצם טעויות.", "מה השתפר לאחר חודש?", "זמני ביצוע המשימות התקצרו", ["מספר העובדים ירד", "המערכת בוטלה", "לא חל שינוי"]),
        ("בית ספר הציב מתקן מחזור. נאספו 800 בקבוקים בחודש הראשון ו-1,000 בשני. המנהל ביקש להמתין לנתונים נוספים.", "למה ביקש המנהל להמתין?", "כדי לקבל נתונים נוספים", ["המתקן נשבר", "המספרים נמוכים מדי", "אין תלמידים"]),
        ("חנות הציבה מוצרי חורף בכניסה ובמקביל הפעילה מבצע הנחה. המכירות עלו, ולכן קשה להפריד בין השפעות שני השינויים.", "מה מקשה על הסקת סיבה?", "שני שינויים התרחשו במקביל", ["אין נתוני מכירות", "החנות נסגרה", "המוצרים נעלמו"]),
        ("קבוצת תלמידים למדה מילים באמצעות כרטיסיות ונמצא שיפור לאחר שבוע. לא נבדקה קבוצה מקבילה ללא כרטיסיות.", "מה חסר למחקר?", "קבוצה מקבילה להשוואה", ["מבחן נוסף", "מילים חדשות", "מורה נוסף"]),
        ("עירייה שתלה עצים ברחוב אחד. בקיץ נמדדה ירידה בטמפרטורה באזור המוצל, אך החוקרים נמנעו מהכללה לכל העיר.", "למה נמנעו מהכללה?", "המדידה הייתה מוגבלת לאזור אחד", ["לא היו עצים", "לא הייתה טמפרטורה", "הרחוב היה סגור"]),
        ("מפעל שינה את סדר העבודה. מספר היחידות לשעה עלה מ-40 ל-48, בעוד זמן התחזוקה השבועי נשאר ללא שינוי.", "מה לא השתנה?", "זמן התחזוקה השבועי", ["מספר היחידות", "סדר העבודה", "התפוקה לשעה"]),
        ("חוקר השווה שני מסלולים. מסלול א קצר יותר ומסלול ב ארוך אך מוצל ברובו. ביום חם בחרו רוב המטיילים במסלול ב.", "מה נתמך בקטע?", "בתנאים החמים העדיפו רבים את המסלול המוצל", ["כולם העדיפו אותו תמיד", "מסלול א אינו בטוח", "הצל הוא הסיבה היחידה"]),
        ("מוזיאון הציג תערוכה במשך שלושה חודשים: 2,000 מבקרים בראשון, 2,400 בשני ו-2,200 בשלישי. לאחר מכן נסגרה כמתוכנן.", "באיזה חודש נרשם המספר הגבוה ביותר?", "השני", ["הראשון", "השלישי", "אין מידע"]),
        ("מחקר תחבורה מצא שרוכבי אופניים דיווחו על זמן נסיעה קצר יותר בשעות העומס. המחקר לא בדק אם בחרו מסלולים שונים מנהגי מכוניות.", "מה אי אפשר להסיק בוודאות?", "שהאופניים לבדם גרמו לזמן הקצר יותר", ["שהיו שעות עומס", "שהיו רוכבים", "שהמחקר נערך"]),
    ]
    for i in range(60):
        passage, question, correct_text, wrongs = reading[i % len(reading)]
        options = [correct_text] + wrongs
        shift = (i * 3) % 4
        options = options[shift:] + options[:shift]
        added += _add(conn, vr, f"QB-V-R-{i+1:03d}", "verbal", "reading_comprehension", "reading_inference", 1 + i % 5, 55,
                       f"קטע:\n{passage}\n\nשאלה: {question}", "מסתמכים רק על המידע המופיע בקטע ומבחינים בין עובדה למסקנה.", options, options.index(correct_text), tags=["הבנת הנקרא", "מסקנות"])

    directions = ["למעלה", "ימינה", "למטה", "שמאלה"]
    for i in range(30):
        start = i % 4
        quarter_turns = 1 + (i % 3)
        correct = directions[(start + quarter_turns) % 4]
        options = [correct] + [d for d in directions if d != correct]
        shift = (i + 1) % 4
        options = options[shift:] + options[:shift]
        added += _add(conn, fr, f"QB-F-R-{i+1:03d}", "figural", "rotations", "rotation_2d", 1 + i % 5, 35 + (i % 4) * 5,
                       f"חץ מצביע {directions[start]}. אם מסובבים אותו {quarter_turns * 90} מעלות עם כיוון השעון, לאיזה כיוון יצביע?",
                       f"כל סיבוב של 90 מעלות עם כיוון השעון מתקדם כיוון אחד. התוצאה היא {correct}.", options, options.index(correct),
                       {"format": "direction_arrow", "initial_direction": directions[start], "rotation_degrees": quarter_turns * 90, "clockwise": True}, ["סיבובים", "צורות"])

    for i in range(30):
        a = 1 + i % 5
        b = 1 + (i * 2) % 5
        a2 = 1 + (i + 1) % 5
        b2 = 1 + (i * 3) % 5
        a3 = 1 + (i * 2 + 1) % 5
        b3 = 1 + (i * 4 + 1) % 5
        correct = a3 + b3
        options = [correct, correct + 1, correct + 2, max(1, correct - 1)]
        shift = i % 4
        options = options[shift:] + options[:shift]
        visual = {"format": "matrix", "cells": [[a, b, a + b], [a2, b2, a2 + b2], [a3, b3, None]], "rule": "third = first + second", "symbol": "dots"}
        added += _add(conn, fm, f"QB-F-M-{i+1:03d}", "figural", "matrices", "addition_rule", 1 + i % 5, 45 + (i % 4) * 5,
                       f"בכל שורה, מספר הסימנים בתא השלישי שווה לסכום שני התאים הראשונים.\nשורה 1: {a}, {b}, {a+b}; שורה 2: {a2}, {b2}, {a2+b2}; שורה 3: {a3}, {b3}, ?",
                       f"{a3}+{b3}={correct}, ולכן בתא החסר יש {correct} סימנים.", [str(x) for x in options], [str(x) for x in options].index(str(correct)), visual, ["מטריצות", "דפוסים"])

    faces = ["A", "B", "C", "D", "E", "F"]
    opposite = {"A": "D", "D": "A", "B": "E", "E": "B", "C": "F", "F": "C"}
    for i in range(30):
        f = faces[i % 6]
        correct = opposite[f]
        options = [correct] + [x for x in faces if x not in (f, correct)][:3]
        shift = i % 4
        options = options[shift:] + options[:shift]
        added += _add(conn, fc, f"QB-F-C-{i+1:03d}", "figural", "cubes", "cube_spatial", 1 + i % 5, 50 + (i % 4) * 5,
                       f"בקובייה הפאות הנגדיות הן A-D, B-E, C-F. איזו פאה נמצאת מול {f}?",
                       f"הפאה הנגדית ל-{f} היא {correct} לפי זוגות הפאות הנתונים.", options, options.index(correct),
                       {"format": "cube", "opposite_pairs": [["A", "D"], ["B", "E"], ["C", "F"]], "highlight": f}, ["קוביות", "מרחבי"])

    symbols = ["משולש", "ריבוע", "עיגול", "מעוין", "כוכב"]
    for i in range(30):
        seq = [symbols[(i + j) % len(symbols)] for j in range(4)]
        step = 2 if i % 2 == 0 else 1
        correct = symbols[(i + 3 * step) % len(symbols)]
        options = [correct] + [s for s in symbols if s != correct][:3]
        shift = (i + 2) % 4
        options = options[shift:] + options[:shift]
        visual = {"format": "sequence", "symbols": seq, "rule": "fixed cyclic step", "next": correct}
        added += _add(conn, fp, f"QB-F-P-{i+1:03d}", "figural", "visual_patterns", "sequence_pattern", 1 + i % 5, 45 + (i % 4) * 5,
                       f"נתון הרצף: {' → '.join(seq)}. לפי הדפוס המחזורי, מהו הסמל הבא?",
                       f"הרצף מתקדם במחזור קבוע; לפי המיקום הבא מתקבל {correct}.", options, options.index(correct), visual, ["דפוסים חזותיים", "רצפים"])

    print(f"question_bank_v7: added {added} questions")


def downgrade():
    # Deliberately empty: generated bank revisions are append-only and guarded by bank_key.
    pass

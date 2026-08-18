"""Correct answer keys in the second question-bank pool.

Revision ID: 20260818_question_bank_v5
Revises: 20260818_question_bank_v4
"""
from alembic import op
import sqlalchemy as sa
import json

revision = "20260818_question_bank_v5"
down_revision = "20260818_question_bank_v4"
branch_labels = None
depends_on = None

VERBAL = {
 "QB-V-036": [("דבורה : כוורת",False),("בונה : סכר",True),("מורה : כיתה",False),("ספר : מדף",False)],
 "QB-V-037": [("מגיה : טקסט",True),("שופט : משחק",False),("נהג : כביש",False),("רופא : בית חולים",False)],
 "QB-V-038": [("ביצה : אפרוח",True),("עץ : יער",False),("מים : כוס",False),("ספר : דף",False)],
 "QB-V-039": [("מד־מהירות : מהירות",True),("שעון : זמן",False),("משקל : גובה",False),("מפה : מרחק",False)],
 "QB-V-040": [("מכחול : ציור",False),("סולם : גובה",False),("מנוע : דלק",False),("מספריים : חיתוך",True)],
 "QB-V-041": [("לכן",True),("אולם",False),("אף על פי כן",False),("משום כך",False)],
 "QB-V-042": [("חד־משמעית",False),("זהירה",True),("מוחלטת",False),("מכרעת",False)],
 "QB-V-043": [("לכן",True),("עם זאת",False),("במקום זאת",False),("אף כי",False)],
 "QB-V-044": [("אקראיות",False),("דיוק",True),("הסתרה",False),("דחייה",False)],
 "QB-V-045": [("ולכן",False),("אך",True),("משום כך",False),("אם כן",False)],
 "QB-V-046": [("שהיה שיפור בדיוק",False),("שהמשוב ניתן מדי שבוע",False),("שהשיפור נמשך ללא משוב",True),("שהחוקרים לא בדקו המשך",False)],
 "QB-V-047": [("המכירות היו גבוהות יותר בחודש הראשון",True),("הספר נכשל",False),("כל הספרים נמכרים פחות בחודש השני",False),("הספר אזל מהמלאי",False)],
 "QB-V-048": [("המסלול הקצר בהכרח קל יותר",False),("המסלול הקצר מהיר יותר לפי הנתון, אך לא בהכרח קל יותר",True),("המסלול הארוך תמיד עדיף",False),("אין הבדל בין המסלולים",False)],
 "QB-V-049": [("25%",False),("50%",False),("75%",True),("80%",False)],
 "QB-V-050": [("שינה גורמת בהכרח לריכוז",False),("נמצא קשר אך לא הוכחה סיבתיות",True),("אין קשר",False),("ריכוז גורם לשינה",False)],
}

FIG = {
 "QB-F-051": [("למעלה",True),("ימינה",False),("למטה",False),("שמאלה",False)],
 "QB-F-052": [("למעלה",False),("ימינה",True),("למטה",False),("שמאלה",False)],
 "QB-F-053": [("למעלה",True),("ימינה",False),("למטה",False),("שמאלה",False)],
 "QB-F-054": [("לא",True),("כן",False),("רק לפעמים",False),("לא ניתן לדעת",False)],
 "QB-F-055": [("כן",False),("לא",True),("רק ב־90°",False),("לא ניתן לדעת",False)],
 "QB-F-056": [("6",True),("5",False),("7",False),("8",False)],
 "QB-F-057": [("1",False),("2",False),("3",True),("4",False)],
 "QB-F-058": [("12",False),("14",False),("16",True),("18",False)],
 "QB-F-059": [("4",False),("5",True),("6",False),("7",False)],
 "QB-F-060": [("4",False),("5",True),("6",False),("7",False)],
 "QB-F-061": [("B",True),("C",False),("D",False),("E",False)],
 "QB-F-062": [("A",False),("B",False),("C",False),("D",True)],
 "QB-F-063": [("C",False),("D",False),("E",False),("F",True)],
 "QB-F-064": [("כן",False),("לא",True),("רק לפעמים",False),("לא ניתן לדעת",False)],
 "QB-F-065": [("A",False),("B",False),("C",True),("D",False)],
}


def _fix(conn, key, answers):
    qid = conn.execute(sa.text("SELECT id FROM questions WHERE question_metadata ->> 'bank_key'=:k"), {"k": key}).scalar()
    if not qid:
        return
    conn.execute(sa.text("DELETE FROM answers WHERE question_id=:qid"), {"qid": qid})
    for order, (text, correct) in enumerate(answers, 1):
        conn.execute(sa.text("""
            INSERT INTO answers (question_id, answer_text, is_correct, explanation_if_selected, "order", created_at, updated_at)
            VALUES (:qid,:text,:correct,CAST(:exp AS JSON),:ord,NOW(),NOW())
        """), {"qid":qid,"text":text,"correct":correct,"exp":json.dumps({"format":"markdown","body":"תשובה שנקבעה לפי מפתח השאלה המאושר."},ensure_ascii=False),"ord":order})
    conn.execute(sa.text("DELETE FROM question_versions WHERE question_id=:qid"), {"qid":qid})
    conn.execute(sa.text("""
        INSERT INTO question_versions (question_id,version_number,category_id,question_type,difficulty,status,body,solution_text,question_metadata,answer_snapshot,recommended_time_seconds,created_at)
        SELECT q.id,1,q.category_id,q.question_type,q.difficulty,q.status,q.body,q.solution_text,q.question_metadata,
               CAST((SELECT jsonb_agg(jsonb_build_object('answer_text',a.answer_text,'is_correct',a.is_correct,'order',a."order") ORDER BY a."order") FROM answers a WHERE a.question_id=q.id) AS JSONB),
               q.recommended_time_seconds,NOW() FROM questions q WHERE q.id=:qid
    """), {"qid":qid})


def upgrade():
    conn=op.get_bind()
    for key,answers in {**VERBAL,**FIG}.items(): _fix(conn,key,answers)


def downgrade():
    # Data correction only; retaining corrected answers is safer than restoring the erroneous keys.
    pass

"""Complete the initial 45-question TIL simulation pool.

Revision ID: 20260818_question_bank_v3
Revises: 20260818_question_bank_v2
"""

import json
from alembic import op
import sqlalchemy as sa

revision = "20260818_question_bank_v3"
down_revision = "20260818_question_bank_v2"
branch_labels = None
depends_on = None


def _cat(conn, name, typ, parent_name):
    parent = conn.execute(sa.text("SELECT id FROM categories WHERE name=:n AND type=:t AND parent_id IS NULL LIMIT 1"), {"n": parent_name, "t": typ}).scalar()
    return conn.execute(sa.text("SELECT id FROM categories WHERE name=:n AND type=:t AND parent_id=:p LIMIT 1"), {"n": name, "t": typ, "p": parent}).scalar()


def _add(conn, cid, p):
    if conn.execute(sa.text("SELECT 1 FROM questions WHERE question_metadata ->> 'bank_key'=:k"), {"k":p["key"]}).first():
        return
    meta={"bank_key":p["key"],"main_category":p["main"],"subcategory":p["sub"],"skill":p["skill"],"difficulty_level":p["level"],"tags":p.get("tags",[]),"visual":p.get("visual"),"psychometrics":{"a":None,"b":None,"c":None},"quality":{"review_status":"APPROVED","single_correct_answer":True,"source":"original_til_bank_v3"}}
    qid=conn.execute(sa.text("INSERT INTO questions (category_id,question_type,difficulty,status,body,solution_text,recommended_time_seconds,question_metadata,created_at,updated_at) VALUES (:cid,'multiple_choice','exam','published',CAST(:body AS JSON),CAST(:solution AS JSON),:secs,CAST(:meta AS JSON),NOW(),NOW()) RETURNING id"),{"cid":cid,"body":json.dumps({"format":"markdown","body":p["body"]},ensure_ascii=False),"solution":json.dumps({"format":"markdown","body":p["solution"]},ensure_ascii=False),"secs":p["secs"],"meta":json.dumps(meta,ensure_ascii=False)}).scalar_one()
    snap=[]
    for i,(text,ok,exp) in enumerate(p["answers"],1):
        aid=conn.execute(sa.text("INSERT INTO answers (question_id,answer_text,is_correct,explanation_if_selected,\"order\",created_at,updated_at) VALUES (:qid,:text,:ok,CAST(:exp AS JSON),:ord,NOW(),NOW()) RETURNING id"),{"qid":qid,"text":text,"ok":ok,"exp":json.dumps({"format":"markdown","body":exp},ensure_ascii=False),"ord":i}).scalar_one()
        snap.append({"id":aid,"answer_text":text,"is_correct":ok,"explanation_if_selected":{"format":"markdown","body":exp},"order":i})
    conn.execute(sa.text("INSERT INTO question_versions (question_id,version_number,category_id,question_type,difficulty,status,body,solution_text,question_metadata,answer_snapshot,recommended_time_seconds,created_at) SELECT :qid,1,category_id,question_type,difficulty,status,body,solution_text,question_metadata,CAST(:snap AS JSONB),recommended_time_seconds,NOW() FROM questions WHERE id=:qid"),{"qid":qid,"snap":json.dumps(snap,ensure_ascii=False)})


def upgrade():
    conn=op.get_bind()
    cats={
      "q1":_cat(conn,"אחוזים ושינויים","quantitative","חשיבה כמותית"),"q2":_cat(conn,"יחס והספק","quantitative","חשיבה כמותית"),"q3":_cat(conn,"סדרות מספרים","quantitative","חשיבה כמותית"),
      "v1":_cat(conn,"אנלוגיות","verbal","חשיבה מילולית"),"v2":_cat(conn,"השלמת משפטים","verbal","חשיבה מילולית"),"v3":_cat(conn,"הבנת הנקרא","verbal","חשיבה מילולית"),
      "f1":_cat(conn,"סיבוב צורות","figural","חשיבה מרחבית וצורנית"),"f2":_cat(conn,"מטריצות צורניות","figural","חשיבה מרחבית וצורנית"),"f3":_cat(conn,"קוביות ומרחב","figural","חשיבה מרחבית וצורנית")}
    qs=[
      ("q1",{"key":"QB-Q-010","main":"quantitative","sub":"percentages","skill":"percentage_points","level":1,"secs":30,"body":"בכיתה 20 תלמידים, ו־30% מהם נעדרו. כמה תלמידים נעדרו?","solution":"30% מ־20 הם 6.","answers":[("4",False,"20% הם 4."),("6",True,"20×0.30=6."),("8",False,"40% הם 8."),("10",False,"50% הם 10.")]}),
      ("q1",{"key":"QB-Q-011","main":"quantitative","sub":"percentages","skill":"successive_change","level":4,"secs":50,"body":"כמות גדלה מ־400 ל־460. בכמה אחוזים גדלה?","solution":"הגידול הוא 60. 60/400=15%.","answers":[("10%",False,"40 היה גידול של 10%."),("12%",False,"48 היה גידול של 12%."),("15%",True,"60/400=0.15."),("20%",False,"80 היה גידול של 20%.")]}),
      ("q2",{"key":"QB-Q-012","main":"quantitative","sub":"rates","skill":"work_rate","level":2,"secs":40,"body":"פועל מסיים משימה ב־6 שעות. בקצב קבוע, איזה חלק מהמשימה יסיים ב־2 שעות?","solution":"הקצב הוא שישית משימה לשעה, לכן בשעתיים יבוצע שליש.","answers":[("1/6",False,"זה חלק של שעה אחת."),("1/3",True,"2/6=1/3."),("1/2",False,"זה דורש 3 שעות."),("2/3",False,"זה דורש 4 שעות.")]}),
      ("q2",{"key":"QB-Q-013","main":"quantitative","sub":"rates","skill":"ratio","level":5,"secs":60,"body":"יחס הבנים לבנות בקבוצה הוא 3:5. אם יש 32 תלמידים, כמה בנים יש?","solution":"סה״כ 8 חלקים. כל חלק 4 תלמידים. בנים הם 3×4=12.","answers":[("10",False,"יחס 2.5:5 אינו הנתון."),("12",True,"3/8×32=12."),("15",False,"זה מספר הבנות כמעט אך לא נכון."),("20",False,"זה 5/8×32, כלומר בנות.")]}),
      ("q3",{"key":"QB-Q-014","main":"quantitative","sub":"sequences","skill":"multiplicative_pattern","level":3,"secs":45,"body":"מהו המספר הבא: 81, 27, 9, 3, ?","solution":"כל איבר מתחלק ב־3. לכן 3/3=1.","answers":[("0",False,"אין חיסור קבוע."),("1",True,"החלוקה ב־3 ממשיכה."),("2",False,"אינו מתאים."),("6",False,"זה כפל ב־2.")]}),
      ("q3",{"key":"QB-Q-015","main":"quantitative","sub":"sequences","skill":"alternating","level":5,"secs":65,"body":"מהו המספר הבא: 4, 7, 14, 17, 34, 37, ?","solution":"הדפוס מתחלף: +3, ×2, +3, ×2, +3, לכן 37×2=74.","answers":[("40",False,"זה היה +3 נוסף."),("71",False,"אינו מכפיל ב־2."),("74",True,"37×2=74."),("80",False,"אין כלל כזה.")]}),
      ("v1",{"key":"QB-V-009","main":"verbal","sub":"analogies","skill":"function","level":2,"secs":35,"body":"מפתח : מנעול — מהו הזוג הדומה ביותר?","solution":"מפתח הוא אמצעי לפתיחת מנעול; קוד הוא אמצעי לפתיחת מערכת מוגנת.","answers":[("קוד : מערכת",True,"אותו יחס של אמצעי המאפשר פתיחה/גישה."),("דלת : בית",False,"חלק ומכלול."),("כיסא : שולחן",False,"פריטים סמוכים."),("ספר : עט",False,"פריטים המשמשים יחד.")]}),
      ("v1",{"key":"QB-V-010","main":"verbal","sub":"analogies","skill":"degree_relation","level":4,"secs":45,"body":"לחישה : דיבור — מהו הזוג בעל היחס הדומה ביותר?","solution":"לחישה היא צורה חלשה יותר של דיבור; טפטוף הוא צורה חלשה יותר של גשם.","answers":[("טפטוף : גשם",True,"אותו יחס של עוצמה נמוכה יותר."),("ענן : גשם",False,"גורם ותוצאה."),("מים : נהר",False,"חלק/מכלול או מקור."),("רוח : סערה",False,"יחס עוצמה אפשרי אך אינו מדויק כמו הזוג הראשון.")]}),
      ("v2",{"key":"QB-V-011","main":"verbal","sub":"sentence_completion","skill":"causal_logic","level":3,"secs":45,"body":"המשימה הושלמה מוקדם מן הצפוי, ______ הצוות הצליח להקדיש זמן נוסף לבדיקות לפני ההגשה.","solution":"הקדמה אפשרה זמן נוסף, לכן 'ולכן' מתאים.","answers":[("אולם",False,"יוצר ניגוד במקום תוצאה."),("ולכן",True,"המשפט מבטא תוצאה."),("אף כי",False,"יוצר ויתור."),("למרות זאת",False,"אינו מחבר סיבה לתוצאה.")]}),
      ("v2",{"key":"QB-V-012","main":"verbal","sub":"sentence_completion","skill":"contrast","level":5,"secs":60,"body":"הדו״ח נראה משכנע במבט ראשון; ______, בדיקה נוספת חשפה כמה הנחות שלא נבדקו.","solution":"נדרש מחבר ניגוד שמציג שינוי בהערכה: עם זאת.","answers":[("לכן",False,"תוצאה ולא ניגוד."),("עם זאת",True,"מתאים לניגוד בין הרושם הראשוני לבדיקה."),("משום כך",False,"סיבה/תוצאה."),("כמו כן",False,"הוספה ולא ניגוד.")]}),
      ("v3",{"key":"QB-V-013","main":"verbal","sub":"reading","skill":"detail","level":1,"secs":35,"body":"טקסט: 'הספרייה פתוחה בימים א׳–ה׳ עד 20:00 וביום ו׳ עד 12:00.' עד איזו שעה פתוחה הספרייה ביום ו׳?","solution":"הטקסט מציין במפורש שביום ו׳ היא פתוחה עד 12:00.","answers":[("10:00",False,"לא מצוין."),("12:00",True,"זו השעה המופיעה בטקסט."),("18:00",False,"זו אינה השעה של יום ו׳."),("20:00",False,"זו שעת הסגירה בימים א׳–ה׳.")]}),
      ("v3",{"key":"QB-V-014","main":"verbal","sub":"reading","skill":"inference","level":4,"secs":55,"body":"טקסט: 'לאחר שהחברה שינתה את תהליך ההכשרה, זמן ההשתלבות של עובדים חדשים התקצר. מספר הטעויות בחודש הראשון נותר ללא שינוי.' איזו מסקנה סבירה?","solution":"ההכשרה החדשה קיצרה השתלבות, אך לפי הנתון לא הוכח שיפור במספר הטעויות.","answers":[("ההכשרה הגדילה טעויות",False,"המספר נותר ללא שינוי."),("ההכשרה קיצרה השתלבות אך לא שינתה את מספר הטעויות לפי הנתונים",True,"זו מסקנה ישירה וזהירה."),("ההכשרה נכשלה לחלוטין",False,"יש שיפור בזמן ההשתלבות."),("כל העובדים טועים פחות",False,"הנתונים אינם אומרים זאת.")]}),
      ("f1",{"key":"QB-F-007","main":"figural","sub":"rotation","skill":"rotation_270","level":2,"secs":40,"body":"חץ מצביע למעלה. לאחר סיבוב של 270° עם כיוון השעון, לאן יצביע?","solution":"270° עם כיוון השעון שקול ל־90° נגד כיוון השעון: למעלה הופך לשמאל.","visual":{"format":"instruction","render":"arrow_up_rotate_clockwise_270"},"answers":[("ימין",False,"זהו 90° עם כיוון השעון."),("שמאל",True,"270° עם כיוון השעון מוביל לשמאל."),("למטה",False,"זהו 180°."),("למעלה",False,"זהו 360° או 0°.")]}),
      ("f1",{"key":"QB-F-008","main":"figural","sub":"rotation","skill":"shape_invariance","level":4,"secs":50,"body":"משולש שווה־צלעות מסובב ב־120°. האם צורתו החיצונית משתנה?","solution":"לא. משולש שווה־צלעות בעל סימטריה סיבובית של 120°, ולכן מתקבל אותו מראה חיצוני.","visual":{"format":"instruction","render":"equilateral_triangle_rotation_120"},"answers":[("כן, הוא הופך לריבוע",False,"סיבוב אינו משנה מספר צלעות."),("כן, הוא הופך למעוין",False,"אין שינוי בצלעות."),("לא, הוא נראה זהה",True,"120° הוא זווית סימטריה סיבובית של המשולש."),("לא ניתן לדעת",False,"הסימטריה מספקת תשובה.")]}),
      ("f2",{"key":"QB-F-009","main":"figural","sub":"matrix","skill":"addition_rule","level":3,"secs":50,"body":"בכל שורה במטריצה מספר הקווים בתא השלישי שווה לסכום הקווים בשני התאים הראשונים. בשורה האחרונה יש 2 ו־3. כמה קווים צריכים להיות בתא השלישי?","solution":"2+3=5.","visual":{"format":"matrix","cells":[[1,2,3],[2,1,3],[2,3,null]],"rule":"third=sum(first,second)"},"answers":[("4",False,"חיבור שגוי."),("5",True,"2+3=5."),("6",False,"כפל או חיבור נוסף."),("7",False,"אין בסיס לכלל.")]}),
      ("f2",{"key":"QB-F-010","main":"figural","sub":"matrix","skill":"rotation_pattern","level":5,"secs":70,"body":"בכל תא מופיע חץ. בכל מעבר ימינה החץ מסתובב 90° עם כיוון השעון, ובכל מעבר מטה 90° נגד כיוון השעון. אם התא העליון־שמאלי מצביע למעלה, לאן יצביע התא התחתון־ימני?","solution":"שני צעדים ימינה נותנים 180° עם כיוון השעון; שני צעדים מטה נותנים 180° נגד כיוון השעון. יחד 360°, ולכן שוב למעלה.","visual":{"format":"matrix","rule":"right=+90deg, down=-90deg","origin":"up"},"answers":[("למעלה",True,"הסיבובים מתקזזים ל־360°."),("ימינה",False,"נשאר סיבוב נטו של 90° בלבד."),("למטה",False,"הנטו אינו 180°."),("שמאלה",False,"הנטו אינו 270°.")] }),
      ("f3",{"key":"QB-F-011","main":"figural","sub":"cube","skill":"adjacency","level":3,"secs":50,"body":"בקובייה A מול B, C מול D, E מול F. אילו פאות יכולות להיפגש בקודקוד אחד?","solution":"בקודקוד יכולות להיפגש רק פאות שאינן נגדיות. A,C,E הן משלוש זוגות שונות ולכן יכולות להיפגש בקודקוד.","visual":{"format":"cube","opposites":[["A","B"],["C","D"],["E","F"]]},"answers":[("A,B,C",False,"A ו־B נגדיות."),("A,C,E",True,"אין ביניהן זוג נגדיות."),("A,D,B",False,"A ו־B נגדיות."),("C,D,F",False,"C ו־D נגדיות.")] }),
      ("f3",{"key":"QB-F-012","main":"figural","sub":"cube","skill":"opposite_faces","level":4,"secs":55,"body":"אם בקובייה A מול B ו־C מול D, ואילו E צמודה ל־A ול־C, איזו פאה חייבת להיות מול E?","solution":"הפאה שמול E היא F, הפאה הנותרת בזוג הנגדי השלישי.","visual":{"format":"cube","opposites":[["A","B"],["C","D"],["E","F"]]},"answers":[("A",False,"A צמודה ל־E."),("B",False,"B יכולה להיות צמודה ל־E."),("F",True,"F היא הפאה הנגדית ל־E."),("C",False,"C צמודה ל־E.")] }),
    ]
    for ck,p in qs: _add(conn,cats[ck],p)


def downgrade():
    conn=op.get_bind()
    for prefix,start,end in [("Q",10,15),("V",9,14),("F",7,12)]:
        for i in range(start,end+1):
            key=f"QB-{prefix}-{i:03d}"
            qid=conn.execute(sa.text("SELECT id FROM questions WHERE question_metadata ->> 'bank_key'=:k"),{"k":key}).scalar()
            if qid:
                conn.execute(sa.text("DELETE FROM question_versions WHERE question_id=:id"),{"id":qid})
                conn.execute(sa.text("DELETE FROM answers WHERE question_id=:id"),{"id":qid})
                conn.execute(sa.text("DELETE FROM questions WHERE id=:id"),{"id":qid})

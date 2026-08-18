"""Expand the TIL bank with 240 original verbal and figural questions.

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

ANALOGIES = [('ציפור','קן'),('דבורה','כוורת'),('בונה','סכר'),('מורה','כיתה'),('ספר','ספרייה'),('מוצג','מוזיאון'),('מכתב','מעטפה'),('מפתח','מנעול'),('רופא','מרפאה'),('שופט','בית משפט'),('דג','מים'),('ציפור','אוויר'),('זרע','צמח'),('ביצה','אפרוח'),('גולם','פרפר'),('מכחול','ציור'),('מספריים','חיתוך'),('מפתח','פתיחה'),('מדחום','טמפרטורה'),('מד מהירות','מהירות')]
EXTRA_ANALOGIES = [('חלב','גבינה'),('ענן','גשם'),('מפתח ברגים','בורג'),('רמקול','קול'),('מצפן','כיוון'),('מסננת','נוזל'),('סופר','רומן'),('צלם','תמונה'),('אדריכל','בניין'),('גנן','גינה')]
CONNECTORS = [('הגשם פסק, ______ הרחובות נותרו רטובים.','אך',['לכן','משום כך','אם כן']),('הנתונים היו חלקיים, ______ החוקרים נמנעו ממסקנה חד־משמעית.','ולכן',['אולם','למרות','אף על פי']),('הצוות סיים את המשימה מוקדם; ______ נותר זמן לבדיקת איכות.','לכן',['אולם','אף כי','מצד שני']),('המחיר ירד, ______ הביקוש לא השתנה.','אך',['לכן','משום כך','אם כן']),('החוקר חזר על הניסוי ______ לוודא שהתוצאה אינה מקרית.','כדי',['אולם','לכן','אף על פי']),('המסלול ארוך יותר; ______ הוא בטוח יותר.','עם זאת',['לכן','משום כך','כדי']),('המערכת התריעה על תקלה, ______ הטכנאי עצר את התהליך.','ולכן',['אולם','אף כי','למרות']),('המשימה נראתה פשוטה, ______ היא דרשה ריכוז רב.','אך',['לכן','משום כך','כדי']),('העובדים קיבלו הוראות ברורות, ______ מספר הטעויות ירד.','ולכן',['אולם','אף על פי','במקום זאת']),('הנתון מעניין; ______ אין בו לבדו כדי להוכיח סיבתיות.','עם זאת',['לכן','משום כך','כדי'])]
PASSAGES = [
('ספרייה עירונית קטנה האריכה את שעות הפתיחה בערב. בחודש הראשון נרשמה עלייה במספר המבקרים, אך מנהלת הספרייה ציינה שעדיין מוקדם לקבוע שהשינוי הוא הסיבה היחידה לעלייה.',[('מה קרה לאחר הארכת שעות הפתיחה?','מספר המבקרים עלה',['מספר המבקרים ירד','הספרייה נסגרה','לא חל שינוי']),('מה הסתייגה המנהלת מלקבוע?','שהשינוי הוא הסיבה היחידה לעלייה',['שהמבקרים קוראים','שהשעות הוארכו','שהספרייה קטנה']),('איזו מסקנה זהירה מתאימה?','ייתכן שהארכת השעות תרמה לעלייה',['ברור שהיא גרמה לכל העלייה','היא לא השפיעה כלל','כל המבקרים הגיעו בערב'])]),
('חברה החליפה את מערכת המחשוב שלה. בשבוע הראשון העובדים דיווחו על האטה, אך לאחר חודש זמני ביצוע המשימות התקצרו. החברה החליטה להמשיך בהדרכה כדי לצמצם טעויות.',[('מה קרה בשבוע הראשון?','נרשמה האטה',['המשימות התקצרו','המערכת בוטלה','לא היו דיווחים']),('מה השתפר לאחר חודש?','זמני ביצוע המשימות התקצרו',['העובדים הפסיקו לעבוד','המערכת נסגרה','מספר המחשבים ירד']),('למה נמשכה ההדרכה?','כדי לצמצם טעויות',['כדי להאריך משימות','כדי לבטל את המערכת','כדי להקטין את מספר העובדים'])]),
('חוקר השווה שני מסלולי הליכה. מסלול א קצר יותר, ואילו מסלול ב ארוך אך מוצל ברובו. ביום חם בחרו רוב המטיילים במסלול ב.',[('איזה מסלול קצר יותר?','א',['ב','שניהם שווים','אין מידע']),('מה מאפיין את מסלול ב?','הוא מוצל ברובו',['הוא קצר יותר','הוא סגור','אין בו שביל']),('איזו מסקנה נתמכת?','בתנאים החמים העדיפו רבים את המסלול המוצל',['כולם העדיפו אותו בכל תנאי','מסלול א אינו בטוח','הצל הוא הסיבה היחידה'])]),
('בבית ספר הוצב מתקן למחזור בקבוקים. בחודש הראשון נאספו 800 בקבוקים, ובחודש השני 1,000. מנהל בית הספר ציין שהמספרים מעידים על שימוש גובר במתקן, אך ביקש להמתין לנתונים נוספים.',[('כמה בקבוקים נאספו בחודש השני?','1,000',['800','1,200','600']),('מה השתנה בין החודשים?','כמות הבקבוקים שנאספה גדלה',['היא קטנה','המתקן הוסר','אין שינוי']),('מדוע ביקש המנהל להמתין?','כדי לקבל נתונים נוספים',['כי המתקן נשבר','כי המספרים נמוכים מדי','כי אין תלמידים'])]),
('חנות ניסתה להציב את מוצרי החורף בכניסה. המכירות עלו בשבועיים הראשונים, אך באותו זמן הופעל גם מבצע הנחה. לכן קשה לקבוע איזה מהשינויים תרם יותר לעלייה.',[('מה קרה למכירות?','הן עלו',['הן ירדו','לא השתנו','החנות נסגרה']),('איזה שינוי נוסף התרחש?','הופעל מבצע הנחה',['המוצרים הוסרו','המחיר הוכפל','הכניסה נסגרה']),('מה הקושי בהסקת מסקנה?','שני שינויים התרחשו במקביל',['אין נתוני מכירות','אין מוצרים','החנות לא פתוחה'])]),
('קבוצת תלמידים למדה מילים חדשות באמצעות כרטיסיות. לאחר שבוע נבחנה הקבוצה ונמצא שיפור. החוקרים ציינו שלא נבדקה קבוצה מקבילה שלא השתמשה בכרטיסיות.',[('באמצעות מה למדה הקבוצה?','כרטיסיות',['סרטונים','הרצאות','תרגום אוטומטי']),('מה נמצא לאחר שבוע?','שיפור במבחן',['ירידה','אין שינוי','ביטול המבחן']),('מה חסר למחקר?','קבוצה מקבילה להשוואה',['מבחן נוסף','מילים חדשות','תלמידים'])]),
('עירייה שתלה עצים ברחוב מרכזי. בקיץ נמדדה ירידה בטמפרטורה באזור המוצל. המדידה נערכה רק ברחוב אחד, ולכן החוקרים נמנעו מהכללה לכל העיר.',[('מה נמדד בקיץ?','ירידה בטמפרטורה באזור המוצל',['עלייה','גשם','מהירות רוח']),('היכן נערכה המדידה?','ברחוב אחד',['בכל העיר','בפארק','בכמה מדינות']),('למה נמנעו מהכללה?','המדידה הייתה מוגבלת לאזור אחד',['לא היו עצים','לא הייתה טמפרטורה','הרחוב היה סגור'])]),
('מפעל שינה את סדר העבודה. מספר היחידות לשעה עלה מ־40 ל־48. עם זאת, זמן התחזוקה השבועי נשאר ללא שינוי.',[('מה היה הקצב החדש?','48 יחידות לשעה',['40','52','32']),('מה לא השתנה?','זמן התחזוקה השבועי',['מספר היחידות','סדר העבודה','הקצב']),('איזה שינוי התרחש?','התפוקה לשעה גדלה',['התפוקה ירדה','התחזוקה בוטלה','הקצב לא השתנה'])]),
('מחקר על תחבורה מצא שאנשים שבחרו באופניים דיווחו על זמן נסיעה קצר יותר בשעות העומס. המחקר לא בדק אם הם בחרו מסלולים שונים מנהגי המכוניות.',[('מה דיווחו רוכבי האופניים?','זמן נסיעה קצר יותר בשעות העומס',['זמן ארוך יותר','אין הבדל','אין נסיעות']),('מה לא נבדק?','האם נבחרו מסלולים שונים',['השעה','התחבורה','מספר האופניים']),('מה אי אפשר להסיק בוודאות?','שהאופניים לבדם גרמו לזמן הקצר יותר',['שהיו שעות עומס','שהיו רוכבים','שהמחקר נערך'])]),
('מוזיאון הציג תערוכה זמנית במשך שלושה חודשים. בחודש הראשון הגיעו 2,000 מבקרים, בשני 2,400 ובשלישי 2,200. לאחר מכן נסגרה התערוכה כמתוכנן.',[('באיזה חודש נרשם המספר הגבוה ביותר?','השני',['הראשון','השלישי','לא ידוע']),('כמה הגיעו בחודש הראשון?','2,000',['2,200','2,400','1,800']),('מה קרה לאחר שלושת החודשים?','התערוכה נסגרה',['היא הוארכה','היא עברה לעיר אחרת','לא ידוע'])])]

def _cat(conn, child, typ, parent):
    pid=conn.execute(sa.text("SELECT id FROM categories WHERE name=:n AND type=:t AND parent_id IS NULL LIMIT 1"),{"n":parent,"t":typ}).scalar()
    return conn.execute(sa.text("SELECT id FROM categories WHERE name=:n AND type=:t AND parent_id=:p LIMIT 1"),{"n":child,"t":typ,"p":pid}).scalar() if pid else None

def _add(conn,cid,key,main,sub,skill,level,secs,body,solution,answers,visual=None,tags=None):
    if not cid or conn.execute(sa.text("SELECT 1 FROM questions WHERE question_metadata ->> 'bank_key'=:k LIMIT 1"),{"k":key}).first(): return 0
    meta={"bank_key":key,"main_category":main,"subcategory":sub,"skill":skill,"difficulty_level":level,"tags":tags or [],"visual":visual,"psychometrics":{"a":None,"b":None,"c":None},"quality":{"review_status":"APPROVED","single_correct_answer":True,"source":"original_til_bank_v7","calibration_status":"initial"}}
    difficulty="easy" if level<=2 else ("medium" if level==3 else "exam")
    qid=conn.execute(sa.text("""INSERT INTO questions (category_id,question_type,difficulty,status,body,solution_text,recommended_time_seconds,question_metadata,created_at,updated_at) VALUES (:cid,'multiple_choice',:difficulty,'published',CAST(:body AS JSON),CAST(:solution AS JSON),:secs,CAST(:meta AS JSON),NOW(),NOW()) RETURNING id"""),{"cid":cid,"difficulty":difficulty,"body":json.dumps({"format":"markdown","body":body},ensure_ascii=False),"solution":json.dumps({"format":"markdown","body":solution},ensure_ascii=False),"secs":secs,"meta":json.dumps(meta,ensure_ascii=False)}).scalar_one()
    snap=[]
    for order,(text,ok,exp) in enumerate(answers,1):
        aid=conn.execute(sa.text("""INSERT INTO answers (question_id,answer_text,is_correct,explanation_if_selected,"order",created_at,updated_at) VALUES (:qid,:text,:ok,CAST(:exp AS JSON),:ord,NOW(),NOW()) RETURNING id"""),{"qid":qid,"text":text,"ok":ok,"exp":json.dumps({"format":"markdown","body":exp},ensure_ascii=False),"ord":order}).scalar_one()
        snap.append({"id":aid,"answer_text":text,"is_correct":ok,"explanation_if_selected":{"format":"markdown","body":exp},"order":order})
    conn.execute(sa.text("""INSERT INTO question_versions (question_id,version_number,category_id,question_type,difficulty,status,body,solution_text,question_metadata,answer_snapshot,recommended_time_seconds,created_at,updated_at) SELECT :qid,1,category_id,question_type,difficulty,status,body,solution_text,question_metadata,CAST(:snap AS JSONB),recommended_time_seconds,NOW(),NOW() FROM questions WHERE id=:qid"""),{"qid":qid,"snap":json.dumps(snap,ensure_ascii=False)})
    return 1

def _answers(options,correct): return [(o,o==correct,"זו התשובה הנכונה לפי הכלל." if o==correct else "המסיח אינו מתאים לכלל.") for o in options]

def upgrade():
    conn=op.get_bind(); cats={"va":_cat(conn,"אנלוגיות","verbal","חשיבה מילולית"),"vs":_cat(conn,"השלמת משפטים","verbal","חשיבה מילולית"),"vr":_cat(conn,"הבנת הנקרא","verbal","חשיבה מילולית"),"fr":_cat(conn,"סיבוב צורות","figural","חשיבה מרחבית וצורנית"),"fm":_cat(conn,"מטריצות צורניות","figural","חשיבה מרחבית וצורנית"),"fc":_cat(conn,"קוביות ומרחב","figural","חשיבה מרחבית וצורנית"),"fp":_cat(conn,"דפוסים חזותיים","figural","חשיבה מרחבית וצורנית")}; added=0
    rows=[(a,b,v) for a,b in ANALOGIES for v in (1,2)]+[(a,b,1) for a,b in EXTRA_ANALOGIES]
    for i,(a,b,v) in enumerate(rows,1):
        ds=[ANALOGIES[(i+j*3+v)%len(ANALOGIES)] for j in (1,2,3)]; correct=f"{a} : {b}"; opts=[correct]+[f"{x} : {y}" for x,y in ds]; r=(i+v)%4; opts[0],opts[r]=opts[r],opts[0]
        added+=_add(conn,cats["va"],f"QB-V-A-{i:03d}","verbal","analogies","relationship_analogy",1+(i%5),35+(i%3)*5,f"{a} : {b} — איזה זוג מציג קשר דומה ביותר?","מזהים את סוג הקשר בין שני המושגים ובוחרים זוג בעל אותו יחס.",_answers(opts,correct),tags=["אנלוגיות","יחסים"])
    for i,(stem,correct,wrongs) in enumerate(CONNECTORS*4,1):
        opts=[correct]+wrongs; r=i%4; opts[0],opts[r]=opts[r],opts[0]
        added+=_add(conn,cats["vs"],f"QB-V-S-{i:03d}","verbal","sentence_completion","logical_connector",1+(i%5),40+(i%3)*5,stem,"בודקים את הקשר הלוגי בין חלקי המשפט ובוחרים את מילת הקישור המתאימה.",_answers(opts,correct),tags=["השלמת משפטים","לוגיקה"])
    n=0
    for pi,(passage,questions) in enumerate(PASSAGES,1):
        for question,correct,wrongs,_ in questions:
            n+=1; opts=[correct]+wrongs; r=(pi+n)%4; opts[0],opts[r]=opts[r],opts[0]
            added+=_add(conn,cats["vr"],f"QB-V-R-{n:03d}","verbal","reading_comprehension","reading_inference",1+(n%5),55,f"קטע:\n{passage}\n\nשאלה: {question}","מסתמכים רק על המידע בקטע ומבחינים בין עובדה, מסקנה והסקה שאינה נתמכת.",_answers(opts,correct),tags=["הבנת הנקרא","מסקנות"])
    dirs=["למעלה","ימינה","למטה","שמאלה"]
    for i in range(30):
        start=i%4; angle=(i%3+1)*90; correct=dirs[(start+angle//90)%4]; opts=[correct]+[dirs[(start+angle//90+j)%4] for j in (1,2,3)]; r=(i+1)%4; opts[0],opts[r]=opts[r],opts[0]
        added+=_add(conn,cats["fr"],f"QB-F-R-{i+1:03d}","figural","rotations","rotation_2d",1+(i%5),35+(i%4)*5,f"חץ מצביע {dirs[start]}. אם מסובבים אותו {angle}° עם כיוון השעון, לאיזה כיוון יצביע?",f"כל 90° עם כיוון השעון מזיזים את הכיוון צעד אחד. התוצאה היא {correct}.",_answers(opts,correct),{"format":"direction_arrow","initial_direction":dirs[start],"rotation_degrees":angle,"clockwise":True},["סיבובים","צורות"])
    for i in range(30):
        a=1+i%5; b=1+(i*2)%5; a2=1+(i+1)%5; b2=1+(i*3)%5; a3=1+(i*2+1)%5; b3=1+(i*4+1)%5; correct=a3+b3; opts=[correct,max(1,correct-2),max(1,correct-1),correct+1]; r=i%4; opts[0],opts[r]=opts[r],opts[0]
        visual={"format":"matrix","cells":[[a,b,a+b],[a2,b2,a2+b2],[a3,b3,None]],"rule":"third = first + second","symbol":"dots"}
        added+=_add(conn,cats["fm"],f"QB-F-M-{i+1:03d}","figural","matrices","addition_rule",1+(i%5),45+(i%4)*5,f"בכל שורה, מספר הסימנים בתא השלישי שווה לסכום שני התאים הראשונים.\nשורה 1: {a}, {b}, {a+b}; שורה 2: {a2}, {b2}, {a2+b2}; שורה 3: {a3}, {b3}, ?\nכמה סימנים בתא החסר?",f"{a3}+{b3}={correct}, ולכן בתא החסר יש {correct} סימנים.",_answers([str(x) for x in opts],str(correct)),visual,["מטריצות","דפוסים"])
    faces=["A","B","C","D","E","F"]; opposite={"A":"D","D":"A","B":"E","E":"B","C":"F","F":"C"}
    for i in range(30):
        f=faces[i%6]
        if i%2==0:
            correct=opposite[f]; q=f"בקובייה הפאות הנגדיות הן A–D, B–E, C–F. איזו פאה מול {f}?"; opts=[correct]+[x for x in faces if x not in (f,correct)][:3]; visual={"format":"cube","opposite_pairs":[["A","D"],["B","E"],["C","F"]],"highlight":f}
        else:
            other=faces[(i*2+1)%6]; correct="כן" if other not in (f,opposite[f]) else "לא"; q=f"בקובייה הפאות הנגדיות הן A–D, B–E, C–F. האם {f} ו־{other} יכולות להיות סמוכות?"; opts=[correct,"לא" if correct=="כן" else "כן","רק לאחר סיבוב","לא ניתן לדעת"]; visual={"format":"cube","opposite_pairs":[["A","D"],["B","E"],["C","F"]],"highlight":[f,other]}
        r=i%4; opts[0],opts[r]=opts[r],opts[0]
        added+=_add(conn,cats["fc"],f"QB-F-C-{i+1:03d}","figural","cubes","cube_spatial",1+(i%5),50+(i%4)*5,q,"פאות נגדיות אינן סמוכות; כל פאה אחרת יכולה להיות סמוכה לפאה הנתונה.",_answers(opts,correct),visual,["קוביות","מרחבי"])
    symbols=["▲","■","●","◆","★"]
    for i in range(30):
        seq=[symbols[(i+j)%5] for j in range(4)]; correct=symbols[(i+4)%5]; opts=[correct,seq[0],seq[1],seq[2]]; r=(i+1)%4; opts[0],opts[r]=opts[r],opts[0]; visual={"format":"sequence","items":seq+[None],"rule":"advance one symbol in a five-symbol cycle"}
        added+=_add(conn,cats["fp"],f"QB-F-P-{i+1:03d}","figural","visual_patterns","cyclic_sequence",1+(i%5),40+(i%4)*5,f"מהו הסמל הבא בסדרה: {' → '.join(seq)} → ?",f"הסדרה מתקדמת מחזורית. אחרי {seq[-1]} מגיע {correct}.",_answers(opts,correct),visual,["דפוסים חזותיים","סדרות"])
    print({"migration":"question_bank_v7","attempted":240,"added":added})

def downgrade():
    conn=op.get_bind(); ids=conn.execute(sa.text("SELECT id FROM questions WHERE question_metadata ->> 'bank_key' LIKE 'QB-V-A-%' OR question_metadata ->> 'bank_key' LIKE 'QB-V-S-%' OR question_metadata ->> 'bank_key' LIKE 'QB-V-R-%' OR question_metadata ->> 'bank_key' LIKE 'QB-F-R-%' OR question_metadata ->> 'bank_key' LIKE 'QB-F-M-%' OR question_metadata ->> 'bank_key' LIKE 'QB-F-C-%' OR question_metadata ->> 'bank_key' LIKE 'QB-F-P-%'")).scalars().all()
    for qid in ids:
        conn.execute(sa.text("DELETE FROM question_versions WHERE question_id=:qid"),{"qid":qid}); conn.execute(sa.text("DELETE FROM answers WHERE question_id=:qid"),{"qid":qid}); conn.execute(sa.text("DELETE FROM questions WHERE id=:qid"),{"qid":qid})

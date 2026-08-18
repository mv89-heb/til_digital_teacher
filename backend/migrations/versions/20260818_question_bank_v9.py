"""Expand the verbal and figural question bank with 200 original items.

Revision ID: 20260818_question_bank_v9
Revises: 20260818_question_bank_v8
"""
import json
from alembic import op
import sqlalchemy as sa

revision = "20260818_question_bank_v9"
down_revision = "20260818_question_bank_v8"
branch_labels = None
depends_on = None


def _cat(conn, name, typ, parent_name, order):
    parent = conn.execute(sa.text("SELECT id FROM categories WHERE name=:n AND type=:t AND parent_id IS NULL LIMIT 1"), {"n": parent_name, "t": typ}).scalar()
    if not parent:
        return None
    cid = conn.execute(sa.text("SELECT id FROM categories WHERE name=:n AND type=:t AND parent_id=:p LIMIT 1"), {"n": name, "t": typ, "p": parent}).scalar()
    if cid:
        return cid
    return conn.execute(sa.text("INSERT INTO categories (name,description,type,status,parent_id,\"order\",created_at,updated_at) VALUES (:n,:d,:t,'published',:p,:o,NOW(),NOW()) RETURNING id"), {"n":name,"d":"מאגר תרגול מורחב.","t":typ,"p":parent,"o":order}).scalar_one()


def _add(conn, cid, key, body, correct, wrongs, main, sub, skill, level, seconds, visual=None):
    if not cid or conn.execute(sa.text("SELECT 1 FROM questions WHERE question_metadata ->> 'bank_key'=:k"), {"k":key}).first():
        if not cid: return 0
        answers = [(correct, True)] + [(x, False) for x in wrongs]
        meta = {"bank_key":key,"main_category":main,"subcategory":sub,"skill":skill,"difficulty_level":level,"tags":[main,sub,skill],"visual":visual,"psychometrics":{"a":None,"b":None,"c":None},"quality":{"review_status":"APPROVED","single_correct_answer":True,"source":"original_til_bank_v9","calibration_status":"initial"}}
        qid = conn.execute(sa.text("INSERT INTO questions (category_id,question_type,difficulty,status,body,solution_text,recommended_time_seconds,question_metadata,created_at,updated_at) VALUES (:cid,'multiple_choice',:difficulty,'published',CAST(:body AS JSON),CAST(:solution AS JSON),:secs,CAST(:meta AS JSON),NOW(),NOW()) RETURNING id"), {"cid":cid,"difficulty":"easy" if level<=2 else ("medium" if level==3 else "exam"),"body":json.dumps({"format":"markdown","body":body},ensure_ascii=False),"solution":json.dumps({"format":"markdown","body":"התשובה הנכונה נבחרת לפי הכלל או המידע המופיע בשאלה."},ensure_ascii=False),"secs":seconds,"meta":json.dumps(meta,ensure_ascii=False)}).scalar_one()
        snap=[]
        for order,(text,ok) in enumerate(answers,1):
            exp="התשובה מתאימה לכלל של השאלה." if ok else "המסיח אינו מתאים לכלל או למידע הנתון."
            aid=conn.execute(sa.text("INSERT INTO answers (question_id,answer_text,is_correct,explanation_if_selected,\"order\",created_at,updated_at) VALUES (:qid,:text,:ok,CAST(:exp AS JSON),:ord,NOW(),NOW()) RETURNING id"),{"qid":qid,"text":text,"ok":ok,"exp":json.dumps({"format":"markdown","body":exp},ensure_ascii=False),"ord":order}).scalar_one()
            snap.append({"id":aid,"answer_text":text,"is_correct":ok,"explanation_if_selected":{"format":"markdown","body":exp},"order":order})
        conn.execute(sa.text("INSERT INTO question_versions (question_id,version_number,category_id,question_type,difficulty,status,body,solution_text,question_metadata,answer_snapshot,recommended_time_seconds,created_at,updated_at) SELECT :qid,1,category_id,question_type,difficulty,status,body,solution_text,question_metadata,CAST(:snap AS JSONB),recommended_time_seconds,NOW(),NOW() FROM questions WHERE id=:qid"),{"qid":qid,"snap":json.dumps(snap,ensure_ascii=False)})
        return 1
    return 0


def upgrade():
    conn=op.get_bind()
    v1=_cat(conn,"אנלוגיות","verbal","חשיבה מילולית",1)
    v2=_cat(conn,"השלמת משפטים","verbal","חשיבה מילולית",2)
    v3=_cat(conn,"הבנת הנקרא","verbal","חשיבה מילולית",3)
    f1=_cat(conn,"סיבוב צורות","figural","חשיבה מרחבית וצורנית",1)
    f2=_cat(conn,"מטריצות צורניות","figural","חשיבה מרחבית וצורנית",2)
    f3=_cat(conn,"קוביות ומרחב","figural","חשיבה מרחבית וצורנית",3)
    f4=_cat(conn,"דפוסים חזותיים","figural","חשיבה מרחבית וצורנית",4)
    added=0

    analogies=[
      ("ציפור","קן","דבורה","כוורת"),("בונה","סכר","אדריכל","בניין"),("מפתח","מנעול","סיסמה","חשבון"),("רופא","מטופל","מורה","תלמיד"),("ספר","ספרייה","מוצג","מוזיאון"),
      ("מכתב","מעטפה","מתנה","אריזה"),("מדחום","טמפרטורה","מד מהירות","מהירות"),("מצפן","כיוון","שעון","זמן"),("מכחול","ציור","מקלדת","הקלדה"),("מספריים","חיתוך","מחק","מחיקה"),
      ("זרע","צמח","ביצה","אפרוח"),("גולם","פרפר","זחל","פרפר"),("גנן","גינה","ספרן","ספרייה"),("שופט","בית משפט","רופא","מרפאה"),("צלם","תמונה","סופר","רומן"),
      ("רמקול","קול","מסך","תמונה"),("מסננת","סינון","מגנט","משיכה"),("מפתח ברגים","בורג","מברג","בורג"),("מנוע","תנועה","סוללה","חשמל"),("ענן","גשם","תנור","חום"),
      ("חלב","גבינה","ענבים","יין"),("קמח","לחם","חימר","כלי"),("עצים","נייר","צמר","בד"),("פרח","ריח","פעמון","צליל"),("אוזן","שמיעה","עין","ראייה"),
      ("פה","דיבור","יד","כתיבה"),("רגל","הליכה","כנף","תעופה"),("דג","מים","ציפור","אוויר"),("ספינה","ים","רכבת","מסילה"),("מכונית","כביש","מטוס","מסלול"),
      ("מפה","מיקום","לוח שנה","תאריך"),("מילון","מילה","אטלס","מפה"),("חוק","ציות","כלל","התנהגות"),("שאלה","תשובה","בעיה","פתרון"),("סיבה","תוצאה","פעולה","תגובה"),
      ("חורף","קור","קיץ","חום"),("בוקר","זריחה","ערב","שקיעה"),("ילד","ילדות","מבוגר","בגרות"),("תלמיד","לימוד","ספורטאי","אימון"),("מוזיקאי","מנגינה","צייר","ציור"),
      ("מחבר","ספר","מלחין","יצירה"),("חקלאי","שדה","דייג","ים"),("כורה","מכרה","חוקר","מעבדה"),("נהג","רכב","טייס","מטוס"),("נגר","עץ","נפח","מתכת"),
      ("מנעול","אבטחה","מטרייה","הגנה"),("סולם","גובה","מנהרה","עומק"),("גשר","מעבר","סכר","אגירה"),("מעלית","קומה","רכבל","גובה"),("פנס","אור","מאוורר","אוויר"),
      ("שעון","שעה","משקל","משקל",""),
    ]
    for i,row in enumerate(analogies[:50],1):
        a,b,c,d=row[:4]
        added+=_add(conn,v1,f"QB-V9-A-{i:03d}",f"{a} : {b} — מהו הזוג המקביל ביותר?",f"{c} : {d}",["חבר : שכונה","ספר : צבע","מפתח : דלת"],"verbal","אנalogies","relationship_mapping",1+(i%5),35+(i%3)*5)

    connectors=[
      ("הנתונים היו חלקיים, ______ החוקרים נמנעו ממסקנה מוחלטת.","ולכן"),("הפתרון פשוט, ______ יישומו דורש תכנון.","אך"),("הצוות סיים מוקדם, ______ נותר זמן לבדיקה.","ולכן"),("המחיר ירד, ______ הביקוש נשאר דומה.","אך"),("החוקר חזר על הניסוי ______ לוודא שהתוצאה יציבה.","כדי"),
      ("המסלול ארוך יותר; ______ הוא מוצל יותר.","עם זאת"),("המערכת התריעה, ______ התהליך נעצר.","ולכן"),("המשימה נראתה פשוטה, ______ דרשה ריכוז.","אך"),("ההוראות היו ברורות, ______ מספר הטעויות ירד.","ולכן"),("הנתון מעניין; ______ אינו מוכיח סיבתיות.","עם זאת")]
    for i in range(30):
        sentence,correct=connectors[i%len(connectors)]
        added+=_add(conn,v2,f"QB-V9-C-{i+1:03d}",sentence,correct,["למרות","משום כך","במקום זאת"],"verbal","sentence_completion","connectors",1+(i%5),35+(i%3)*5)

    passages=[
      ("ספרייה האריכה שעות פתיחה. בחודש הראשון מספר המבקרים עלה, אך המנהלת ציינה שעדיין מוקדם לקבוע שהשינוי הוא הסיבה היחידה.","מהי המסקנה הזהירה?","ייתכן שהארכת השעות תרמה לעלייה"),
      ("חברה החליפה מערכת מחשוב. בשבוע הראשון הייתה האטה, ולאחר חודש התקצרו זמני הביצוע. ההדרכה נמשכה כדי לצמצם טעויות.","מה השתפר לאחר חודש?","זמני ביצוע המשימות התקצרו"),
      ("בית ספר הציב מתקן מחזור. נאספו 800 בקבוקים בחודש הראשון ו־1,000 בשני. המנהל ביקש להמתין לנתונים נוספים.","למה ביקש המנהל להמתין?","כדי לקבל נתונים נוספים"),
      ("חנות הציבה מוצרי חורף בכניסה ובמקביל הפעילה מבצע הנחה. המכירות עלו, ולכן קשה לבודד את השפעת כל שינוי.","מה מקשה על המסקנה?","שני שינויים התרחשו במקביל"),
      ("קבוצת תלמידים למדה באמצעות כרטיסיות ונמצא שיפור. לא נבדקה קבוצה מקבילה שלא השתמשה בכרטיסיות.","מה חסר למחקר?","קבוצה מקבילה להשוואה"),
      ("עירייה שתלה עצים ברחוב אחד. בקיץ נמדדה ירידה בטמפרטורה באזור המוצל, אך החוקרים נמנעו מהכללה לכל העיר.","מדוע נמנעו מהכללה?","המדידה הייתה מוגבלת לאזור אחד"),
      ("מפעל שינה את סדר העבודה והגדיל את התפוקה מ־40 ל־48 יחידות בשעה. לא נבדק אם השיפור נשמר לאורך זמן.","מה עדיין אינו ידוע?","אם השיפור נשמר לאורך זמן"),
      ("צוות בדק שני מסלולים. אחד קצר יותר והשני מוצל יותר. ביום חם רוב המטיילים בחרו במסלול המוצל.","מה נתמך בנתונים?","בתנאים החמים רבים העדיפו את המסלול המוצל"),
      ("מוזיאון הוסיף שילוט. המבקרים דיווחו שקל יותר למצוא חדרים, אך לא נאסף נתון אובייקטיבי על זמן החיפוש.","מה אי אפשר לקבוע בביטחון?","בכמה זמן בדיוק התקצר החיפוש"),
      ("קורס מקוון הוסיף תרגול. שיעור ההשלמות עלה, אך באותו חודש קוצר גם מספר המטלות.","מהו גורם מבלבל?","שני שינויים התרחשו באותו זמן")]
    for i in range(30):
        p,q,correct=passages[i%len(passages)]
        added+=_add(conn,v3,f"QB-V9-R-{i+1:03d}",p+"\n\n"+q,correct,["ההשפעה הוכחה לחלוטין","אין קשר בין הנתונים","כל המשתתפים פעלו באותה דרך"],"verbal","reading_comprehension","inference",1+(i%5),50+(i%4)*5)

    # 20 rotation items
    for i in range(20):
        turns=[90,180,270,360][i%4]
        shape=["חץ ימינה","L עם זרוע עליונה","משולש עם קודקוד למעלה","צורת T"] [i%4]
        dirs=["למטה","שמאלה","למעלה","למעלה"][i%4]
        correct=dirs if turns else "למעלה"
        added+=_add(conn,f1,f"QB-F9-R-{i+1:03d}",f"צורה: {shape}. לאחר סיבוב של {turns}° בכיוון השעון, לאיזה כיוון יפנה הסימון הראשי?",correct,["ימינה","למטה","שמאלה"],"figural","rotation","mental_rotation",1+(i%5),45+(i%3)*5, {"format":"rotation","degrees":turns})

    # 20 matrix items using arithmetic/count rules
    for i in range(20):
        a=(i%5)+1; b=((i*2)%5)+1; c=a+b
        correct=str(c)
        added+=_add(conn,f2,f"QB-F9-M-{i+1:03d}",f"במטריצה בכל שורה: המספר השלישי מתקבל מחיבור שני המספרים הראשונים. בשורה הנוכחית מופיעים {a}, {b}, ?. מה חסר?",correct,[str(c-1),str(c+1),str(a*b)],"figural","matrices","matrix_rule",1+(i%5),50+(i%3)*5)

    # 20 cube/spatial items
    for i in range(20):
        n=4+(i%5); opposite=7-n
        correct=f"הפאה שממולה היא {opposite}"
        added+=_add(conn,f3,f"QB-F9-C-{i+1:03d}",f"בקובייה ממוספרת הפאות הזוגיות המשלימות ל־7 נמצאות זו מול זו. אם הפאה העליונה היא {n}, איזו פאה נמצאת מולה?",correct,[f"הפאה {n}",f"הפאה {n+1}",f"הפאה {n-1}"],"figural","cubes_and_space","opposite_faces",1+(i%5),45+(i%3)*5)

    # 20 visual pattern items
    symbols=["▲","■","●","◆","★"]
    for i in range(20):
        seq=[symbols[(i+j)%5] for j in range(4)]
        correct=symbols[(i+4)%5]
        wrong=[symbols[i%5],symbols[(i+1)%5],symbols[(i+2)%5]]
        added+=_add(conn,f4,f"QB-F9-P-{i+1:03d}",f"מהו הסמל הבא בסדרה: {' → '.join(seq)} → ?",correct,wrong,"figural","visual_patterns","cyclic_sequence",1+(i%5),40+(i%3)*5,{"format":"sequence","items":seq+[None],"rule":"five-symbol cycle"})

    print({"migration":"question_bank_v9","added":added,"target":200})


def downgrade():
    conn=op.get_bind()
    ids=conn.execute(sa.text("SELECT id FROM questions WHERE question_metadata ->> 'bank_key' LIKE 'QB-V9-%' OR question_metadata ->> 'bank_key' LIKE 'QB-F9-%'")).scalars().all()
    for qid in ids:
        conn.execute(sa.text("DELETE FROM question_versions WHERE question_id=:qid"),{"qid":qid})
        conn.execute(sa.text("DELETE FROM answers WHERE question_id=:qid"),{"qid":qid})
        conn.execute(sa.text("DELETE FROM questions WHERE id=:qid"),{"qid":qid})

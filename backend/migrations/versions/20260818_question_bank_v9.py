"""Repair/expand the verbal+figural question bank with duplicate-safe items.
Revision ID: 20260818_question_bank_v9
Revises: 20260818_question_bank_v8
"""
import json
from alembic import op
import sqlalchemy as sa
revision="20260818_question_bank_v9"
down_revision="20260818_question_bank_v8"
branch_labels=None
depends_on=None

def _cat(conn,name,typ,parent_name,order):
    parent=conn.execute(sa.text("SELECT id FROM categories WHERE name=:n AND type=:t AND parent_id IS NULL LIMIT 1"),{"n":parent_name,"t":typ}).scalar()
    if not parent:return None
    cid=conn.execute(sa.text("SELECT id FROM categories WHERE name=:n AND type=:t AND parent_id=:p LIMIT 1"),{"n":name,"t":typ,"p":parent}).scalar()
    if cid:return cid
    return conn.execute(sa.text("INSERT INTO categories (name,description,type,status,parent_id,\"order\",created_at,updated_at) VALUES (:n,:d,:t,'published',:p,:o,NOW(),NOW()) RETURNING id"),{"n":name,"d":"מאגר תרגול מורחב.","t":typ,"p":parent,"o":order}).scalar_one()

def _add(conn,cid,key,body,correct,wrongs,main,sub,skill,level,seconds,visual=None):
    if not cid or conn.execute(sa.text("SELECT 1 FROM questions WHERE question_metadata ->> 'bank_key'=:k LIMIT 1"),{"k":key}).first():return 0
    options=[]
    for x in [correct]+list(wrongs):
        x=str(x)
        if x not in options:options.append(x)
    if len(options)!=4 or str(correct) not in options:return 0
    meta={"bank_key":key,"main_category":main,"subcategory":sub,"skill":skill,"difficulty_level":level,"tags":[main,sub,skill],"visual":visual,"psychometrics":{"a":None,"b":None,"c":None},"quality":{"review_status":"APPROVED","single_correct_answer":True,"source":"original_til_bank_v9","calibration_status":"initial"}}
    difficulty="easy" if level<=2 else ("medium" if level==3 else "exam")
    qid=conn.execute(sa.text("INSERT INTO questions (category_id,question_type,difficulty,status,body,solution_text,recommended_time_seconds,question_metadata,created_at,updated_at) VALUES (:cid,'multiple_choice',:difficulty,'published',CAST(:body AS JSON),CAST(:solution AS JSON),:secs,CAST(:meta AS JSON),NOW(),NOW()) RETURNING id"),{"cid":cid,"difficulty":difficulty,"body":json.dumps({"format":"markdown","body":body},ensure_ascii=False),"solution":json.dumps({"format":"markdown","body":"התשובה הנכונה נבחרת לפי הכלל, ההקשר או המידע הנתון."},ensure_ascii=False),"secs":seconds,"meta":json.dumps(meta,ensure_ascii=False)}).scalar_one()
    snap=[]
    for order,text in enumerate(options,1):
        ok=text==str(correct)
        exp="התשובה מתאימה לכלל של השאלה." if ok else "המסיח אינו מתאים לכלל או למידע הנתון."
        aid=conn.execute(sa.text("INSERT INTO answers (question_id,answer_text,is_correct,explanation_if_selected,\"order\",created_at,updated_at) VALUES (:qid,:text,:ok,CAST(:exp AS JSON),:ord,NOW(),NOW()) RETURNING id"),{"qid":qid,"text":text,"ok":ok,"exp":json.dumps({"format":"markdown","body":exp},ensure_ascii=False),"ord":order}).scalar_one()
        snap.append({"id":aid,"answer_text":text,"is_correct":ok,"explanation_if_selected":{"format":"markdown","body":exp},"order":order})
    conn.execute(sa.text("INSERT INTO question_versions (question_id,version_number,category_id,question_type,difficulty,status,body,solution_text,question_metadata,answer_snapshot,recommended_time_seconds,created_at,updated_at) SELECT :qid,1,category_id,question_type,difficulty,status,body,solution_text,question_metadata,CAST(:snap AS JSONB),recommended_time_seconds,NOW(),NOW() FROM questions WHERE id=:qid"),{"qid":qid,"snap":json.dumps(snap,ensure_ascii=False)})
    return 1

def upgrade():
    conn=op.get_bind()
    cats={k:_cat(conn,n,"verbal" if k[0]=="v" else "figural","חשיבה מילולית" if k[0]=="v" else "חשיבה מרחבית וצורנית",i) for i,(k,n) in enumerate([("va","אנלוגיות"),("vs","השלמת משפטים"),("vr","הבנת הנקרא"),("fr","סיבוב צורות"),("fm","מטריצות צורניות"),("fc","קוביות ומרחב"),("fp","דפוסים חזותיים")],1)}
    added=0
    analogy=[("ציפור","קן","דבורה","כוורת"),("בונה","סכר","אדריכל","בניין"),("מפתח","מנעול","סיסמה","חשבון"),("רופא","מטופל","מורה","תלמיד"),("ספר","ספרייה","מוצג","מוזיאון"),("מכתב","מעטפה","מתנה","אריזה"),("מדחום","טמפרטורה","מד מהירות","מהירות"),("מצפן","כיוון","שעון","זמן"),("מכחול","ציור","מקלדת","הקלדה"),("מספריים","חיתוך","מחק","מחיקה"),("זרע","צמח","ביצה","אפרוח"),("גנן","גינה","ספרן","ספרייה"),("שופט","בית משפט","רופא","מרפאה"),("צלם","תמונה","סופר","רומן"),("רמקול","קול","מסך","תמונה"),("מנוע","תנועה","סוללה","חשמל"),("חלב","גבינה","ענבים","יין"),("קמח","לחם","חימר","כלי"),("פרח","ריח","פעמון","צליל"),("אוזן","שמיעה","עין","ראייה"),("פה","דיבור","יד","כתיבה"),("רגל","הליכה","כנף","תעופה"),("דג","מים","ציפור","אוויר"),("ספינה","ים","רכבת","מסילה"),("מכונית","כביש","מטוס","מסלול")]
    for i,(a,b,c,d) in enumerate(analogy,1):
        wrong=[f"{analogy[(i+j)%len(analogy)][0]} : {analogy[(i+j)%len(analogy)][1]}" for j in (1,2,3)]
        added+=_add(conn,cats["va"],f"QB-V9-A-{i:03d}",f"{a} : {b} — איזה זוג מציג קשר דומה ביותר?",f"{c} : {d}",wrong,"verbal","analogies","relationship_mapping",1+(i%5),35+(i%3)*5)
    connectors=[("הנתונים היו חלקיים, ______ החוקרים נמנעו ממסקנה מוחלטת.","ולכן"),("הפתרון פשוט, ______ יישומו דורש תכנון.","אך"),("הצוות סיים מוקדם, ______ נותר זמן לבדיקה.","ולכן"),("המחיר ירד, ______ הביקוש נשאר דומה.","אך"),("החוקר חזר על הניסוי ______ לוודא שהתוצאה יציבה.","כדי"),("המסלול ארוך יותר; ______ הוא מוצל יותר.","עם זאת"),("המערכת התריעה, ______ התהליך נעצר.","ולכן"),("המשימה נראתה פשוטה, ______ דרשה ריכוז.","אך"),("ההוראות היו ברורות, ______ מספר הטעויות ירד.","ולכן"),("הנתון מעניין; ______ אינו מוכיח סיבתיות.","עם זאת")]
    for i in range(50):
        stem,correct=connectors[i%10]
        added+=_add(conn,cats["vs"],f"QB-V9-S-{i+1:03d}",stem,correct,["למרות","משום כך","במקום זאת"],"verbal","sentence_completion","logical_connectors",1+(i%5),35+(i%3)*5)
    for i in range(50):
        passage=f"מרכז למידה בדק שיטת תרגול חדשה. קבוצה אחת השתמשה בתרגול יומי במשך {7+i%8} ימים, ובסוף התקבל שיפור במדד הביצוע. החוקרים ציינו שההשוואה מוגבלת משום שהמשתתפים למדו בקצב שונה."
        q=[("מה נבדק במחקר?","שיטת תרגול חדשה"),("מה נמדד בסוף התקופה?","מדד הביצוע"),("מה הייתה מגבלת ההשוואה?","המשתתפים למדו בקצב שונה")][i%3]
        added+=_add(conn,cats["vr"],f"QB-V9-R-{i+1:03d}",passage+"\n\nשאלה: "+q[0],q[1],["לא נבדק דבר","המערכת נסגרה","כל המשתתפים קיבלו אותו קצב"],"verbal","reading_comprehension","reading_inference",1+(i%5),55)
    dirs=["למעלה","ימינה","למטה","שמאלה"]
    for i in range(25):
        start=i%4; angle=(i%4+1)*90; correct=dirs[(start+angle//90)%4]
        added+=_add(conn,cats["fr"],f"QB-F9-R-{i+1:03d}",f"חץ מצביע {dirs[start]}. הוא מסתובב {angle}° עם כיוון השעון. לאיזה כיוון יצביע?",correct,[d for d in dirs if d!=correct],"figural","rotations","rotation_2d",1+(i%5),35+(i%4)*5,{"format":"direction_arrow","initial_direction":dirs[start],"rotation_degrees":angle,"clockwise":True})
    for i in range(25):
        a=1+i%5;b=1+(i*2)%5;c=1+(i*3)%5;correct=a+b+c
        added+=_add(conn,cats["fm"],f"QB-F9-M-{i+1:03d}",f"בכל שורה המספר בתא הרביעי שווה לסכום שלושת התאים הראשונים. בשורה האחרונה: {a}, {b}, {c}, ?",str(correct),[str(correct-3),str(correct+1),str(correct+3)],"figural","matrices","addition_rule",1+(i%5),45,{"format":"matrix","cells":[[1,2,3,6],[2,1,2,5],[a,b,c,None]],"rule":"fourth=sum(first,second,third)"})
    faces=["A","B","C","D","E","F"]; opposite={"A":"D","D":"A","B":"E","E":"B","C":"F","F":"C"}
    for i in range(25):
        f=faces[i%6];correct=opposite[f]
        added+=_add(conn,cats["fc"],f"QB-F9-C-{i+1:03d}",f"בקובייה הפאות הנגדיות הן A–D, B–E, C–F. איזו פאה מול {f}?",correct,[x for x in faces if x not in (f,correct)][:3],"figural","cubes","cube_spatial",1+(i%5),50,{"format":"cube","opposite_pairs":[["A","D"],["B","E"],["C","F"]],"highlight":f})
    symbols=["▲","■","●","◆","★"]
    for i in range(25):
        seq=[symbols[(i+j)%5] for j in range(4)];correct=symbols[(i+4)%5]
        added+=_add(conn,cats["fp"],f"QB-F9-P-{i+1:03d}","מהו הסמל הבא בסדרה: "+" → ".join(seq)+" → ?",correct,[s for s in symbols if s!=correct][:3],"figural","visual_patterns","cyclic_sequence",1+(i%5),40,{"format":"sequence","items":seq+[None],"rule":"five-symbol cycle"})
    print({"migration":"question_bank_v9","attempted":200,"added":added})

def downgrade():
    conn=op.get_bind();ids=conn.execute(sa.text("SELECT id FROM questions WHERE question_metadata ->> 'bank_key' LIKE 'QB-V9-%' OR question_metadata ->> 'bank_key' LIKE 'QB-F9-%'")).scalars().all()
    for qid in ids:
        conn.execute(sa.text("DELETE FROM question_versions WHERE question_id=:qid"),{"qid":qid});conn.execute(sa.text("DELETE FROM answers WHERE question_id=:qid"),{"qid":qid});conn.execute(sa.text("DELETE FROM questions WHERE id=:qid"),{"qid":qid})

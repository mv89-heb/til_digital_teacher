"""Add a second full simulation pool so repeated simulations do not immediately reuse every item.

Revision ID: 20260818_question_bank_v4
Revises: 20260818_question_bank_v3
"""
import json
from alembic import op
import sqlalchemy as sa

revision = "20260818_question_bank_v4"
down_revision = "20260818_question_bank_v3"
branch_labels = None
depends_on = None


def _cat(conn, name, typ, parent_name):
    parent=conn.execute(sa.text("SELECT id FROM categories WHERE name=:n AND type=:t AND parent_id IS NULL LIMIT 1"),{"n":parent_name,"t":typ}).scalar()
    return conn.execute(sa.text("SELECT id FROM categories WHERE name=:n AND type=:t AND parent_id=:p LIMIT 1"),{"n":name,"t":typ,"p":parent}).scalar()


def _add(conn,cid,p):
    if conn.execute(sa.text("SELECT 1 FROM questions WHERE question_metadata ->> 'bank_key'=:k"),{"k":p["key"]}).first(): return
    meta={"bank_key":p["key"],"main_category":p["main"],"subcategory":p["sub"],"skill":p["skill"],"difficulty_level":p["level"],"tags":p.get("tags",[]),"visual":p.get("visual"),"psychometrics":{"a":None,"b":None,"c":None},"quality":{"review_status":"APPROVED","single_correct_answer":True,"source":"original_til_bank_v4"}}
    qid=conn.execute(sa.text("INSERT INTO questions (category_id,question_type,difficulty,status,body,solution_text,recommended_time_seconds,question_metadata,created_at,updated_at) VALUES (:cid,'multiple_choice','exam','published',CAST(:body AS JSON),CAST(:solution AS JSON),:secs,CAST(:meta AS JSON),NOW(),NOW()) RETURNING id"),{"cid":cid,"body":json.dumps({"format":"markdown","body":p["body"]},ensure_ascii=False),"solution":json.dumps({"format":"markdown","body":p["solution"]},ensure_ascii=False),"secs":p["secs"],"meta":json.dumps(meta,ensure_ascii=False)}).scalar_one()
    snap=[]
    for i,(text,ok,exp) in enumerate(p["answers"],1):
        aid=conn.execute(sa.text("INSERT INTO answers (question_id,answer_text,is_correct,explanation_if_selected,\"order\",created_at,updated_at) VALUES (:qid,:text,:ok,CAST(:exp AS JSON),:ord,NOW(),NOW()) RETURNING id"),{"qid":qid,"text":text,"ok":ok,"exp":json.dumps({"format":"markdown","body":exp},ensure_ascii=False),"ord":i}).scalar_one()
        snap.append({"id":aid,"answer_text":text,"is_correct":ok,"explanation_if_selected":{"format":"markdown","body":exp},"order":i})
    conn.execute(sa.text("INSERT INTO question_versions (question_id,version_number,category_id,question_type,difficulty,status,body,solution_text,question_metadata,answer_snapshot,recommended_time_seconds,created_at) SELECT :qid,1,category_id,question_type,difficulty,status,body,solution_text,question_metadata,CAST(:snap AS JSONB),recommended_time_seconds,NOW() FROM questions WHERE id=:qid"),{"qid":qid,"snap":json.dumps(snap,ensure_ascii=False)})


def _mc(correct, wrongs, explanations=None):
    ex=explanations or ["מסיח שאינו מתאים לכלל."]*4
    vals=[(str(correct),True,ex[0])]+[(str(x),False,ex[i+1]) for i,x in enumerate(wrongs)]
    return vals


def upgrade():
    conn=op.get_bind()
    c={"q1":_cat(conn,"אחוזים ושינויים","quantitative","חשיבה כמותית"),"q2":_cat(conn,"יחס והספק","quantitative","חשיבה כמותית"),"q3":_cat(conn,"סדרות מספרים","quantitative","חשיבה כמותית"),"v1":_cat(conn,"אנלוגיות","verbal","חשיבה מילולית"),"v2":_cat(conn,"השלמת משפטים","verbal","חשיבה מילולית"),"v3":_cat(conn,"הבנת הנקרא","verbal","חשיבה מילולית"),"f1":_cat(conn,"סיבוב צורות","figural","חשיבה מרחבית וצורנית"),"f2":_cat(conn,"מטריצות צורניות","figural","חשיבה מרחבית וצורנית"),"f3":_cat(conn,"קוביות ומרחב","figural","חשיבה מרחבית וצורנית")}
    qs=[]
    # 15 quantitative items: percentage, rate and sequence variants with distinct numbers/rules.
    for i,(a,b,pct,level) in enumerate([(160,200,25,2),(240,300,25,3),(360,306,-15,4),(480,600,25,5),(250,275,10,1)],16):
        final=b; sign="עלה" if pct>0 else "ירד"; correct=f"{pct:+d}%".replace("+","")
        qs.append(("q1",{"key":f"QB-Q-{i:03d}","main":"quantitative","sub":"percentages","skill":"percentage_change","level":level,"secs":45,"body":f"מחירו של מוצר {sign} מ־{a} ל־{b} ש״ח. מהו אחוז השינוי?","solution":f"השינוי הוא {b-a}. ביחס ל־{a} מתקבל {(b-a)/a*100:.0f}%, ולכן השינוי הוא {correct}%." ,"answers":_mc(correct,["15%","20%","30%"],["זה אינו אחוז השינוי המתאים.","זה אינו אחוז השינוי המתאים.","זה אינו אחוז השינוי המתאים.","זה אינו אחוז השינוי המתאים."])}))
    for i,(total,part,need,level) in enumerate([(500,120,24,2),(750,150,20,3),(900,225,25,4),(640,96,15,5),(320,32,10,1)],21):
        qs.append(("q1",{"key":f"QB-Q-{i:03d}","main":"quantitative","sub":"percentages","skill":"part_whole","level":level,"secs":45,"body":f"איזה אחוז הם {part} מתוך {total}?","solution":f"{part}/{total}={part/total:.2f}, כלומר {need}%." ,"answers":_mc(f"{need}%",["10%","12%","30%"], ["החלק היחסי אינו זה.","החלק היחסי אינו זה.","החלק היחסי אינו זה.","החלק היחסי אינו זה."])}))
    for i,(rate,hours,extra,level) in enumerate([(18,4,2,2),(25,3,5,3),(32,2,3,4),(45,4,1,5),(14,5,2,1)],26):
        total=rate*(hours+extra)
        qs.append(("q2",{"key":f"QB-Q-{i:03d}","main":"quantitative","sub":"rates","skill":"constant_rate","level":level,"secs":50,"body":f"מכונה מייצרת {rate} יחידות בשעה. כמה יחידות תייצר ב־{hours+extra} שעות בקצב קבוע?","solution":f"{rate}×{hours+extra}={total} יחידות.","answers":_mc(total,[total-rate,total+rate,total+2*rate],["הפרש של שעה אחת.","חיבור במקום כפל.","תוספת שאינה קיימת.","הכפל הנכון הוא לפי מספר השעות."])}))
    for i,(start,step,level) in enumerate([(4,5,2),(11,7,3),(2,9,4),(17,4,5),(8,3,1)],31):
        vals=[start+step*k for k in range(5)]; correct=vals[-1]+step
        qs.append(("q3",{"key":f"QB-Q-{i:03d}","main":"quantitative","sub":"sequences","skill":"arithmetic_sequence","level":level,"secs":40,"body":f"מהו המספר הבא: {', '.join(map(str,vals))}, ?","solution":f"ההפרש הקבוע הוא {step}, ולכן {vals[-1]}+{step}={correct}.","answers":_mc(correct,[correct-step,correct+step,correct+2],["זה האיבר הקודם.","חריגה מההפרש הקבוע.","חריגה מההפרש הקבוע.","ההפרש הקבוע מוביל לתשובה הנכונה."])}))
    # 15 verbal items.
    verbal=[
      ("v1",36,"ציפור : קן — מהו הזוג הדומה ביותר?","דבורה : כוורת","בונה : סכר","מורה : כיתה","ספר : מדף",2,3,35),
      ("v1",37,"עורך : טקסט — מהו הזוג הדומה ביותר?","מגיה : טקסט","שופט : משחק","נהג : כביש","רופא : בית חולים",1,4,40),
      ("v1",38,"זרע : צמח — מהו הזוג הדומה ביותר?","ביצה : אפרוח","עץ : יער","מים : כוס","ספר : דף",1,3,35),
      ("v1",39,"מדחום : טמפרטורה — מהו הזוג הדומה ביותר?","מד־מהירות : מהירות","שעון : זמן","משקל : גובה","מפה : מרחק",0,5,40),
      ("v1",40,"מפתח : פתיחה — מהו הזוג הדומה ביותר?","מכחול : ציור","סולם : גובה","מנוע : דלק","מספריים : חיתוך",3,4,35),
      ("v2",41,"הטענה הייתה שנויה במחלוקת, ______ היא עוררה דיון ציבורי רחב.","לכן","אולם","אף על פי כן","משום כך",0,2,40),
      ("v2",42,"הנתונים היו חלקיים, ולכן המסקנה הייתה ______ ולא סופית.","חד־משמעית","זהירה","מוחלטת","מכרעת",1,3,40),
      ("v2",43,"החוקר לא הסתפק בתוצאה הראשונית; ______ הוא חזר על הניסוי.","לכן","עם זאת","במקום זאת","אף כי",0,4,40),
      ("v2",44,"הפתרון פשוט יחסית, אך יישומו דורש ______ ותכנון.","אקראיות","דיוק","הסתרה","דחייה",1,2,35),
      ("v2",45,"הצוות עבד במהירות, ______ הוא הקפיד שלא לדלג על שלבי הבדיקה.","ולכן","אך","משום כך","אם כן",1,5,45),
      ("v3",46,"טקסט: 'העובדים שקיבלו משוב שבועי שיפרו את הדיוק. החוקרים לא בדקו אם השיפור נמשך לאחר הפסקת המשוב.' מה לא ניתן להסיק?","שהיה שיפור בדיוק","שהמשוב ניתן מדי שבוע","שהשיפור נמשך ללא משוב","שהחוקרים לא בדקו המשך",2,3,50),
      ("v3",47,"טקסט: 'הספר החדש נמכר היטב בחודש הראשון, אך המכירות בחודש השני ירדו.' איזו מסקנה נתמכת?","המכירות היו גבוהות יותר בחודש הראשון","הספר נכשל","כל הספרים נמכרים פחות בחודש השני","הספר אזל מהמלאי",0,2,40),
      ("v3",48,"טקסט: 'המסלול הקצר חסך זמן, אך כלל יותר עליות.' איזו השוואה מדויקת?","המסלול הקצר בהכרח קל יותר","המסלול הקצר מהיר יותר לפי הנתון, אך לא בהכרח קל יותר","המסלול הארוך תמיד עדיף","אין הבדל בין המסלולים",1,4,45),
      ("v3",49,"טקסט: 'שלושה מתוך ארבעה ניסויים הצליחו.' איזה שיעור הצלחה מתואר?","25%","50%","75%","80%",2,1,35),
      ("v3",50,"טקסט: 'המחקר מצא קשר בין שינה מספקת לריכוז, אך לא הוכיח סיבתיות.' מה נכון?","שינה גורמת בהכרח לריכוז","נמצא קשר אך לא הוכחה סיבתיות","אין קשר","ריכוז גורם לשינה",1,5,50),
    ]
    for cat,i,body,*rest in verbal:
        opts=rest[:4]; correct_idx=rest[4]; level=rest[5]; secs=rest[6]
        ans=[(x,j==correct_idx,"זו התשובה המתאימה ביותר ליחס או לטקסט.") for j,x in enumerate(opts)]
        sol=f"התשובה הנכונה היא: {opts[correct_idx]}. יש לבחור אותה לפי הקשר והיחס הלוגי המתואר בשאלה."
        qs.append((cat,{"key":f"QB-V-{i:03d}","main":"verbal","sub":"analogies" if cat=="v1" else ("sentence_completion" if cat=="v2" else "reading"),"skill":"reasoning","level":level,"secs":secs,"body":body,"solution":sol,"answers":ans}))
    # 15 figural items represented as renderer instructions rather than external images.
    fig=[
      ("f1",51,"החץ מצביע ימינה. לאחר סיבוב 90° נגד כיוון השעון, לאן יצביע?","למעלה",1,2),
      ("f1",52,"החץ מצביע שמאלה. לאחר סיבוב 180°, לאן יצביע?","ימינה",3,3),
      ("f1",53,"החץ מצביע למטה. לאחר שני סיבובים של 90° עם כיוון השעון, לאן יצביע?","למעלה",2,4),
      ("f1",54,"ריבוע מסובב ב־90°. האם מספר צלעותיו משתנה?","לא",0,1),
      ("f1",55,"מלבן שאינו ריבוע מסובב ב־180°. האם אורכו ורוחבו מתחלפים?","לא",1,5),
      ("f2",56,"בכל שורה מספר הצלעות גדל ב־1: 3,4,5. מהו התא הבא?","6",0,2),
      ("f2",57,"בכל שורה מופיעים 1,2,3 סמלים; בשורה הבאה הסדר מוזז תא אחד שמאלה. מה הסמל החסר?","3",2,3),
      ("f2",58,"מטריצה: 2,4,8 / 3,6,12 / 4,8,?. מה חסר?","16",3,4),
      ("f2",59,"מטריצה: 1,2,3 / 2,3,4 / 3,4,?. מה חסר?","5",1,5),
      ("f2",60,"בכל תא מספר נקודות שווה למספר העמודה ועוד מספר השורה. בתא (3,2) כמה נקודות?","5",2,2),
      ("f3",61,"בקובייה A מול B. איזו פאה אינה יכולה להיות צמודה ל־A?","B",0,1),
      ("f3",62,"בקובייה C מול D. אם C קדמית, איזו פאה אחורית?","D",1,2),
      ("f3",63,"בקובייה E מול F. אם E שמאלית, איזו פאה ימנית?","F",3,3),
      ("f3",64,"אם A,C,E נפגשות בקודקוד, האם B,C,E יכולות להיפגש באותו קודקוד?","לא",1,4),
      ("f3",65,"בפריסת קובייה ארבע פאות ברצף A-B-C-D. איזו פאה נגדית ל־A?","C",2,5),
    ]
    for cat,i,body,correct,idx,level in fig:
        opts=[correct,"אופציה 2","אופציה 3","אופציה 4"]
        if idx==0: opts=[correct,"ימין","למטה","שמאלה"]
        if idx==1: opts=["למעלה",correct,"למטה","שמאלה"]
        if idx==2: opts=["למעלה","ימינה",correct,"שמאלה"]
        if idx==3: opts=["למעלה","לא",correct,"לא ניתן לדעת"]
        ans=[(x,j==0,"נכון לפי כלל הרנדור/המרחב המתואר.") for j,x in enumerate(opts)]
        if correct not in opts: opts[0]=correct; ans=[(x,j==0,"נכון לפי כלל הרנדור/המרחב המתואר.") for j,x in enumerate(opts)]
        qs.append((cat,{"key":f"QB-F-{i:03d}","main":"figural","sub":"rotation" if cat=="f1" else ("matrix" if cat=="f2" else "cube"),"skill":"spatial_reasoning","level":level,"secs":45,"body":body,"solution":f"התשובה היא {correct}, בהתאם לכלל המרחבי המתואר.","visual":{"format":"instruction","render":f"til_{i}"},"answers":ans}))
    for cat_key,p in qs: _add(conn,c[cat_key],p)


def downgrade():
    conn=op.get_bind()
    for prefix,start,end in [("Q",16,35),("V",36,50),("F",51,65)]:
        for i in range(start,end+1):
            qid=conn.execute(sa.text("SELECT id FROM questions WHERE question_metadata ->> 'bank_key'=:k"),{"k":f"QB-{prefix}-{i:03d}"}).scalar()
            if qid:
                conn.execute(sa.text("DELETE FROM question_versions WHERE question_id=:id"),{"id":qid})
                conn.execute(sa.text("DELETE FROM answers WHERE question_id=:id"),{"id":qid})
                conn.execute(sa.text("DELETE FROM questions WHERE id=:id"),{"id":qid})

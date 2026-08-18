"""Populate the Learning Center with a large structured TIL curriculum.
Revision ID: 20260818_learning_center_v10
Revises: 20260818_question_bank_v9
"""
import json
from alembic import op
import sqlalchemy as sa

revision="20260818_learning_center_v10"
down_revision="20260818_question_bank_v9"
branch_labels=None
depends_on=None

LESSONS={
"quantitative":[
("אחוזים – בסיס","לחשב אחוז מתוך מספר, מספר מתוך שלם ושינוי באחוזים"),("אחוזים – שינוי כפול","להבין עלייה וירידה רצופות ולמנוע חיבור אחוזים שגוי"),("יחסים ופרופורציות","לפתור יחסים, קנה מידה וחלוקה יחסית"),("שברים ועשרוניים","להשוות, לחבר ולהמיר שברים, עשרוניים ואחוזים"),("ממוצעים","לחשב ממוצע ולהסיק את הסכום או האיבר החסר"),("סדרות מספרים","לזהות הפרשים, יחסים, ריבועים ודפוסים מתחלפים"),("בעיות דרך–זמן–מהירות","לקשר בין דרך, זמן ומהירות ולבודד משתנה"),("הספק ועבודה","לשלב קצבי עבודה ולחשב זמן לביצוע משימה"),("בעיות גילאים","לבנות משוואות פשוטות לבעיות גיל בהווה ובעבר"),("בעיות קנייה ומכירה","לחשב מחיר, הנחה, רווח והפסד"),("תרשימים וטבלאות","לקרוא נתונים ולהשוות ביניהם במהירות"),("חשיבה כמותית מעורבת","לבחור את הכלי המתמטי המתאים תחת מגבלת זמן")],
"verbal":[
("אנלוגיות – סוגי קשרים","לזהות קשר של כלי–פעולה, מקום–תוכן, חלק–שלם וסיבה–תוצאה"),("אנלוגיות – קשר תפקודי","להשוות זוגות לפי התפקיד והפעולה ולא לפי אסוציאציה שטחית"),("אנלוגיות – חומר ותוצר","לזהות חומר שממנו נוצר תוצר ולבדוק כיוון קשר"),("השלמת משפטים – ניגוד","לזהות מילות קישור שמבטאות הסתייגות וניגוד"),("השלמת משפטים – סיבה ותוצאה","להבחין בין סיבה, תוצאה ומסקנה"),("השלמת משפטים – תנאי","לזהות מבני תנאי והשלכותיהם"),("הבנת הנקרא – עובדה","לאתר מידע מפורש בלי להוסיף הנחות"),("הבנת הנקרא – מסקנה","להסיק מסקנה שנתמכת ישירות בכמה משפטים"),("הבנת הנקרא – מטרת הכותב","לזהות את המטרה המרכזית של הקטע"),("הבנת הנקרא – טענה וראיה","להפריד בין טענה, דוגמה וראיה"),("הבנת הנקרא – השוואה","להשוות בין שני רעיונות לפי קריטריון משותף"),("חשיבה מילולית מעורבת","לשלב אנלוגיות, השלמות וקריאה תחת זמן")],
"figural":[
("סיבובים – 90 ו־180 מעלות","לחשב כיוון חדש אחרי סיבוב ולשמור על נקודת הייחוס"),("סיבובים – סדרת תנועות","לבצע כמה סיבובים ברצף בלי לאבד את הכיוון"),("מטריצות – חיבור","לזהות חוק שבו תא נבנה מסכום תאים אחרים"),("מטריצות – חיסור","לזהות הפרש קבוע או משתנה בין תאים"),("מטריצות – דפוס דו־ממדי","לבדוק חוק לאורך שורות ועמודות במקביל"),("קוביות – פאות נגדיות","לזכור שפאות נגדיות אינן נפגשות"),("קוביות – פאות סמוכות","לנתח אילו פאות יכולות להופיע יחד"),("קוביות – סיבוב מרחבי","לעקוב אחר קובייה לאחר סיבוב במרחב"),("דפוסים – מחזוריות","לזהות רצף שחוזר במחזור קבוע"),("דפוסים – שינוי צורה","לעקוב אחר מספר צלעות, מילוי או כיוון"),("דפוסים – שני חוקים","לבדוק שני משתנים המשתנים במקביל"),("חשיבה מרחבית מעורבת","לשלב סיבוב, מטריצה, קובייה ודפוס")],
"logic":[
("סיווגים וקבוצות","למצוא את הפריט שאינו שייך לקבוצה לפי כלל חד"),("רצפים לוגיים","לזהות חוק ברצף סמלים או פעולות"),("תנאים והסקות","לתרגם תנאי למסקנה בלי להוסיף מידע"),("אם–אז","להבחין בין תנאי מספיק לתנאי הכרחי"),("סדר ישיבה","לפתור אילוצים של מיקום וסדר"),("לוחות אמת בסיסיים","לנתח צירופי תנאים פשוטים"),("בעיות התאמה","לשייך פריטים לאנשים או קטגוריות לפי רמזים"),("שלילה והיפוך","להבין מה נובע משלילת טענה"),("זיהוי חוק נסתר","לבדוק כמה אפשרויות לפני בחירת החוק"),("אסטרטגיית אלימינציה","לפסול תשובות שאינן יכולות להתאים"),("לוגיקה במבחן תיל","לנהל חיפוש קצר ומדויק תחת זמן"),("חשיבה לוגית מעורבת","לשלב תנאים, סדרים, סיווגים והסקות")]
}

CATS={
"quantitative":("חשיבה כמותית","quantitative","תרגול מספרים, אחוזים, יחסים, סדרות ובעיות מילוליות."),
"verbal":("חשיבה מילולית","verbal","אנלוגיות, השלמת משפטים והבנת הנקרא."),
"figural":("חשיבה מרחבית וצורנית","figural","סיבובים, מטריצות, קוביות וזיהוי דפוסים חזותיים."),
"logic":("חשיבה לוגית","logic","תנאים, סדרים, סיווגים והסקות לוגיות.")}

SECTIONS=[
("simple_explanation","הסבר פשוט"),("normal_explanation","הסבר מלא"),("solved_example","דוגמה פתורה"),("normal_method","שיטת פתרון"),("fast_method","שיטה מהירה"),("common_mistakes","טעויות נפוצות"),("guided_practice","תרגול מודרך"),("summary","סיכום")]

def _category(conn,key):
    name,typ,desc=CATS[key]
    cid=conn.execute(sa.text("SELECT id FROM categories WHERE name=:n AND type=:t AND parent_id IS NULL LIMIT 1"),{"n":name,"t":typ}).scalar()
    if cid:return cid
    return conn.execute(sa.text("INSERT INTO categories (name,description,type,status,\"order\",created_at,updated_at) VALUES (:n,:d,:t,'published',:o,NOW(),NOW()) RETURNING id"),{"n":name,"d":desc,"t":typ,"o":{"quantitative":1,"verbal":2,"figural":3,"logic":4}[key]}).scalar_one()

def _block(conn,lesson_id,section,order,body,meta):
    conn.execute(sa.text("INSERT INTO lesson_contents (lesson_id,section,block_type,\"order\",content,block_metadata,created_at,updated_at) VALUES (:lid,:section,'text',:ord,CAST(:content AS JSON),CAST(:meta AS JSON),NOW(),NOW())"),{"lid":lesson_id,"section":section,"ord":order,"content":json.dumps({"format":"markdown","body":body},ensure_ascii=False),"meta":json.dumps(meta,ensure_ascii=False)})

def upgrade():
    conn=op.get_bind();added=0;blocks=0
    for key,items in LESSONS.items():
        cid=_category(conn,key)
        for idx,(title,goal) in enumerate(items,1):
            slug=f"learning-v10-{key}-{idx:02d}"
            exists=conn.execute(sa.text("SELECT id FROM lessons WHERE slug=:s LIMIT 1"),{"s":slug}).scalar()
            if exists:continue
            level="beginner" if idx<=4 else ("intermediate" if idx<=8 else "advanced")
            lesson_id=conn.execute(sa.text("INSERT INTO lessons (category_id,title,slug,description,status,difficulty_level,estimated_duration,icon,\"order\",created_at,updated_at) VALUES (:cid,:title,:slug,:desc,'published',:level,:duration,:icon,:ord,NOW(),NOW()) RETURNING id"),{"cid":cid,"title":title,"slug":slug,"desc":f"{goal}. שיעור מובנה עם הסבר, דוגמה, שיטה מהירה, טעויות נפוצות ותרגול.","level":level,"duration":12+(idx%5)*3,"icon":"book-open","ord":idx}).scalar_one()
            examples={
                "quantitative":f"נושא השיעור: {title}. התחילו בהגדרת הנתונים, כתבו את הפעולה המתאימה ובדקו שהיחידות והסימנים עקביים.",
                "verbal":f"נושא השיעור: {title}. קראו את הקשר או המשפט במלואו, הגדירו את היחס המרכזי ורק אחר כך בדקו את המסיחים.",
                "figural":f"נושא השיעור: {title}. קבעו נקודת ייחוס, עקבו אחרי שינוי אחד בכל פעם ובדקו את החוק גם בשורה או בצעד נוסף.",
                "logic":f"נושא השיעור: {title}. רשמו את התנאים במילים קצרות, פסלו אפשרויות שסותרות תנאי, ורק אז בחרו מסקנה."
            }[key]
            texts=[
                f"## {title}\n\n**מטרת השיעור:** {goal}.\n\nזהו שיעור לימודי מלא במרכז הלמידה, נפרד ממאגר השאלות. המטרה היא להבין את השיטה לפני התרגול.",
                f"{goal}. במבחן תיל חשוב לא רק להגיע לתשובה אלא לזהות במהירות איזה כלל מתאים לבעיה. התחילו מהמידע הבטוח ביותר והימנעו מהנחות שאינן כתובות.",
                examples,
                "1. קראו את הנתונים.\n2. הגדירו את החוק או היחס.\n3. פתרו בצעד הקצר ביותר.\n4. בדקו את התוצאה מול הנתונים והתשובות.",
                "בתרגול מתוזמן, חפשו קודם את הסימן המזהה את סוג השאלה. אם יש דרך קצרה לפסול שלוש תשובות, השתמשו בה במקום לפתור חישוב ארוך.",
                "הטעויות הנפוצות הן בחירת חוק מוקדם מדי, התעלמות ממילה אחת בשאלה, חישוב בכיוון ההפוך או בדיקה חלקית של הדפוס. אם שתי תשובות נראות אפשריות, חזרו לנתון שמכריע ביניהן.",
                "תרגול מודרך: פתרו שלוש שאלות מאותו נושא. בשאלה הראשונה הסבירו לעצמכם את כל הצעדים; בשנייה נסו לקצר; בשלישית הפעילו רק את השיטה המהירה. לאחר מכן השוו דיוק וזמן.",
                f"### זכירה מהירה\n\n**{title}** → {goal}.\n\nהבינו את החוק, תרגלו ללא לחץ, ואז עברו לתרגול מתוזמן במאגר השאלות."
            ]
            for order,((section,_),body) in enumerate(zip(SECTIONS,texts),1):
                _block(conn,lesson_id,section,order,body,{"curriculum_version":"v10","domain":key,"lesson_index":idx,"tags":[key,title]});blocks+=1
            added+=1
    print({"migration":"learning_center_v10","lessons_added":added,"content_blocks_added":blocks})

def downgrade():
    conn=op.get_bind();ids=conn.execute(sa.text("SELECT id FROM lessons WHERE slug LIKE 'learning-v10-%'")).scalars().all()
    for lid in ids:
        conn.execute(sa.text("DELETE FROM lesson_contents WHERE lesson_id=:lid"),{"lid":lid})
        conn.execute(sa.text("DELETE FROM lessons WHERE id=:lid"),{"lid":lid})

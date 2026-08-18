"""Seed the first calibrated TIL question bank.

Revision ID: 20260818_question_bank_v1
Revises: 20260818_add_user_last_login_at
"""

import json

from alembic import op
import sqlalchemy as sa

revision = "20260818_question_bank_v1"
down_revision = "20260818_add_user_last_login_at"
branch_labels = None
depends_on = None


def _get_or_create_category(conn, name, category_type, parent_id=None, description=None, order=0):
    row = conn.execute(
        sa.text(
            "SELECT id FROM categories "
            "WHERE name = :name AND type = :type "
            "AND ((parent_id = :parent_id) OR (parent_id IS NULL AND :parent_id IS NULL)) "
            "LIMIT 1"
        ),
        {"name": name, "type": category_type, "parent_id": parent_id},
    ).first()
    if row:
        return row[0]

    return conn.execute(
        sa.text(
            "INSERT INTO categories "
            "(name, description, type, status, parent_id, \"order\", created_at, updated_at) "
            "VALUES (:name, :description, :type, 'published', :parent_id, :order, NOW(), NOW()) "
            "RETURNING id"
        ),
        {
            "name": name,
            "description": description,
            "type": category_type,
            "parent_id": parent_id,
            "order": order,
        },
    ).scalar_one()


def _insert_question(conn, category_id, payload):
    existing = conn.execute(
        sa.text(
            "SELECT id FROM questions "
            "WHERE question_metadata ->> 'bank_key' = :bank_key LIMIT 1"
        ),
        {"bank_key": payload["bank_key"]},
    ).first()
    if existing:
        return existing[0]

    question_id = conn.execute(
        sa.text(
            "INSERT INTO questions "
            "(category_id, question_type, difficulty, status, body, solution_text, "
            "recommended_time_seconds, question_metadata, created_at, updated_at) "
            "VALUES (:category_id, 'multiple_choice', :difficulty, 'published', "
            "CAST(:body AS JSON), CAST(:solution AS JSON), :time_seconds, "
            "CAST(:metadata AS JSON), NOW(), NOW()) RETURNING id"
        ),
        {
            "category_id": category_id,
            "difficulty": payload["difficulty"],
            "body": json.dumps({"format": "markdown", "body": payload["body"]}, ensure_ascii=False),
            "solution": json.dumps({"format": "markdown", "body": payload["solution"]}, ensure_ascii=False),
            "time_seconds": payload["time_seconds"],
            "metadata": json.dumps(
                {
                    "bank_key": payload["bank_key"],
                    "main_category": payload["main_category"],
                    "subcategory": payload["subcategory"],
                    "skill": payload["skill"],
                    "difficulty_level": payload["difficulty_level"],
                    "tags": payload["tags"],
                    "visual": payload.get("visual"),
                    "psychometrics": {"a": None, "b": None, "c": None},
                    "quality": {
                        "review_status": "APPROVED",
                        "single_correct_answer": True,
                        "source": "original_til_bank_v1",
                    },
                },
                ensure_ascii=False,
            ),
        },
    ).scalar_one()

    answer_snapshot = []
    for position, answer in enumerate(payload["answers"], start=1):
        answer_id = conn.execute(
            sa.text(
                "INSERT INTO answers "
                "(question_id, answer_text, is_correct, explanation_if_selected, \"order\", created_at, updated_at) "
                "VALUES (:question_id, :answer_text, :is_correct, CAST(:explanation AS JSON), :position, NOW(), NOW()) "
                "RETURNING id"
            ),
            {
                "question_id": question_id,
                "answer_text": answer["text"],
                "is_correct": answer["is_correct"],
                "explanation": json.dumps({"format": "markdown", "body": answer["explanation"]}, ensure_ascii=False),
                "position": position,
            },
        ).scalar_one()
        answer_snapshot.append(
            {
                "id": answer_id,
                "answer_text": answer["text"],
                "is_correct": answer["is_correct"],
                "explanation_if_selected": {"format": "markdown", "body": answer["explanation"]},
                "order": position,
            }
        )

    conn.execute(
        sa.text(
            "INSERT INTO question_versions "
            "(question_id, version_number, category_id, question_type, difficulty, status, body, "
            "solution_text, question_metadata, answer_snapshot, recommended_time_seconds, created_at) "
            "SELECT :question_id, 1, category_id, question_type, difficulty, status, body, solution_text, "
            "question_metadata, CAST(:answer_snapshot AS JSONB), recommended_time_seconds, NOW() "
            "FROM questions WHERE id = :question_id"
        ),
        {"question_id": question_id, "answer_snapshot": json.dumps(answer_snapshot, ensure_ascii=False)},
    )
    return question_id


def upgrade():
    conn = op.get_bind()

    main_quant = _get_or_create_category(conn, "חשיבה כמותית", "quantitative", description="חשיבה מספרית, חישובים והסקה כמותית.", order=1)
    main_verbal = _get_or_create_category(conn, "חשיבה מילולית", "verbal", description="אנלוגיות, השלמת משפטים והבנת הנקרא.", order=2)
    main_figural = _get_or_create_category(conn, "חשיבה מרחבית וצורנית", "figural", description="סיבובים, מטריצות, קוביות וזיהוי דפוסים חזותיים.", order=3)

    categories = {
        "quant_percent": _get_or_create_category(conn, "אחוזים ושינויים", "quantitative", main_quant, order=1),
        "quant_rate": _get_or_create_category(conn, "יחס והספק", "quantitative", main_quant, order=2),
        "quant_sequence": _get_or_create_category(conn, "סדרות מספרים", "quantitative", main_quant, order=3),
        "verbal_analogy": _get_or_create_category(conn, "אנלוגיות", "verbal", main_verbal, order=1),
        "verbal_sentence": _get_or_create_category(conn, "השלמת משפטים", "verbal", main_verbal, order=2),
        "verbal_reading": _get_or_create_category(conn, "הבנת הנקרא", "verbal", main_verbal, order=3),
        "fig_rotation": _get_or_create_category(conn, "סיבוב צורות", "figural", main_figural, order=1),
        "fig_matrix": _get_or_create_category(conn, "מטריצות צורניות", "figural", main_figural, order=2),
        "fig_cube": _get_or_create_category(conn, "קוביות ומרחב", "figural", main_figural, order=3),
    }

    questions = [
        ("quant_percent", {
            "bank_key": "QB-Q-001", "main_category": "quantitative", "subcategory": "percentages", "skill": "relative_change", "difficulty": "medium", "difficulty_level": 3, "time_seconds": 45,
            "body": "מחירו של מוצר עלה ב־25% ולאחר מכן ירד ב־20% מהמחיר החדש. מהו המחיר הסופי ביחס למחיר המקורי?",
            "solution": "נניח שהמחיר המקורי הוא 100. לאחר העלייה: 100×1.25=125. לאחר הירידה: 125×0.80=100. לכן המחיר הסופי שווה למחיר המקורי.",
            "answers": [
                {"text": "95%", "is_correct": False, "explanation": "הירידה מחושבת מתוך 125 ולא מתוך 100."},
                {"text": "100%", "is_correct": True, "explanation": "נכון: 100×1.25×0.8=100."},
                {"text": "105%", "is_correct": False, "explanation": "הכפל הכולל הוא 1."},
                {"text": "110%", "is_correct": False, "explanation": "המחיר אינו עולה נטו."}
            ], "tags": ["percentages", "multi_step", "trap"]
        }),
        ("quant_rate", {
            "bank_key": "QB-Q-002", "main_category": "quantitative", "subcategory": "rates", "skill": "combined_rate", "difficulty": "exam", "difficulty_level": 4, "time_seconds": 60,
            "body": "מכונה א' מייצרת 120 יחידות בשעה ומכונה ב' 80 יחידות בשעה. שתיהן פועלות שעתיים, ולאחר מכן א' מפסיקה וב' ממשיכה עוד 3 שעות. כמה יחידות יוצרו?",
            "solution": "בשעתיים הראשונות: (120+80)×2=400. בשלוש השעות הבאות: 80×3=240. סך הכול 640 יחידות.",
            "answers": [
                {"text": "480", "is_correct": False, "explanation": "זה מתעלם מהעבודה של מכונה ב' לאחר שא' הפסיקה."},
                {"text": "520", "is_correct": False, "explanation": "יש לחשב שני פרקי זמן."},
                {"text": "600", "is_correct": False, "explanation": "הסכום הנכון הוא 640."},
                {"text": "640", "is_correct": True, "explanation": "נכון: 400+240=640."}
            ], "tags": ["rates", "work", "multi_step"]
        }),
        ("quant_sequence", {
            "bank_key": "QB-Q-003", "main_category": "quantitative", "subcategory": "sequences", "skill": "difference_pattern", "difficulty": "exam", "difficulty_level": 4, "time_seconds": 40,
            "body": "מהו המספר הבא בסדרה: 2, 6, 12, 20, 30, ?",
            "solution": "ההפרשים הם 4, 6, 8, 10. ההפרש הבא הוא 12, ולכן 30+12=42.",
            "answers": [
                {"text": "36", "is_correct": False, "explanation": "ההפרשים אינם קבועים."},
                {"text": "40", "is_correct": False, "explanation": "ההפרש הבא הוא 12."},
                {"text": "42", "is_correct": True, "explanation": "נכון."},
                {"text": "44", "is_correct": False, "explanation": "44 היה מתקבל מהפרש 14."}
            ], "tags": ["sequences", "second_order"]
        }),
        ("verbal_analogy", {
            "bank_key": "QB-V-001", "main_category": "verbal", "subcategory": "analogies", "skill": "role_relation", "difficulty": "medium", "difficulty_level": 3, "time_seconds": 35,
            "body": "רופא : מטופל — מהו הזוג בעל היחס הדומה ביותר?",
            "solution": "רופא הוא בעל מקצוע שמעניק טיפול למטופל. באותו יחס, מורה מעניק הוראה לתלמיד.",
            "answers": [
                {"text": "מורה : תלמיד", "is_correct": True, "explanation": "זהו אותו יחס של נותן שירות/הכוונה למקבל."},
                {"text": "ספר : ספרייה", "is_correct": False, "explanation": "זהו יחס של פריט למקום."},
                {"text": "מכונית : כביש", "is_correct": False, "explanation": "זהו יחס של כלי לסביבה."},
                {"text": "סכין : מטבח", "is_correct": False, "explanation": "זהו יחס של כלי למקום שימוש."}
            ], "tags": ["analogy", "semantic_relation"]
        }),
        ("verbal_sentence", {
            "bank_key": "QB-V-002", "main_category": "verbal", "subcategory": "sentence_completion", "skill": "contrast_and_causality", "difficulty": "exam", "difficulty_level": 4, "time_seconds": 50,
            "body": "אף על פי שהחוקר ציפה שהתוצאות יאשרו את השערתו, הנתונים החדשים ______ אותה, ולכן נדרש ממנו ______ את המודל המקורי.",
            "solution": "הפתיח יוצר ניגוד לציפייה. לכן הנתונים הפריכו את ההשערה, ובעקבות זאת החוקר נדרש לעדכן את המודל.",
            "answers": [
                {"text": "חיזקו / לדחות", "is_correct": False, "explanation": "המשמעות אינה מתאימה למבנה הניגודי."},
                {"text": "הפריכו / לעדכן", "is_correct": True, "explanation": "נכון: הנתונים סתרו את ההשערה ולכן המודל עודכן."},
                {"text": "אישרו / להרחיב", "is_correct": False, "explanation": "אין כאן ניגוד לציפייה."},
                {"text": "הסבירו / להוכיח", "is_correct": False, "explanation": "הצירוף אינו מתאים ליחסים במשפט."}
            ], "tags": ["sentence_completion", "contrast"]
        }),
        ("verbal_reading", {
            "bank_key": "QB-V-003", "main_category": "verbal", "subcategory": "reading", "skill": "main_idea", "difficulty": "medium", "difficulty_level": 3, "time_seconds": 55,
            "body": "ארגונים רבים משתמשים במבחני מיון כדי להעריך מועמדים לפני קבלה לעבודה. מטרת המבחנים אינה בהכרח לזהות את המועמד בעל הידע הרב ביותר, אלא לבחון יכולות הרלוונטיות לתפקיד, כגון הסקת מסקנות, עבודה תחת מגבלת זמן וזיהוי דפוסים. מהי הטענה המרכזית?",
            "solution": "הקטע מדגיש שמבחני מיון נועדו להעריך יכולות שונות הרלוונטיות לביצוע בתפקיד, ולא רק כמות ידע.",
            "answers": [
                {"text": "ידע מקצועי אינו חשוב בקבלה לעבודה.", "is_correct": False, "explanation": "הקטע אינו טוען זאת."},
                {"text": "מבחני מיון מיועדים בעיקר לבחינת ידע כללי.", "is_correct": False, "explanation": "הקטע אומר ההפך."},
                {"text": "מבחני מיון יכולים להעריך יכולות שונות הרלוונטיות לעבודה.", "is_correct": True, "explanation": "זו הטענה המרכזית."},
                {"text": "מבחני מיון מתאימים רק לתפקידים הדורשים עבודה מהירה.", "is_correct": False, "explanation": "נזכרות גם הסקת מסקנות וזיהוי דפוסים."}
            ], "tags": ["reading", "main_idea"]
        }),
        ("fig_rotation", {
            "bank_key": "QB-F-001", "main_category": "figural", "subcategory": "rotation", "skill": "mental_rotation", "difficulty": "medium", "difficulty_level": 3, "time_seconds": 40,
            "body": "צורת L מורכבת משלושה ריבועים אנכיים ושני ריבועים בשורה העליונה. איזו אפשרות מתקבלת לאחר סיבוב של 90° בכיוון השעון?",
            "solution": "בסיבוב של 90° בכיוון השעון הזרוע האנכית הופכת לאופקית והזרוע האופקית פונה כלפי מטה. יש לשמור על היחסים בין הריבועים ולא לשקף את הצורה.",
            "visual": {"format": "svg_spec", "shape": "polyomino", "cells": [[0,0],[1,0],[0,1],[0,2]], "rotation_degrees": 0},
            "answers": [
                {"text": "צורה L מסובבת 90° עם כיוון השעון", "is_correct": True, "explanation": "נכון: מדובר בסיבוב ולא בשיקוף."},
                {"text": "הצורה המקורית ללא שינוי", "is_correct": False, "explanation": "לא בוצע סיבוב."},
                {"text": "צורה L מסובבת 180°", "is_correct": False, "explanation": "זהו סיבוב גדול יותר."},
                {"text": "שיקוף אופקי של הצורה", "is_correct": False, "explanation": "שיקוף אינו סיבוב."}
            ], "tags": ["rotation", "svg", "polyomino"]
        }),
        ("fig_matrix", {
            "bank_key": "QB-F-002", "main_category": "figural", "subcategory": "matrix", "skill": "pattern_completion", "difficulty": "exam", "difficulty_level": 4, "time_seconds": 60,
            "body": "במטריצה בכל שורה מספר הנקודות גדל ב־2. בשורה השלישית מופיעות 3 נקודות, 5 נקודות ואז סימן שאלה. כמה נקודות צריכות להופיע בתא האחרון?",
            "solution": "בשורה השלישית החוק הוא 3, 5, 7. לכן התא החסר מכיל 7 נקודות. יש לוודא שהחוק עקבי גם בשורות האחרות.",
            "visual": {"format": "matrix", "cells": [[1,3,5],[2,4,6],[3,5,null]], "rule": "+2 across each row"},
            "answers": [
                {"text": "5", "is_correct": False, "explanation": "5 הוא התא האמצעי בשורה השלישית."},
                {"text": "6", "is_correct": False, "explanation": "החוק הוא תוספת של 2."},
                {"text": "7", "is_correct": True, "explanation": "נכון: 3→5→7."},
                {"text": "8", "is_correct": False, "explanation": "המעבר האחרון צריך להיות +2."}
            ], "tags": ["matrix", "pattern", "visual"]
        }),
        ("fig_cube", {
            "bank_key": "QB-F-003", "main_category": "figural", "subcategory": "cube", "skill": "spatial_constraints", "difficulty": "exam", "difficulty_level": 5, "time_seconds": 70,
            "body": "בקובייה שלוש פאות סמוכות מסומנות בעיגול, במשולש ובריבוע. לאחר סיבוב שבו הפאה המסומנת בריבוע עוברת למעלה, איזה סימן יהיה בהכרח בפאה הקדמית?",
            "solution": "מהנתונים ידועות שלוש פאות סמוכות בלבד. בלי לדעת איזו מבין הפאות הנגדיות הייתה בכיוון הסיבוב, או את ציר הסיבוב המדויק, אין דרך לקבוע בוודאות את הפאה הקדמית. לכן התשובה היא שלא ניתן לקבוע.",
            "visual": {"format": "cube", "faces": {"top": "circle", "front": "triangle", "right": "square"}},
            "answers": [
                {"text": "עיגול", "is_correct": False, "explanation": "אין מספיק מידע כדי לקבוע זאת."},
                {"text": "משולש", "is_correct": False, "explanation": "ייתכן בתרחישים מסוימים אך אינו הכרחי."},
                {"text": "ריבוע", "is_correct": False, "explanation": "הריבוע עבר למעלה."},
                {"text": "לא ניתן לקבוע", "is_correct": True, "explanation": "נכון: חסר מידע על הכיוון/הפאות הנגדיות."}
            ], "tags": ["cube", "spatial", "insufficient_information"]
        })
    ]

    for category_key, payload in questions:
        _insert_question(conn, categories[category_key], payload)


def downgrade():
    conn = op.get_bind()
    keys = ["QB-Q-001", "QB-Q-002", "QB-Q-003", "QB-V-001", "QB-V-002", "QB-V-003", "QB-F-001", "QB-F-002", "QB-F-003"]
    for key in keys:
        conn.execute(sa.text("DELETE FROM questions WHERE question_metadata ->> 'bank_key' = :key"), {"key": key})

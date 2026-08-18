"""Complete the figural bank with the visual-pattern category and 30 items.

Revision ID: 20260818_question_bank_v8
Revises: 20260818_question_bank_v7
"""
import json
from alembic import op
import sqlalchemy as sa

revision = "20260818_question_bank_v8"
down_revision = "20260818_question_bank_v7"
branch_labels = None
depends_on = None


def _get_or_create_category(conn, name, typ, parent_name, order):
    parent = conn.execute(sa.text(
        "SELECT id FROM categories WHERE name=:n AND type=:t AND parent_id IS NULL LIMIT 1"
    ), {"n": parent_name, "t": typ}).scalar()
    if not parent:
        return None
    existing = conn.execute(sa.text(
        "SELECT id FROM categories WHERE name=:n AND type=:t AND parent_id=:p LIMIT 1"
    ), {"n": name, "t": typ, "p": parent}).scalar()
    if existing:
        return existing
    return conn.execute(sa.text(
        "INSERT INTO categories (name,description,type,status,parent_id,\"order\",created_at,updated_at) "
        "VALUES (:n,:d,:t,'published',:p,:o,NOW(),NOW()) RETURNING id"
    ), {"n": name, "d": "זיהוי סדרות ודפוסים חזותיים.", "t": typ, "p": parent, "o": order}).scalar_one()


def _add(conn, cid, i):
    key = f"QB-F-P-{i:03d}"
    if conn.execute(sa.text("SELECT 1 FROM questions WHERE question_metadata ->> 'bank_key'=:k"), {"k": key}).first():
        return 0
    symbols = ["▲", "■", "●", "◆", "★"]
    seq = [symbols[(i - 1 + j) % 5] for j in range(4)]
    correct = symbols[(i + 3) % 5]
    options = [correct, seq[0], seq[1], seq[2]]
    r = i % 4
    options[0], options[r] = options[r], options[0]
    answers = [(x, x == correct, "זהו הסמל הבא במחזור." if x == correct else "הסמל אינו הבא לפי הדפוס.") for x in options]
    level = 1 + (i % 5)
    visual = {"format": "sequence", "items": seq + [None], "rule": "advance one symbol in a five-symbol cycle"}
    meta = {"bank_key": key, "main_category": "figural", "subcategory": "visual_patterns", "skill": "cyclic_sequence", "difficulty_level": level, "tags": ["דפוסים חזותיים", "סדרות"], "visual": visual, "psychometrics": {"a": None, "b": None, "c": None}, "quality": {"review_status": "APPROVED", "single_correct_answer": True, "source": "original_til_bank_v8", "calibration_status": "initial"}}
    qid = conn.execute(sa.text("""INSERT INTO questions (category_id,question_type,difficulty,status,body,solution_text,recommended_time_seconds,question_metadata,created_at,updated_at)
        VALUES (:cid,'multiple_choice',:difficulty,'published',CAST(:body AS JSON),CAST(:solution AS JSON),:secs,CAST(:meta AS JSON),NOW(),NOW()) RETURNING id"""), {
        "cid": cid, "difficulty": "easy" if level <= 2 else ("medium" if level == 3 else "exam"),
        "body": json.dumps({"format": "markdown", "body": f"מהו הסמל הבא בסדרה: {' → '.join(seq)} → ?"}, ensure_ascii=False),
        "solution": json.dumps({"format": "markdown", "body": f"הסדרה מתקדמת מחזורית. אחרי {seq[-1]} מגיע {correct}."}, ensure_ascii=False),
        "secs": 40 + (i % 4) * 5, "meta": json.dumps(meta, ensure_ascii=False)}).scalar_one()
    snap = []
    for order, (text, ok, exp) in enumerate(answers, 1):
        aid = conn.execute(sa.text("""INSERT INTO answers (question_id,answer_text,is_correct,explanation_if_selected,"order",created_at,updated_at)
            VALUES (:qid,:text,:ok,CAST(:exp AS JSON),:ord,NOW(),NOW()) RETURNING id"""), {
            "qid": qid, "text": text, "ok": ok, "exp": json.dumps({"format": "markdown", "body": exp}, ensure_ascii=False), "ord": order}).scalar_one()
        snap.append({"id": aid, "answer_text": text, "is_correct": ok, "explanation_if_selected": {"format": "markdown", "body": exp}, "order": order})
    conn.execute(sa.text("""INSERT INTO question_versions (question_id,version_number,category_id,question_type,difficulty,status,body,solution_text,question_metadata,answer_snapshot,recommended_time_seconds,created_at,updated_at)
        SELECT :qid,1,category_id,question_type,difficulty,status,body,solution_text,question_metadata,CAST(:snap AS JSONB),recommended_time_seconds,NOW(),NOW() FROM questions WHERE id=:qid"""), {"qid": qid, "snap": json.dumps(snap, ensure_ascii=False)})
    return 1


def upgrade():
    conn = op.get_bind()
    cid = _get_or_create_category(conn, "דפוסים חזותיים", "figural", "חשיבה מרחבית וצורנית", 4)
    added = sum(_add(conn, cid, i) for i in range(1, 31)) if cid else 0
    print({"migration": "question_bank_v8", "attempted": 30, "added": added})


def downgrade():
    conn = op.get_bind()
    ids = conn.execute(sa.text("SELECT id FROM questions WHERE question_metadata ->> 'bank_key' LIKE 'QB-F-P-%'")).scalars().all()
    for qid in ids:
        conn.execute(sa.text("DELETE FROM question_versions WHERE question_id=:qid"), {"qid": qid})
        conn.execute(sa.text("DELETE FROM answers WHERE question_id=:qid"), {"qid": qid})
        conn.execute(sa.text("DELETE FROM questions WHERE id=:qid"), {"qid": qid})

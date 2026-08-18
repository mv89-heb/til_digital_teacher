"""Connect the Learning Center lessons to the shared question bank.

Revision ID: 20260818_learning_center_v11
Revises: 20260818_learning_center_v10

The Learning Center and the question bank remain one source of truth: lessons
reference real published questions through the existing Question.lesson_id
field and expose a small guided-practice set as embedded_question blocks.
"""
import json
from alembic import op
import sqlalchemy as sa

revision = "20260818_learning_center_v11"
down_revision = "20260818_learning_center_v10"
branch_labels = None
depends_on = None


def _lesson_ids(conn):
    rows = conn.execute(sa.text("""
        SELECT id, slug, category_id
        FROM lessons
        WHERE slug LIKE 'learning-v10-%'
        ORDER BY slug
    """)).mappings().all()
    return rows


def _attach_questions(conn, lesson_id, category_id, lesson_slug, limit=5):
    # Prefer questions that are not already owned by another lesson. This
    # keeps the bank reusable while giving each lesson a concrete practice set.
    rows = conn.execute(sa.text("""
        SELECT id
        FROM questions
        WHERE category_id = :category_id
          AND status = 'published'
          AND (lesson_id IS NULL OR lesson_id = :lesson_id)
        ORDER BY
          CASE WHEN lesson_id = :lesson_id THEN 0 ELSE 1 END,
          id
        LIMIT :limit
    """), {"category_id": category_id, "lesson_id": lesson_id, "limit": limit}).scalars().all()

    for question_id in rows:
        conn.execute(sa.text("""
            UPDATE questions
            SET lesson_id = :lesson_id,
                updated_at = NOW()
            WHERE id = :question_id
              AND (lesson_id IS NULL OR lesson_id = :lesson_id)
        """), {"lesson_id": lesson_id, "question_id": question_id})
    return rows


def _ensure_guided_blocks(conn, lesson_id, question_ids):
    # Do not duplicate blocks if the deployment is retried.
    existing = conn.execute(sa.text("""
        SELECT content
        FROM lesson_contents
        WHERE lesson_id = :lesson_id
          AND section = 'guided_practice'
          AND block_type = 'embedded_question'
    """), {"lesson_id": lesson_id}).all()
    existing_ids = set()
    for row in existing:
        payload = row[0] or {}
        if isinstance(payload, dict):
            qid = payload.get("question_id")
            if qid is not None:
                existing_ids.add(int(qid))

    next_order = conn.execute(sa.text("""
        SELECT COALESCE(MAX("order"), 0) + 1
        FROM lesson_contents
        WHERE lesson_id = :lesson_id
    """), {"lesson_id": lesson_id}).scalar_one()

    added = 0
    for question_id in question_ids:
        if int(question_id) in existing_ids:
            continue
        conn.execute(sa.text("""
            INSERT INTO lesson_contents
                (lesson_id, section, block_type, "order", content,
                 block_metadata, created_at, updated_at)
            VALUES
                (:lesson_id, 'guided_practice', 'embedded_question', :ord,
                 CAST(:content AS JSON), CAST(:meta AS JSON), NOW(), NOW())
        """), {
            "lesson_id": lesson_id,
            "ord": next_order,
            "content": json.dumps({"question_id": int(question_id)}, ensure_ascii=False),
            "meta": json.dumps({
                "source": "shared_question_bank",
                "mode": "practice",
                "show_explanation_after_answer": True,
            }, ensure_ascii=False),
        })
        next_order += 1
        added += 1
    return added


def upgrade():
    conn = op.get_bind()
    lessons = _lesson_ids(conn)
    attached = 0
    blocks = 0

    for lesson in lessons:
        question_ids = _attach_questions(
            conn,
            lesson_id=lesson["id"],
            category_id=lesson["category_id"],
            lesson_slug=lesson["slug"],
            limit=5,
        )
        attached += len(question_ids)
        blocks += _ensure_guided_blocks(conn, lesson["id"], question_ids[:3])

    print({
        "migration": "learning_center_v11",
        "lessons_processed": len(lessons),
        "questions_attached": attached,
        "guided_practice_blocks_added": blocks,
    })


def downgrade():
    conn = op.get_bind()
    lesson_ids = conn.execute(sa.text("""
        SELECT id FROM lessons WHERE slug LIKE 'learning-v10-%'
    """)).scalars().all()
    if not lesson_ids:
        return

    for lesson_id in lesson_ids:
        conn.execute(sa.text("""
            DELETE FROM lesson_contents
            WHERE lesson_id = :lesson_id
              AND section = 'guided_practice'
              AND block_type = 'embedded_question'
              AND block_metadata ->> 'source' = 'shared_question_bank'
        """), {"lesson_id": lesson_id})
        conn.execute(sa.text("""
            UPDATE questions
            SET lesson_id = NULL, updated_at = NOW()
            WHERE lesson_id = :lesson_id
              AND (question_metadata ->> 'bank_key' LIKE 'QB-%')
        """), {"lesson_id": lesson_id})

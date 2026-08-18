"""Repair question snapshots and normalize bank metadata.

Revision ID: 20260818_question_bank_v6
Revises: 20260818_question_bank_v5
"""
from alembic import op
import sqlalchemy as sa

revision = "20260818_question_bank_v6"
down_revision = "20260818_question_bank_v5"
branch_labels = None
depends_on = None


def upgrade():
    conn = op.get_bind()

    # v5 rebuilt answers but accidentally omitted answer ids from the
    # immutable version snapshot. ExamService uses those ids when validating
    # submissions, so every latest version must contain them.
    conn.execute(sa.text("""
        UPDATE question_versions v
        SET answer_snapshot = COALESCE((
            SELECT jsonb_agg(
                jsonb_build_object(
                    'id', a.id,
                    'answer_text', a.answer_text,
                    'is_correct', a.is_correct,
                    'explanation_if_selected', a.explanation_if_selected,
                    'order', a."order"
                ) ORDER BY a."order", a.id
            )
            FROM answers a
            WHERE a.question_id = v.question_id
        ), '[]'::jsonb)
        WHERE v.version_number = (
            SELECT MAX(v2.version_number)
            FROM question_versions v2
            WHERE v2.question_id = v.question_id
        )
    """))

    # Repair any already-created session snapshots as well. This is safe for
    # sessions that have not yet received an answer and makes the migration
    # resilient if a session was created immediately before v6 deployed.
    conn.execute(sa.text("""
        UPDATE session_questions sq
        SET answer_snapshot = COALESCE((
            SELECT jsonb_agg(
                jsonb_build_object(
                    'id', a.id,
                    'answer_text', a.answer_text,
                    'is_correct', a.is_correct,
                    'explanation_if_selected', a.explanation_if_selected,
                    'order', a."order"
                ) ORDER BY a."order", a.id
            )
            FROM answers a
            WHERE a.question_id = sq.question_id
        ), '[]'::jsonb)
        WHERE sq.question_id IS NOT NULL
    """))

    # The renderer expects visual_data while the seed stored visual.
    conn.execute(sa.text("""
        UPDATE questions
        SET question_metadata = jsonb_set(
            COALESCE(question_metadata::jsonb, '{}'::jsonb),
            '{visual_data}',
            COALESCE(question_metadata::jsonb -> 'visual', 'null'::jsonb),
            true
        )
        WHERE question_metadata::jsonb ? 'visual'
    """))

    # Keep the legacy difficulty field compatible with QuestionDifficulty
    # while retaining the precise 1..5 calibration in metadata.
    conn.execute(sa.text("""
        UPDATE questions
        SET difficulty = CASE
            WHEN COALESCE((question_metadata::jsonb ->> 'difficulty_level')::int, 3) <= 2 THEN 'easy'
            WHEN COALESCE((question_metadata::jsonb ->> 'difficulty_level')::int, 3) = 3 THEN 'medium'
            ELSE 'exam'
        END
        WHERE question_metadata::jsonb ? 'difficulty_level'
    """))

    conn.execute(sa.text("""
        UPDATE question_versions v
        SET difficulty = q.difficulty,
            question_metadata = q.question_metadata
        FROM questions q
        WHERE q.id = v.question_id
    """))


def downgrade():
    pass

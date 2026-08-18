"""Fix exam-engine migration parity and historical snapshots.

Revision ID: 20260818_exam_engine_integrity_fix
Revises: 20260818_exam_engine_hardening
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "20260818_exam_engine_integrity_fix"
down_revision = "20260818_exam_engine_hardening"
branch_labels = None
depends_on = None


def upgrade():
    # The hardening migration already creates updated_at on every exam table
    # except question_versions. Add it only where it is actually missing.
    op.add_column(
        "question_versions",
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.execute(sa.text("UPDATE question_versions SET updated_at = created_at WHERE updated_at IS NULL"))
    op.alter_column("question_versions", "updated_at", nullable=False, server_default=sa.func.now())

    # Freeze answer correctness/content together with each question version.
    op.add_column(
        "question_versions",
        sa.Column("answer_snapshot", postgresql.JSONB(), nullable=False, server_default=sa.text("'[]'::jsonb")),
    )

    # Backfill one immutable version for every existing question.
    op.execute(
        sa.text(
            """
            INSERT INTO question_versions
                (question_id, version_number, category_id, question_type,
                 difficulty, status, body, solution_text, question_metadata,
                 answer_snapshot, recommended_time_seconds, created_by,
                 created_at, updated_at)
            SELECT
                q.id, 1, q.category_id, q.question_type, q.difficulty, q.status,
                q.body, q.solution_text,
                COALESCE(q.question_metadata, '{}'::jsonb),
                COALESCE(
                    (
                        SELECT jsonb_agg(
                            jsonb_build_object(
                                'id', a.id,
                                'answer_text', a.answer_text,
                                'is_correct', a.is_correct,
                                'explanation_if_selected', a.explanation_if_selected,
                                'order', a."order"
                            ) ORDER BY a."order", a.id
                        )
                        FROM answers a WHERE a.question_id = q.id
                    ),
                    '[]'::jsonb
                ),
                q.recommended_time_seconds, q.created_by,
                COALESCE(q.created_at, NOW()), COALESCE(q.updated_at, NOW())
            FROM questions q
            WHERE NOT EXISTS (
                SELECT 1 FROM question_versions v WHERE v.question_id = q.id
            )
            """
        )
    )

    # Preserve the exact answer set used by every session question.
    op.add_column(
        "session_questions",
        sa.Column("answer_snapshot", postgresql.JSONB(), nullable=False, server_default=sa.text("'[]'::jsonb")),
    )
    op.execute(
        sa.text(
            """
            UPDATE session_questions sq
            SET answer_snapshot = COALESCE(qv.answer_snapshot, '[]'::jsonb)
            FROM question_versions qv
            WHERE qv.id = sq.question_version_id
            """
        )
    )

    # Only one final answer may exist for a session question.
    op.execute(
        "CREATE UNIQUE INDEX uq_user_answers_one_final "
        "ON user_answers(session_question_id) WHERE is_final = TRUE"
    )


def downgrade():
    op.execute("DROP INDEX IF EXISTS uq_user_answers_one_final")
    op.drop_column("session_questions", "answer_snapshot")
    op.drop_column("question_versions", "answer_snapshot")
    op.drop_column("question_versions", "updated_at")

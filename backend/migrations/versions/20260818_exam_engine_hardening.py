"""Exam engine schema and integrity hardening.

Revision ID: 20260818_exam_engine_hardening
Revises: 122cbf161068
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "20260818_exam_engine_hardening"
down_revision = "122cbf161068"
branch_labels = None
depends_on = None


def upgrade():
    # Question versioning: preserves the exact content used by historical sessions.
    op.create_table(
        "question_versions",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("question_id", sa.Integer(), sa.ForeignKey("questions.id", ondelete="CASCADE"), nullable=False),
        sa.Column("version_number", sa.Integer(), nullable=False),
        sa.Column("category_id", sa.Integer(), sa.ForeignKey("categories.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("question_type", sa.String(30), nullable=False),
        sa.Column("difficulty", sa.String(20), nullable=False),
        sa.Column("status", sa.String(20), nullable=False),
        sa.Column("body", postgresql.JSONB(), nullable=False),
        sa.Column("solution_text", postgresql.JSONB(), nullable=False),
        sa.Column("question_metadata", postgresql.JSONB(), nullable=False, server_default=sa.text("'{}'::jsonb")),
        sa.Column("recommended_time_seconds", sa.Integer(), nullable=True),
        sa.Column("created_by", sa.Integer(), sa.ForeignKey("users.id", ondelete="SET NULL"), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.UniqueConstraint("question_id", "version_number", name="uq_question_versions_question_version"),
    )
    op.create_index("ix_question_versions_question_id", "question_versions", ["question_id"])

    # Exam definitions and sections.
    op.create_table(
        "exams",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("name", sa.String(200), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("version", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("status", sa.String(20), nullable=False, server_default="DRAFT"),
        sa.Column("duration_seconds", sa.Integer(), nullable=False),
        sa.Column("configuration", postgresql.JSONB(), nullable=False, server_default=sa.text("'{}'::jsonb")),
        sa.Column("created_by", sa.Integer(), sa.ForeignKey("users.id", ondelete="SET NULL"), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.CheckConstraint("duration_seconds > 0", name="ck_exams_duration_positive"),
    )
    op.create_table(
        "exam_sections",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("exam_id", sa.Integer(), sa.ForeignKey("exams.id", ondelete="CASCADE"), nullable=False),
        sa.Column("name", sa.String(200), nullable=False),
        sa.Column("category", sa.String(30), nullable=False),
        sa.Column("display_order", sa.Integer(), nullable=False),
        sa.Column("duration_seconds", sa.Integer(), nullable=True),
        sa.Column("question_count", sa.Integer(), nullable=True),
        sa.Column("instructions", postgresql.JSONB(), nullable=True),
        sa.Column("scoring_configuration", postgresql.JSONB(), nullable=False, server_default=sa.text("'{}'::jsonb")),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.UniqueConstraint("exam_id", "display_order", name="uq_exam_sections_order"),
    )
    op.create_index("ix_exam_sections_exam_id", "exam_sections", ["exam_id"])

    op.create_table(
        "exam_question_pool",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("exam_section_id", sa.Integer(), sa.ForeignKey("exam_sections.id", ondelete="CASCADE"), nullable=False),
        sa.Column("question_id", sa.Integer(), sa.ForeignKey("questions.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("question_version_id", sa.Integer(), sa.ForeignKey("question_versions.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("weight", sa.Numeric(8, 4), nullable=False, server_default="1"),
        sa.Column("selection_probability", sa.Numeric(8, 4), nullable=True),
        sa.Column("display_order", sa.Integer(), nullable=True),
        sa.Column("is_required", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.UniqueConstraint("exam_section_id", "question_id", name="uq_exam_question_pool_question"),
        sa.CheckConstraint("weight > 0", name="ck_exam_question_pool_weight_positive"),
    )
    op.create_index("ix_exam_question_pool_section", "exam_question_pool", ["exam_section_id"])

    # Runtime session and immutable question assignment.
    op.create_table(
        "exam_sessions",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("user_id", sa.Integer(), sa.ForeignKey("users.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("exam_id", sa.Integer(), sa.ForeignKey("exams.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("status", sa.String(20), nullable=False, server_default="CREATED"),
        sa.Column("exam_version", sa.Integer(), nullable=False),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("submitted_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("last_activity_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("current_question_index", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("state", postgresql.JSONB(), nullable=False, server_default=sa.text("'{}'::jsonb")),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )
    op.create_index("ix_exam_sessions_user_id", "exam_sessions", ["user_id"])
    op.create_index("ix_exam_sessions_status", "exam_sessions", ["status"])
    op.create_index("ix_exam_sessions_expires_at", "exam_sessions", ["expires_at"])

    op.create_table(
        "session_questions",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("session_id", sa.Integer(), sa.ForeignKey("exam_sessions.id", ondelete="CASCADE"), nullable=False),
        sa.Column("question_id", sa.Integer(), sa.ForeignKey("questions.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("question_version_id", sa.Integer(), sa.ForeignKey("question_versions.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("section_id", sa.Integer(), sa.ForeignKey("exam_sections.id", ondelete="RESTRICT"), nullable=True),
        sa.Column("sequence_number", sa.Integer(), nullable=False),
        sa.Column("weight", sa.Numeric(8, 4), nullable=False, server_default="1"),
        sa.Column("status", sa.String(20), nullable=False, server_default="UNANSWERED"),
        sa.Column("first_seen_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("last_seen_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("answered_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("total_time_ms", sa.BigInteger(), nullable=False, server_default="0"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.UniqueConstraint("session_id", "sequence_number", name="uq_session_question_sequence"),
        sa.UniqueConstraint("session_id", "question_id", name="uq_session_question_question"),
    )
    op.create_index("ix_session_questions_session_id", "session_questions", ["session_id"])

    op.create_table(
        "user_answers",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("session_question_id", sa.Integer(), sa.ForeignKey("session_questions.id", ondelete="CASCADE"), nullable=False),
        sa.Column("answer_id", sa.Integer(), sa.ForeignKey("answers.id", ondelete="RESTRICT"), nullable=True),
        sa.Column("answer_value", postgresql.JSONB(), nullable=True),
        sa.Column("is_final", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("is_correct", sa.Boolean(), nullable=True),
        sa.Column("answered_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("response_time_ms", sa.BigInteger(), nullable=True),
        sa.Column("score", sa.Numeric(10, 4), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )
    op.create_index("ix_user_answers_session_question_id", "user_answers", ["session_question_id"])

    op.create_table(
        "question_events",
        sa.Column("id", sa.BigInteger(), primary_key=True),
        sa.Column("session_id", sa.Integer(), sa.ForeignKey("exam_sessions.id", ondelete="CASCADE"), nullable=False),
        sa.Column("session_question_id", sa.Integer(), sa.ForeignKey("session_questions.id", ondelete="CASCADE"), nullable=True),
        sa.Column("event_type", sa.String(50), nullable=False),
        sa.Column("event_timestamp", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("elapsed_ms", sa.BigInteger(), nullable=True),
        sa.Column("metadata", postgresql.JSONB(), nullable=False, server_default=sa.text("'{}'::jsonb")),
    )
    op.create_index("ix_question_events_session_id", "question_events", ["session_id"])

    # Results and analytical breakdowns.
    op.create_table(
        "exam_results",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("session_id", sa.Integer(), sa.ForeignKey("exam_sessions.id", ondelete="RESTRICT"), nullable=False, unique=True),
        sa.Column("user_id", sa.Integer(), sa.ForeignKey("users.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("exam_id", sa.Integer(), sa.ForeignKey("exams.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("raw_score", sa.Numeric(12, 4), nullable=False, server_default="0"),
        sa.Column("weighted_score", sa.Numeric(12, 4), nullable=False, server_default="0"),
        sa.Column("normalized_score", sa.Numeric(12, 4), nullable=True),
        sa.Column("percentile", sa.Numeric(7, 4), nullable=True),
        sa.Column("total_questions", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("answered_questions", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("correct_answers", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("skipped_questions", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("total_time_ms", sa.BigInteger(), nullable=False, server_default="0"),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("metadata", postgresql.JSONB(), nullable=False, server_default=sa.text("'{}'::jsonb")),
    )
    op.create_index("ix_exam_results_user_id", "exam_results", ["user_id"])
    op.create_index("ix_exam_results_exam_id", "exam_results", ["exam_id"])

    op.create_table(
        "exam_result_categories",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("result_id", sa.Integer(), sa.ForeignKey("exam_results.id", ondelete="CASCADE"), nullable=False),
        sa.Column("category", sa.String(30), nullable=False),
        sa.Column("total_questions", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("answered_questions", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("correct_answers", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("raw_score", sa.Numeric(12, 4), nullable=False, server_default="0"),
        sa.Column("weighted_score", sa.Numeric(12, 4), nullable=False, server_default="0"),
        sa.Column("accuracy", sa.Numeric(7, 4), nullable=True),
        sa.Column("total_time_ms", sa.BigInteger(), nullable=False, server_default="0"),
        sa.Column("average_time_ms", sa.BigInteger(), nullable=True),
        sa.UniqueConstraint("result_id", "category", name="uq_exam_result_category"),
    )

    op.create_table(
        "exam_result_difficulties",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("result_id", sa.Integer(), sa.ForeignKey("exam_results.id", ondelete="CASCADE"), nullable=False),
        sa.Column("difficulty", sa.String(20), nullable=False),
        sa.Column("total_questions", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("correct_answers", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("accuracy", sa.Numeric(7, 4), nullable=True),
        sa.Column("average_time_ms", sa.BigInteger(), nullable=True),
        sa.UniqueConstraint("result_id", "difficulty", name="uq_exam_result_difficulty"),
    )

    # Operational integrity: one correct answer for single-answer questions is
    # enforced at the DB layer. PostgreSQL partial indexes are intentional.
    op.execute(
        "CREATE UNIQUE INDEX uq_answers_one_correct_per_question "
        "ON answers(question_id) WHERE is_correct = TRUE"
    )

    # Existing slug uniqueness must be enforced atomically.
    op.execute(
        "CREATE UNIQUE INDEX IF NOT EXISTS uq_lessons_slug ON lessons(slug)"
    )

    # Safe role/content constraints.
    op.execute(
        "ALTER TABLE users ADD CONSTRAINT ck_users_role_valid "
        "CHECK (role IN ('student', 'admin'))"
    )

    # Ensure the legacy XP counter is safe at DB level.
    op.execute(
        "ALTER TABLE users ALTER COLUMN xp_total SET DEFAULT 0"
    )


def downgrade():
    op.execute("DROP INDEX IF EXISTS uq_lessons_slug")
    op.execute("DROP INDEX IF EXISTS uq_answers_one_correct_per_question")
    op.execute("ALTER TABLE users ALTER COLUMN xp_total DROP DEFAULT")
    op.execute("ALTER TABLE users DROP CONSTRAINT IF EXISTS ck_users_role_valid")

    op.drop_table("exam_result_difficulties")
    op.drop_table("exam_result_categories")
    op.drop_index("ix_exam_results_exam_id", table_name="exam_results")
    op.drop_index("ix_exam_results_user_id", table_name="exam_results")
    op.drop_table("exam_results")
    op.drop_index("ix_question_events_session_id", table_name="question_events")
    op.drop_table("question_events")
    op.drop_index("ix_user_answers_session_question_id", table_name="user_answers")
    op.drop_table("user_answers")
    op.drop_index("ix_session_questions_session_id", table_name="session_questions")
    op.drop_table("session_questions")
    op.drop_index("ix_exam_sessions_expires_at", table_name="exam_sessions")
    op.drop_index("ix_exam_sessions_status", table_name="exam_sessions")
    op.drop_index("ix_exam_sessions_user_id", table_name="exam_sessions")
    op.drop_table("exam_sessions")
    op.drop_index("ix_exam_question_pool_section", table_name="exam_question_pool")
    op.drop_table("exam_question_pool")
    op.drop_index("ix_exam_sections_exam_id", table_name="exam_sections")
    op.drop_table("exam_sections")
    op.drop_table("exams")
    op.drop_index("ix_question_versions_question_id", table_name="question_versions")
    op.drop_table("question_versions")

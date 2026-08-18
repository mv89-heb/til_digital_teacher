"""Add persistent feedback memory for the local TIL teacher.

The migration merges the independent learning-center, question-bank and
exam-engine heads before introducing teacher memory so production keeps a
single Alembic head.
"""
from alembic import op
import sqlalchemy as sa

revision = "20260818_teacher_memory_v1"
down_revision = (
    "20260818_question_bank_v7",
    "20260818_lc_v14b",
    "20260818_merge_stage4_exam_heads",
)
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "teacher_feedback",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("user_id", sa.Integer(), sa.ForeignKey("users.id", ondelete="SET NULL"), nullable=True),
        sa.Column("question_id", sa.Integer(), sa.ForeignKey("questions.id", ondelete="SET NULL"), nullable=True),
        sa.Column("topic", sa.String(120), nullable=True),
        sa.Column("subcategory", sa.String(120), nullable=True),
        sa.Column("skill", sa.String(120), nullable=True),
        sa.Column("student_query", sa.Text(), nullable=False),
        sa.Column("original_answer", sa.Text(), nullable=True),
        sa.Column("feedback", sa.Text(), nullable=False),
        sa.Column("correction", sa.Text(), nullable=False),
        sa.Column("correct_answer", sa.Text(), nullable=True),
        sa.Column("error_type", sa.String(40), nullable=True),
        sa.Column("severity", sa.String(20), nullable=False, server_default="medium"),
        sa.Column("source", sa.String(30), nullable=False, server_default="student"),
        sa.Column("status", sa.String(30), nullable=False, server_default="pending"),
        sa.Column("confidence", sa.Integer(), nullable=False, server_default="50"),
        sa.Column("times_used", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("last_used_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("ix_teacher_feedback_user_id", "teacher_feedback", ["user_id"])
    op.create_index("ix_teacher_feedback_question_id", "teacher_feedback", ["question_id"])
    op.create_index("ix_teacher_feedback_topic", "teacher_feedback", ["topic"])
    op.create_index("ix_teacher_feedback_subcategory", "teacher_feedback", ["subcategory"])
    op.create_index("ix_teacher_feedback_skill", "teacher_feedback", ["skill"])
    op.create_index("ix_teacher_feedback_error_type", "teacher_feedback", ["error_type"])
    op.create_index("ix_teacher_feedback_status", "teacher_feedback", ["status"])
    op.create_index("ix_teacher_feedback_topic_status", "teacher_feedback", ["topic", "status"])
    op.create_index("ix_teacher_feedback_question_status", "teacher_feedback", ["question_id", "status"])


def downgrade():
    op.drop_index("ix_teacher_feedback_question_status", table_name="teacher_feedback")
    op.drop_index("ix_teacher_feedback_topic_status", table_name="teacher_feedback")
    op.drop_index("ix_teacher_feedback_status", table_name="teacher_feedback")
    op.drop_index("ix_teacher_feedback_error_type", table_name="teacher_feedback")
    op.drop_index("ix_teacher_feedback_skill", table_name="teacher_feedback")
    op.drop_index("ix_teacher_feedback_subcategory", table_name="teacher_feedback")
    op.drop_index("ix_teacher_feedback_topic", table_name="teacher_feedback")
    op.drop_index("ix_teacher_feedback_question_id", table_name="teacher_feedback")
    op.drop_index("ix_teacher_feedback_user_id", table_name="teacher_feedback")
    op.drop_table("teacher_feedback")

"""Add last_login_at to users.

Revision ID: 20260818_add_user_last_login_at
Revises: 20260818_merge_stage4_exam_heads
"""

from alembic import op
import sqlalchemy as sa


revision = "20260818_add_user_last_login_at"
down_revision = "20260818_merge_stage4_exam_heads"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column(
        "users",
        sa.Column("last_login_at", sa.DateTime(), nullable=True),
    )


def downgrade():
    op.drop_column("users", "last_login_at")

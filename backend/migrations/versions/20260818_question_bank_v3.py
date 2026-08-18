"""Compatibility migration for the TIL question bank.

Revision ID: 20260818_question_bank_v3
Revises: 20260818_question_bank_v2
"""

from alembic import op

revision = "20260818_question_bank_v3"
down_revision = "20260818_question_bank_v2"
branch_labels = None
depends_on = None


def upgrade():
    # The original v3 contained Python literals copied from JSON (null),
    # which made Alembic fail while importing the migration. Keep this
    # revision schema-safe and move question seeding to the dedicated bank
    # migration that follows it.
    pass


def downgrade():
    pass

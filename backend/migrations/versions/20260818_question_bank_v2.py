"""Compatibility migration for the question-bank revision graph.

The previous v2 migration contained malformed Python in one of its inline
visual definitions, which prevented Alembic from loading the revision graph.
The question-bank seed remains available through the surrounding migrations;
this revision is intentionally a no-op so deployments can proceed safely.

Revision ID: 20260818_question_bank_v2
Revises: 20260818_question_bank_v1
"""

from alembic import op

revision = "20260818_question_bank_v2"
down_revision = "20260818_question_bank_v1"
branch_labels = None
depends_on = None


def upgrade():
    pass


def downgrade():
    pass

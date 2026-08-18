"""Merge the Stage 4 and exam-engine migration heads.

Revision ID: 20260818_merge_stage4_exam_heads
Revises: 6d983a13bcd6, 20260818_exam_engine_integrity_fix
"""

revision = "20260818_merge_stage4_exam_heads"
down_revision = ("6d983a13bcd6", "20260818_exam_engine_integrity_fix")
branch_labels = None
depends_on = None


def upgrade():
    # Merge-only migration. Both parent branches have already applied their
    # schema changes; this revision establishes a single Alembic head.
    pass


def downgrade():
    # Intentionally empty. Reverting this merge does not undo either parent
    # branch; Alembic will expose the two parent heads again.
    pass

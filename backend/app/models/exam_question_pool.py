from app.extensions import db
from app.models.mixins import TimestampMixin


class ExamQuestionPool(db.Model, TimestampMixin):
    __tablename__ = "exam_question_pool"
    __table_args__ = (db.UniqueConstraint("exam_section_id", "question_id", name="uq_exam_question_pool_question"),)

    id = db.Column(db.Integer, primary_key=True)
    exam_section_id = db.Column(db.Integer, db.ForeignKey("exam_sections.id", ondelete="CASCADE"), nullable=False, index=True)
    question_id = db.Column(db.Integer, db.ForeignKey("questions.id", ondelete="RESTRICT"), nullable=False)
    question_version_id = db.Column(db.Integer, db.ForeignKey("question_versions.id", ondelete="RESTRICT"), nullable=False)
    weight = db.Column(db.Numeric(8, 4), nullable=False, default=1)
    selection_probability = db.Column(db.Numeric(8, 4))
    display_order = db.Column(db.Integer)
    is_required = db.Column(db.Boolean, nullable=False, default=True)

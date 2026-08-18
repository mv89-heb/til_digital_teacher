from app.extensions import db
from app.models.mixins import TimestampMixin


class ExamSection(db.Model, TimestampMixin):
    __tablename__ = "exam_sections"
    __table_args__ = (db.UniqueConstraint("exam_id", "display_order", name="uq_exam_sections_order"),)

    id = db.Column(db.Integer, primary_key=True)
    exam_id = db.Column(db.Integer, db.ForeignKey("exams.id", ondelete="CASCADE"), nullable=False, index=True)
    name = db.Column(db.String(200), nullable=False)
    category = db.Column(db.String(30), nullable=False)
    display_order = db.Column(db.Integer, nullable=False)
    duration_seconds = db.Column(db.Integer)
    question_count = db.Column(db.Integer)
    instructions = db.Column(db.JSON)
    scoring_configuration = db.Column(db.JSON, nullable=False, default=dict)

    exam = db.relationship("Exam", back_populates="sections")

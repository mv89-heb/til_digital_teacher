from app.extensions import db
from app.models.mixins import TimestampMixin


class ExamResult(db.Model, TimestampMixin):
    __tablename__ = "exam_results"

    id = db.Column(db.Integer, primary_key=True)
    session_id = db.Column(db.Integer, db.ForeignKey("exam_sessions.id", ondelete="RESTRICT"), nullable=False, unique=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id", ondelete="RESTRICT"), nullable=False, index=True)
    exam_id = db.Column(db.Integer, db.ForeignKey("exams.id", ondelete="RESTRICT"), nullable=False, index=True)
    raw_score = db.Column(db.Numeric(12, 4), nullable=False, default=0)
    weighted_score = db.Column(db.Numeric(12, 4), nullable=False, default=0)
    normalized_score = db.Column(db.Numeric(12, 4))
    percentile = db.Column(db.Numeric(7, 4))
    total_questions = db.Column(db.Integer, nullable=False, default=0)
    answered_questions = db.Column(db.Integer, nullable=False, default=0)
    correct_answers = db.Column(db.Integer, nullable=False, default=0)
    skipped_questions = db.Column(db.Integer, nullable=False, default=0)
    total_time_ms = db.Column(db.BigInteger, nullable=False, default=0)
    completed_at = db.Column(db.DateTime(timezone=True), nullable=False, server_default=db.func.now())
    metadata_json = db.Column("metadata", db.JSON, nullable=False, default=dict)

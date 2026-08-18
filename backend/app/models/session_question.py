from app.extensions import db
from app.models.mixins import TimestampMixin


class SessionQuestion(db.Model, TimestampMixin):
    __tablename__ = "session_questions"
    __table_args__ = (
        db.UniqueConstraint("session_id", "sequence_number", name="uq_session_question_sequence"),
        db.UniqueConstraint("session_id", "question_id", name="uq_session_question_question"),
    )

    id = db.Column(db.Integer, primary_key=True)
    session_id = db.Column(db.Integer, db.ForeignKey("exam_sessions.id", ondelete="CASCADE"), nullable=False, index=True)
    question_id = db.Column(db.Integer, db.ForeignKey("questions.id", ondelete="RESTRICT"), nullable=False)
    question_version_id = db.Column(db.Integer, db.ForeignKey("question_versions.id", ondelete="RESTRICT"), nullable=False)
    section_id = db.Column(db.Integer, db.ForeignKey("exam_sections.id", ondelete="RESTRICT"))
    sequence_number = db.Column(db.Integer, nullable=False)
    weight = db.Column(db.Numeric(8, 4), nullable=False, default=1)
    status = db.Column(db.String(20), nullable=False, default="UNANSWERED")
    first_seen_at = db.Column(db.DateTime(timezone=True))
    last_seen_at = db.Column(db.DateTime(timezone=True))
    answered_at = db.Column(db.DateTime(timezone=True))
    total_time_ms = db.Column(db.BigInteger, nullable=False, default=0)
    answer_snapshot = db.Column(db.JSON, nullable=False, default=list)

    session = db.relationship("ExamSession", back_populates="questions")

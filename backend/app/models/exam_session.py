from app.extensions import db
from app.models.mixins import TimestampMixin


class ExamSession(db.Model, TimestampMixin):
    __tablename__ = "exam_sessions"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id", ondelete="RESTRICT"), nullable=False, index=True)
    exam_id = db.Column(db.Integer, db.ForeignKey("exams.id", ondelete="RESTRICT"), nullable=False)
    status = db.Column(db.String(20), nullable=False, default="CREATED", index=True)
    exam_version = db.Column(db.Integer, nullable=False)
    started_at = db.Column(db.DateTime(timezone=True))
    expires_at = db.Column(db.DateTime(timezone=True), index=True)
    submitted_at = db.Column(db.DateTime(timezone=True))
    last_activity_at = db.Column(db.DateTime(timezone=True))
    current_question_index = db.Column(db.Integer, nullable=False, default=0)
    state = db.Column(db.JSON, nullable=False, default=dict)

    questions = db.relationship("SessionQuestion", back_populates="session", cascade="all, delete-orphan", order_by="SessionQuestion.sequence_number")

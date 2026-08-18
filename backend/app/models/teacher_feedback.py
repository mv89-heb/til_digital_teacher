from app.extensions import db
from app.models.mixins import TimestampMixin


class TeacherFeedback(db.Model, TimestampMixin):
    """Human/student feedback that can become approved teacher memory.

    Feedback is deliberately separated from authoritative question content.
    Only approved records are retrieved as teaching rules.
    """

    __tablename__ = "teacher_feedback"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(
        db.Integer,
        db.ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    question_id = db.Column(
        db.Integer,
        db.ForeignKey("questions.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    topic = db.Column(db.String(120), nullable=True, index=True)
    subcategory = db.Column(db.String(120), nullable=True, index=True)
    skill = db.Column(db.String(120), nullable=True, index=True)
    student_query = db.Column(db.Text, nullable=False)
    original_answer = db.Column(db.Text, nullable=True)
    feedback = db.Column(db.Text, nullable=False)
    correction = db.Column(db.Text, nullable=False)
    correct_answer = db.Column(db.Text, nullable=True)
    error_type = db.Column(db.String(40), nullable=True, index=True)
    severity = db.Column(db.String(20), nullable=False, default="medium")
    source = db.Column(db.String(30), nullable=False, default="student")
    status = db.Column(db.String(30), nullable=False, default="pending", index=True)
    confidence = db.Column(db.Integer, nullable=False, default=50)
    times_used = db.Column(db.Integer, nullable=False, default=0)
    last_used_at = db.Column(db.DateTime(timezone=True), nullable=True)

    question = db.relationship("Question", lazy="joined")

    def to_dict(self):
        return {
            "id": self.id,
            "user_id": self.user_id,
            "question_id": self.question_id,
            "topic": self.topic,
            "subcategory": self.subcategory,
            "skill": self.skill,
            "student_query": self.student_query,
            "original_answer": self.original_answer,
            "feedback": self.feedback,
            "correction": self.correction,
            "correct_answer": self.correct_answer,
            "error_type": self.error_type,
            "severity": self.severity,
            "source": self.source,
            "status": self.status,
            "confidence": self.confidence,
            "times_used": self.times_used,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }

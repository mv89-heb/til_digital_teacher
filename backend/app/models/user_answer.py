from app.extensions import db
from app.models.mixins import TimestampMixin


class UserAnswer(db.Model, TimestampMixin):
    __tablename__ = "user_answers"

    id = db.Column(db.Integer, primary_key=True)
    session_question_id = db.Column(db.Integer, db.ForeignKey("session_questions.id", ondelete="CASCADE"), nullable=False, index=True)
    answer_id = db.Column(db.Integer, db.ForeignKey("answers.id", ondelete="RESTRICT"))
    answer_value = db.Column(db.JSON)
    is_final = db.Column(db.Boolean, nullable=False, default=False)
    is_correct = db.Column(db.Boolean)
    answered_at = db.Column(db.DateTime(timezone=True))
    response_time_ms = db.Column(db.BigInteger)
    score = db.Column(db.Numeric(10, 4))

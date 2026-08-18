from app.extensions import db


class ExamEvent(db.Model):
    __tablename__ = "question_events"

    id = db.Column(db.BigInteger, primary_key=True)
    session_id = db.Column(db.Integer, db.ForeignKey("exam_sessions.id", ondelete="CASCADE"), nullable=False, index=True)
    session_question_id = db.Column(db.Integer, db.ForeignKey("session_questions.id", ondelete="CASCADE"), nullable=True, index=True)
    event_type = db.Column(db.String(50), nullable=False)
    event_timestamp = db.Column(db.DateTime(timezone=True), nullable=False, server_default=db.func.now(), index=True)
    elapsed_ms = db.Column(db.BigInteger)
    metadata_json = db.Column("metadata", db.JSON, nullable=False, default=dict)

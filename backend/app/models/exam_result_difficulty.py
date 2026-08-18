from app.extensions import db


class ExamResultDifficulty(db.Model):
    __tablename__ = "exam_result_difficulties"
    __table_args__ = (db.UniqueConstraint("result_id", "difficulty", name="uq_exam_result_difficulty"),)

    id = db.Column(db.Integer, primary_key=True)
    result_id = db.Column(db.Integer, db.ForeignKey("exam_results.id", ondelete="CASCADE"), nullable=False)
    difficulty = db.Column(db.String(20), nullable=False)
    total_questions = db.Column(db.Integer, nullable=False, default=0)
    correct_answers = db.Column(db.Integer, nullable=False, default=0)
    accuracy = db.Column(db.Numeric(7, 4))
    average_time_ms = db.Column(db.BigInteger)

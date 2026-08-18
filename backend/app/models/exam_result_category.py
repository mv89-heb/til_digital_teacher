from app.extensions import db


class ExamResultCategory(db.Model):
    __tablename__ = "exam_result_categories"
    __table_args__ = (db.UniqueConstraint("result_id", "category", name="uq_exam_result_category"),)

    id = db.Column(db.Integer, primary_key=True)
    result_id = db.Column(db.Integer, db.ForeignKey("exam_results.id", ondelete="CASCADE"), nullable=False)
    category = db.Column(db.String(30), nullable=False)
    total_questions = db.Column(db.Integer, nullable=False, default=0)
    answered_questions = db.Column(db.Integer, nullable=False, default=0)
    correct_answers = db.Column(db.Integer, nullable=False, default=0)
    raw_score = db.Column(db.Numeric(12, 4), nullable=False, default=0)
    weighted_score = db.Column(db.Numeric(12, 4), nullable=False, default=0)
    accuracy = db.Column(db.Numeric(7, 4))
    total_time_ms = db.Column(db.BigInteger, nullable=False, default=0)
    average_time_ms = db.Column(db.BigInteger)

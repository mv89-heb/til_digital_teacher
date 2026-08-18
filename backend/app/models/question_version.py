from app.extensions import db
from app.models.mixins import TimestampMixin


class QuestionVersion(db.Model, TimestampMixin):
    __tablename__ = "question_versions"
    __table_args__ = (
        db.UniqueConstraint("question_id", "version_number", name="uq_question_versions_question_version"),
    )

    id = db.Column(db.Integer, primary_key=True)
    question_id = db.Column(db.Integer, db.ForeignKey("questions.id", ondelete="CASCADE"), nullable=False, index=True)
    version_number = db.Column(db.Integer, nullable=False)
    category_id = db.Column(db.Integer, db.ForeignKey("categories.id", ondelete="RESTRICT"), nullable=False)
    question_type = db.Column(db.String(30), nullable=False)
    difficulty = db.Column(db.String(20), nullable=False)
    status = db.Column(db.String(20), nullable=False)
    body = db.Column(db.JSON, nullable=False)
    solution_text = db.Column(db.JSON, nullable=False)
    question_metadata = db.Column(db.JSON, nullable=False, default=dict)
    answer_snapshot = db.Column(db.JSON, nullable=False, default=list)
    recommended_time_seconds = db.Column(db.Integer)
    created_by = db.Column(db.Integer, db.ForeignKey("users.id", ondelete="SET NULL"))

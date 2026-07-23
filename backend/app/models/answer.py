from app.extensions import db
from app.models.mixins import TimestampMixin


class Answer(db.Model, TimestampMixin):
    __tablename__ = "answers"

    id = db.Column(db.Integer, primary_key=True)
    question_id = db.Column(db.Integer, db.ForeignKey("questions.id"), nullable=False, index=True)
    answer_text = db.Column(db.String(500), nullable=False)
    is_correct = db.Column(db.Boolean, default=False, nullable=False)
    explanation_if_selected = db.Column(db.JSON, nullable=True)  # {"format": "markdown", "body": "..."}
    order = db.Column(db.Integer, default=0, nullable=False)

    question = db.relationship("Question", back_populates="answers")

    def to_dict(self, reveal: bool = False) -> dict:
        """By default, hides is_correct and explanation_if_selected — those
        would let the frontend infer the correct answer before submitting.
        Only admin content-management routes and post-submission responses
        should pass reveal=True.
        """
        data = {
            "id": self.id,
            "question_id": self.question_id,
            "answer_text": self.answer_text,
            "order": self.order,
        }
        if reveal:
            data["is_correct"] = self.is_correct
            data["explanation_if_selected"] = self.explanation_if_selected
            data["created_at"] = self.created_at.isoformat()
            data["updated_at"] = self.updated_at.isoformat()
        return data

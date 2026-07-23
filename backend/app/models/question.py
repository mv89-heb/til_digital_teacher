from app.extensions import db
from app.models.constants import ContentStatus
from app.models.mixins import TimestampMixin


class Question(db.Model, TimestampMixin):
    """A question is a standalone entity, never embedded wholesale into
    LessonContent JSON — a lesson references it by id only (see
    LessonContent's embedded_question block: content == {"question_id": N}).
    This lets the same question be reused across lessons/practice pools and
    edited in one place.
    """

    __tablename__ = "questions"

    id = db.Column(db.Integer, primary_key=True)
    category_id = db.Column(db.Integer, db.ForeignKey("categories.id"), nullable=False, index=True)
    lesson_id = db.Column(db.Integer, db.ForeignKey("lessons.id"), nullable=True, index=True)
    question_type = db.Column(db.String(30), default="multiple_choice", nullable=False)
    difficulty = db.Column(db.String(20), nullable=False, index=True)  # see QuestionDifficulty
    status = db.Column(db.String(20), default=ContentStatus.DRAFT, nullable=False, index=True)
    body = db.Column(db.JSON, nullable=False)  # {"format": "markdown", "body": "..."}
    solution_text = db.Column(db.JSON, nullable=False)  # shown after answering
    recommended_time_seconds = db.Column(db.Integer, nullable=True)
    question_metadata = db.Column(db.JSON, default=dict)

    answers = db.relationship(
        "Answer", back_populates="question", cascade="all, delete-orphan", order_by="Answer.order"
    )

    def to_dict(self, include_answers: bool = True, reveal_answers: bool = False) -> dict:
        """Secure by default: reveal_answers=False hides is_correct,
        explanation_if_selected, and solution_text — used by the public
        /api/learning/* endpoints before a student has submitted an answer.
        Admin routes and post-submission responses pass reveal_answers=True.
        """
        data = {
            "id": self.id,
            "category_id": self.category_id,
            "lesson_id": self.lesson_id,
            "question_type": self.question_type,
            "difficulty": self.difficulty,
            "status": self.status,
            "body": self.body,
            "solution_text": self.solution_text if reveal_answers else None,
            "recommended_time_seconds": self.recommended_time_seconds,
            "metadata": self.question_metadata or {},
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
        }
        if include_answers:
            data["answers"] = [answer.to_dict(reveal=reveal_answers) for answer in self.answers]
        return data

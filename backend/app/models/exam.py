from app.extensions import db
from app.models.mixins import TimestampMixin


class Exam(db.Model, TimestampMixin):
    __tablename__ = "exams"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text)
    version = db.Column(db.Integer, nullable=False, default=1)
    status = db.Column(db.String(20), nullable=False, default="DRAFT", index=True)
    duration_seconds = db.Column(db.Integer, nullable=False)
    configuration = db.Column(db.JSON, nullable=False, default=dict)
    created_by = db.Column(db.Integer, db.ForeignKey("users.id", ondelete="SET NULL"))

    sections = db.relationship("ExamSection", back_populates="exam", cascade="all, delete-orphan", order_by="ExamSection.display_order")

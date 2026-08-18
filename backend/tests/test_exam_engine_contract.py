import pytest


def test_exam_schema_migration_is_present():
    from pathlib import Path

    migrations = Path(__file__).resolve().parents[1] / "migrations" / "versions"
    assert any("exam_engine_hardening" in path.name for path in migrations.iterdir())


def test_exam_models_importable():
    from app.models.exam import Exam
    from app.models.exam_session import ExamSession
    from app.models.session_question import SessionQuestion
    from app.models.user_answer import UserAnswer

    assert Exam.__tablename__ == "exams"
    assert ExamSession.__tablename__ == "exam_sessions"
    assert SessionQuestion.__tablename__ == "session_questions"
    assert UserAnswer.__tablename__ == "user_answers"

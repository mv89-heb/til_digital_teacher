def test_exam_schema_migrations_are_present():
    from pathlib import Path

    migrations = Path(__file__).resolve().parents[1] / "migrations" / "versions"
    names = {path.name for path in migrations.iterdir()}
    assert any("exam_engine_hardening" in name for name in names)
    assert any("exam_engine_integrity_fix" in name for name in names)


def test_exam_models_importable():
    from app.models.exam import Exam
    from app.models.exam_session import ExamSession
    from app.models.question_version import QuestionVersion
    from app.models.session_question import SessionQuestion
    from app.models.user_answer import UserAnswer

    assert Exam.__tablename__ == "exams"
    assert ExamSession.__tablename__ == "exam_sessions"
    assert QuestionVersion.__tablename__ == "question_versions"
    assert SessionQuestion.__tablename__ == "session_questions"
    assert UserAnswer.__tablename__ == "user_answers"


def test_immutable_answer_snapshot_fields_exist():
    from app.models.question_version import QuestionVersion
    from app.models.session_question import SessionQuestion

    assert "answer_snapshot" in QuestionVersion.__table__.columns
    assert "answer_snapshot" in SessionQuestion.__table__.columns


def test_session_question_has_final_answer_uniqueness_contract():
    from pathlib import Path

    migration = Path(__file__).resolve().parents[1] / "migrations" / "versions" / "20260818_exam_engine_integrity_fix.py"
    source = migration.read_text(encoding="utf-8")
    assert "uq_user_answers_one_final" in source

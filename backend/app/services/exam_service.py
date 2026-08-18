from datetime import datetime, timedelta, timezone
from decimal import Decimal

from sqlalchemy.exc import IntegrityError

from app.extensions import db
from app.models.answer import Answer
from app.models.exam import Exam
from app.models.exam_event import ExamEvent
from app.models.exam_question_pool import ExamQuestionPool
from app.models.exam_result import ExamResult
from app.models.exam_section import ExamSection
from app.models.exam_session import ExamSession
from app.models.question_version import QuestionVersion
from app.models.session_question import SessionQuestion
from app.models.user_answer import UserAnswer
from app.utils.exceptions import AppError


ACTIVE_SESSION_STATUSES = ("CREATED", "IN_PROGRESS", "PAUSED")


class ExamService:
    """Server-authoritative exam lifecycle and scoring service."""

    @staticmethod
    def start_session(user_id: int, exam_id: int) -> ExamSession:
        exam = db.session.get(Exam, exam_id)
        if not exam or exam.status != "PUBLISHED":
            raise AppError("Exam not found", status_code=404)

        existing = (
            ExamSession.query.filter(
                ExamSession.user_id == user_id,
                ExamSession.exam_id == exam_id,
                ExamSession.status.in_(ACTIVE_SESSION_STATUSES),
            )
            .order_by(ExamSession.created_at.desc())
            .first()
        )
        if existing:
            return existing

        now = datetime.now(timezone.utc)
        session = ExamSession(
            user_id=user_id,
            exam_id=exam.id,
            exam_version=exam.version,
            status="IN_PROGRESS",
            started_at=now,
            expires_at=now + timedelta(seconds=exam.duration_seconds),
            last_activity_at=now,
        )
        db.session.add(session)
        db.session.flush()

        pools = (
            ExamQuestionPool.query.join(ExamSection)
            .filter(ExamSection.exam_id == exam.id)
            .order_by(ExamSection.display_order, ExamQuestionPool.display_order, ExamQuestionPool.id)
            .all()
        )
        if not pools:
            db.session.rollback()
            raise AppError("Exam has no questions", status_code=422)

        for index, pool in enumerate(pools):
            version = db.session.get(QuestionVersion, pool.question_version_id)
            if not version:
                db.session.rollback()
                raise AppError("Exam contains a missing question version", status_code=422)
            db.session.add(
                SessionQuestion(
                    session_id=session.id,
                    question_id=pool.question_id,
                    question_version_id=pool.question_version_id,
                    section_id=pool.exam_section_id,
                    sequence_number=index,
                    weight=pool.weight,
                    answer_snapshot=version.answer_snapshot or [],
                )
            )
        try:
            db.session.commit()
        except IntegrityError:
            db.session.rollback()
            raise AppError("Could not create exam session", status_code=409)
        return session

    @staticmethod
    def get_session_for_user(user_id: int, session_id: int) -> ExamSession:
        session = db.session.get(ExamSession, session_id)
        if not session or session.user_id != user_id:
            raise AppError("Exam session not found", status_code=404)
        return session

    @staticmethod
    def mark_question_viewed(user_id: int, session_id: int, session_question_id: int) -> SessionQuestion:
        session = ExamService.get_session_for_user(user_id, session_id)
        ExamService._ensure_active(session)
        sq = db.session.get(SessionQuestion, session_question_id)
        if not sq or sq.session_id != session.id:
            raise AppError("Session question not found", status_code=404)
        now = datetime.now(timezone.utc)
        if sq.first_seen_at is None:
            sq.first_seen_at = now
        sq.last_seen_at = now
        session.last_activity_at = now
        db.session.add(
            ExamEvent(
                session_id=session.id,
                session_question_id=sq.id,
                event_type="QUESTION_VIEWED",
                elapsed_ms=max(0, int((now - session.started_at).total_seconds() * 1000)) if session.started_at else None,
            )
        )
        db.session.commit()
        return sq

    @staticmethod
    def submit_answer(
        user_id: int,
        session_id: int,
        session_question_id: int,
        answer_id: int,
        elapsed_ms: int | None = None,
    ) -> UserAnswer:
        session = ExamService.get_session_for_user(user_id, session_id)
        ExamService._ensure_active(session)
        sq = db.session.get(SessionQuestion, session_question_id)
        if not sq or sq.session_id != session.id:
            raise AppError("Session question not found", status_code=404)

        snapshot = sq.answer_snapshot or []
        selected = next((item for item in snapshot if int(item.get("id")) == answer_id), None)
        if selected is None:
            # The answer must belong to the immutable session snapshot, not merely
            # the current mutable question row.
            raise AppError("Answer is not part of this exam question", status_code=422)

        now = datetime.now(timezone.utc)
        response_time = max(0, int(elapsed_ms or 0))
        if sq.last_seen_at:
            response_time = max(response_time, 0)
        response_time = min(response_time, max(0, int((session.expires_at - session.started_at).total_seconds() * 1000)))

        previous_final = UserAnswer.query.filter_by(session_question_id=sq.id, is_final=True).first()
        if previous_final:
            previous_final.is_final = False

        correct = bool(selected.get("is_correct"))
        ua = UserAnswer(
            session_question_id=sq.id,
            answer_id=answer_id,
            is_final=True,
            is_correct=correct,
            answered_at=now,
            response_time_ms=response_time,
            score=Decimal(str(sq.weight if correct else 0)),
        )
        db.session.add(ua)
        sq.status = "ANSWERED"
        sq.answered_at = now
        sq.last_seen_at = now
        sq.total_time_ms += response_time
        session.last_activity_at = now
        db.session.add(
            ExamEvent(
                session_id=session.id,
                session_question_id=sq.id,
                event_type="ANSWER_SUBMITTED",
                elapsed_ms=response_time,
                metadata_json={"answer_id": answer_id, "is_correct": correct},
            )
        )
        try:
            db.session.commit()
        except IntegrityError:
            db.session.rollback()
            raise AppError("Could not save answer", status_code=409)
        return ua

    @staticmethod
    def submit_session(user_id: int, session_id: int, expired: bool = False) -> ExamResult:
        session = ExamService.get_session_for_user(user_id, session_id)
        return ExamService._finalize(session, expired=expired)

    @staticmethod
    def _finalize(session: ExamSession, expired: bool = False) -> ExamResult:
        if session.status in ("SUBMITTED", "EXPIRED"):
            result = ExamResult.query.filter_by(session_id=session.id).first()
            if result:
                return result

        now = datetime.now(timezone.utc)
        session.status = "EXPIRED" if expired or (session.expires_at and now >= session.expires_at) else "SUBMITTED"
        session.submitted_at = now
        session.last_activity_at = now

        questions = SessionQuestion.query.filter_by(session_id=session.id).all()
        total = len(questions)
        answered = 0
        correct = 0
        skipped = 0
        raw = Decimal("0")
        weighted = Decimal("0")
        total_time = 0

        for sq in questions:
            final = UserAnswer.query.filter_by(session_question_id=sq.id, is_final=True).first()
            total_time += sq.total_time_ms
            if final:
                answered += 1
                if final.is_correct:
                    correct += 1
                    raw += Decimal("1")
                    weighted += Decimal(str(sq.weight))
            else:
                skipped += 1
                sq.status = "SKIPPED"

        result = ExamResult(
            session_id=session.id,
            user_id=session.user_id,
            exam_id=session.exam_id,
            raw_score=raw,
            weighted_score=weighted,
            total_questions=total,
            answered_questions=answered,
            correct_answers=correct,
            skipped_questions=skipped,
            total_time_ms=total_time,
            metadata={"expired": session.status == "EXPIRED"},
        )
        db.session.add(result)
        try:
            db.session.commit()
        except IntegrityError:
            db.session.rollback()
            existing = ExamResult.query.filter_by(session_id=session.id).first()
            if existing:
                return existing
            raise AppError("Could not finalize exam", status_code=409)
        return result

    @staticmethod
    def _ensure_active(session: ExamSession) -> None:
        if session.status not in ACTIVE_SESSION_STATUSES:
            raise AppError("Exam session is not active", status_code=409)
        now = datetime.now(timezone.utc)
        if session.expires_at and now >= session.expires_at:
            ExamService._finalize(session, expired=True)
            raise AppError("Exam time has expired", status_code=409)

    @staticmethod
    def serialize_session(session: ExamSession) -> dict:
        questions = (
            SessionQuestion.query.filter_by(session_id=session.id)
            .order_by(SessionQuestion.sequence_number)
            .all()
        )
        serialized_questions = []
        for q in questions:
            version = db.session.get(QuestionVersion, q.question_version_id)
            serialized_questions.append(
                {
                    "id": q.id,
                    "question_id": q.question_id,
                    "question_version_id": q.question_version_id,
                    "section_id": q.section_id,
                    "sequence_number": q.sequence_number,
                    "status": q.status,
                    "total_time_ms": q.total_time_ms,
                    "prompt": version.body if version else {},
                    "visual_data": version.question_metadata.get("visual_data") if version and version.question_metadata else None,
                    "question_type": version.question_type if version else None,
                    "difficulty": version.difficulty if version else None,
                    "solution": None,
                    "answers": [
                        {
                            "id": item.get("id"),
                            "answer_text": item.get("answer_text"),
                            "order": item.get("order", 0),
                        }
                        for item in (q.answer_snapshot or [])
                    ],
                }
            )
        return {
            "id": session.id,
            "exam_id": session.exam_id,
            "status": session.status,
            "started_at": session.started_at.isoformat() if session.started_at else None,
            "expires_at": session.expires_at.isoformat() if session.expires_at else None,
            "current_question_index": session.current_question_index,
            "questions": serialized_questions,
        }

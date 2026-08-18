from datetime import datetime, timezone
from decimal import Decimal

from sqlalchemy.exc import IntegrityError

from app.extensions import db
from app.models.exam_event import ExamEvent
from app.models.exam_section import ExamSection
from app.models.exam_session import ExamSession
from app.models.session_question import SessionQuestion
from app.models.user_answer import UserAnswer
from app.services.exam_service import ExamService
from app.utils.exceptions import AppError


class ExamAnswerService:
    """Secure answer submission using server-observed timing only.

    The browser is never trusted for response time. The authoritative duration
    is measured from the latest QUESTION_VIEWED event to the answer request.
    Repeating the exact same final answer is idempotent.
    """

    @staticmethod
    def submit(user_id: int, session_id: int, session_question_id: int, answer_id: int) -> UserAnswer:
        session = ExamService.get_session_for_user(user_id, session_id)
        ExamService._ensure_active(session)

        sq = (
            SessionQuestion.query.filter_by(id=session_question_id, session_id=session.id)
            .with_for_update()
            .first()
        )
        if not sq:
            raise AppError("Session question not found", status_code=404)

        ExamService._assert_current_section(session, sq)

        snapshot = sq.answer_snapshot or []
        selected = next((item for item in snapshot if int(item.get("id")) == answer_id), None)
        if selected is None:
            raise AppError("Answer is not part of this exam question", status_code=422)

        # Same final answer = safe retry. Do not create another answer row.
        previous_final = UserAnswer.query.filter_by(
            session_question_id=sq.id,
            is_final=True,
        ).first()
        if previous_final and previous_final.answer_id == answer_id:
            return previous_final

        now = datetime.now(timezone.utc)
        last_view = (
            ExamEvent.query.filter_by(
                session_id=session.id,
                session_question_id=sq.id,
                event_type="QUESTION_VIEWED",
            )
            .order_by(ExamEvent.event_timestamp.desc(), ExamEvent.id.desc())
            .first()
        )

        if last_view and last_view.event_timestamp:
            response_time_ms = max(
                0,
                int((now - last_view.event_timestamp).total_seconds() * 1000),
            )
        elif sq.first_seen_at:
            response_time_ms = max(
                0,
                int((now - sq.first_seen_at).total_seconds() * 1000),
            )
        else:
            # No server-side view event means the client cannot establish a
            # legitimate response interval. Record zero rather than trusting it.
            response_time_ms = 0

        # Never allow a question's measured time to exceed the active section.
        sections = ExamSection.query.filter_by(exam_id=session.exam_id).order_by(
            ExamSection.display_order
        ).all()
        current_index = int((session.state or {}).get("current_section_index", 0))
        section_started = ExamService._current_section_started(session)
        if current_index < len(sections):
            section_elapsed_ms = max(
                0,
                int((now - section_started).total_seconds() * 1000),
            )
            response_time_ms = min(response_time_ms, section_elapsed_ms)

        if previous_final:
            previous_final.is_final = False

        correct = bool(selected.get("is_correct"))
        answer = UserAnswer(
            session_question_id=sq.id,
            answer_id=answer_id,
            is_final=True,
            is_correct=correct,
            answered_at=now,
            response_time_ms=response_time_ms,
            score=Decimal(str(sq.weight if correct else 0)),
        )
        db.session.add(answer)

        sq.status = "ANSWERED"
        sq.answered_at = now
        sq.last_seen_at = now
        sq.total_time_ms += response_time_ms
        session.last_activity_at = now

        db.session.add(
            ExamEvent(
                session_id=session.id,
                session_question_id=sq.id,
                event_type="ANSWER_SUBMITTED",
                elapsed_ms=response_time_ms,
                metadata_json={
                    "answer_id": answer_id,
                    "timing_source": "server_question_view_event",
                },
            )
        )

        try:
            db.session.commit()
        except IntegrityError:
            db.session.rollback()
            # A concurrent duplicate retry can safely return the final answer
            # that won the race.
            existing = UserAnswer.query.filter_by(
                session_question_id=sq.id,
                answer_id=answer_id,
                is_final=True,
            ).first()
            if existing:
                return existing
            raise AppError("Could not save answer", status_code=409)

        return answer

from datetime import datetime, timedelta, timezone
from decimal import Decimal

from sqlalchemy.exc import IntegrityError

from app.extensions import db
from app.models.constants import ContentStatus
from app.models.exam import Exam
from app.models.exam_event import ExamEvent
from app.models.exam_question_pool import ExamQuestionPool
from app.models.exam_result import ExamResult
from app.models.exam_result_category import ExamResultCategory
from app.models.exam_section import ExamSection
from app.models.exam_session import ExamSession
from app.models.question import Question
from app.models.question_version import QuestionVersion
from app.models.session_question import SessionQuestion
from app.models.user_answer import UserAnswer
from app.utils.exceptions import AppError


ACTIVE_SESSION_STATUSES = ("CREATED", "IN_PROGRESS", "PAUSED")
DEFAULT_TARGET_TIME_MS = 45_000


class ExamService:
    """Server-authoritative exam lifecycle, section state machine and scoring."""

    @staticmethod
    def create_exam(admin_user_id: int, data: dict) -> Exam:
        sections = data.get("sections") or []
        if not sections:
            raise AppError("Exam must contain at least one section", status_code=422)

        total_duration = sum(int(s.get("duration_seconds") or 0) for s in sections)
        requested_duration = int(data.get("duration_seconds") or 0)
        if total_duration <= 0 and requested_duration <= 0:
            raise AppError("Exam must have section durations or a total duration", status_code=422)
        if total_duration <= 0:
            raise AppError("Each simulation section must define duration_seconds", status_code=422)

        exam = Exam(
            name=data["name"],
            description=data.get("description"),
            duration_seconds=total_duration,
            configuration=data.get("configuration") or {},
            created_by=admin_user_id,
            status="DRAFT",
            version=1,
        )
        db.session.add(exam)
        db.session.flush()

        seen_questions = set()
        for section_index, section_data in enumerate(sections):
            duration = int(section_data.get("duration_seconds") or 0)
            if duration <= 0:
                raise AppError(f"Section {section_index + 1} must have a positive duration", status_code=422)

            section = ExamSection(
                exam_id=exam.id,
                name=section_data["name"],
                category=section_data["category"],
                display_order=section_data.get("display_order", section_index),
                duration_seconds=duration,
                question_count=section_data.get("question_count"),
                instructions=section_data.get("instructions"),
                scoring_configuration=section_data.get("scoring_configuration") or {},
            )
            db.session.add(section)
            db.session.flush()

            question_ids = section_data.get("question_ids") or []
            if section.question_count is not None and int(section.question_count) != len(question_ids):
                raise AppError(f"Section {section.name} question_count does not match question_ids", status_code=422)

            for question_index, question_id in enumerate(question_ids):
                if question_id in seen_questions:
                    raise AppError("A question cannot appear twice in the same exam", status_code=422)
                seen_questions.add(question_id)
                question = db.session.get(Question, question_id)
                if not question or question.status != ContentStatus.PUBLISHED:
                    raise AppError(f"Question {question_id} is not published", status_code=422)
                version = (
                    QuestionVersion.query.filter_by(question_id=question.id, status=ContentStatus.PUBLISHED)
                    .order_by(QuestionVersion.version_number.desc())
                    .first()
                )
                if not version:
                    raise AppError(f"Question {question_id} has no published version", status_code=422)
                db.session.add(
                    ExamQuestionPool(
                        exam_section_id=section.id,
                        question_id=question.id,
                        question_version_id=version.id,
                        weight=section_data.get("weights", {}).get(str(question_id), 1),
                        display_order=question_index,
                        is_required=True,
                    )
                )

        db.session.commit()
        return exam

    @staticmethod
    def publish_exam(exam_id: int) -> Exam:
        exam = db.session.get(Exam, exam_id)
        if not exam:
            raise AppError("Exam not found", status_code=404)
        sections = ExamSection.query.filter_by(exam_id=exam.id).order_by(ExamSection.display_order).all()
        if not sections:
            raise AppError("Exam has no sections", status_code=422)
        if any(not s.duration_seconds or s.duration_seconds <= 0 for s in sections):
            raise AppError("Every exam section must have a positive duration", status_code=422)
        pool_count = ExamQuestionPool.query.join(ExamSection).filter(ExamSection.exam_id == exam.id).count()
        if pool_count == 0:
            raise AppError("Exam has no questions", status_code=422)
        exam.duration_seconds = sum(s.duration_seconds for s in sections)
        exam.status = "PUBLISHED"
        exam.version += 1
        db.session.commit()
        return exam

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

        sections = ExamSection.query.filter_by(exam_id=exam.id).order_by(ExamSection.display_order).all()
        if not sections:
            raise AppError("Exam has no sections", status_code=422)

        now = datetime.now(timezone.utc)
        session = ExamSession(
            user_id=user_id,
            exam_id=exam.id,
            exam_version=exam.version,
            status="IN_PROGRESS",
            started_at=now,
            expires_at=now + timedelta(seconds=exam.duration_seconds),
            last_activity_at=now,
            state={
                "current_section_index": 0,
                "section_started_at": now.isoformat(),
                "completed_section_indices": [],
                "locked_before_section_index": 0,
            },
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
    def advance_section(user_id: int, session_id: int) -> ExamSession:
        session = ExamService.get_session_for_user(user_id, session_id)
        ExamService._ensure_active(session, allow_section_advance=False)
        sections = ExamService._sections(session.exam_id)
        state = dict(session.state or {})
        current_index = int(state.get("current_section_index", 0))
        current_started = ExamService._parse_iso(state.get("section_started_at")) or session.started_at
        current = sections[current_index]
        now = datetime.now(timezone.utc)
        elapsed = max(0, int((now - current_started).total_seconds() * 1000))
        remaining = max(0, int(current.duration_seconds * 1000) - elapsed)

        # Manual transition is allowed only after the section timer has expired.
        if remaining > 0:
            raise AppError("The current section is still active", status_code=409)
        return ExamService._advance_expired_section(session, now=now)

    @staticmethod
    def mark_question_viewed(user_id: int, session_id: int, session_question_id: int) -> SessionQuestion:
        session = ExamService.get_session_for_user(user_id, session_id)
        ExamService._ensure_active(session)
        sq = db.session.get(SessionQuestion, session_question_id)
        if not sq or sq.session_id != session.id:
            raise AppError("Session question not found", status_code=404)
        ExamService._assert_current_section(session, sq)

        now = datetime.now(timezone.utc)
        if sq.first_seen_at is None:
            sq.first_seen_at = now
        sq.last_seen_at = now
        session.last_activity_at = now
        db.session.add(ExamEvent(
            session_id=session.id,
            session_question_id=sq.id,
            event_type="QUESTION_VIEWED",
            elapsed_ms=max(0, int((now - session.started_at).total_seconds() * 1000)) if session.started_at else None,
        ))
        db.session.commit()
        return sq

    @staticmethod
    def submit_answer(user_id: int, session_id: int, session_question_id: int, answer_id: int, elapsed_ms: int | None = None) -> UserAnswer:
        session = ExamService.get_session_for_user(user_id, session_id)
        ExamService._ensure_active(session)
        sq = db.session.get(SessionQuestion, session_question_id)
        if not sq or sq.session_id != session.id:
            raise AppError("Session question not found", status_code=404)
        ExamService._assert_current_section(session, sq)

        snapshot = sq.answer_snapshot or []
        selected = next((item for item in snapshot if int(item.get("id")) == answer_id), None)
        if selected is None:
            raise AppError("Answer is not part of this exam question", status_code=422)

        now = datetime.now(timezone.utc)
        current_started = ExamService._current_section_started(session)
        section_elapsed_ms = max(0, int((now - current_started).total_seconds() * 1000))
        response_time = max(0, int(elapsed_ms or 0))
        response_time = min(response_time, section_elapsed_ms)

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
        db.session.add(ExamEvent(
            session_id=session.id,
            session_question_id=sq.id,
            event_type="ANSWER_SUBMITTED",
            elapsed_ms=response_time,
            metadata_json={"answer_id": answer_id},
        ))
        try:
            db.session.commit()
        except IntegrityError:
            db.session.rollback()
            raise AppError("Could not save answer", status_code=409)
        return ua

    @staticmethod
    def submit_session(user_id: int, session_id: int) -> ExamResult:
        session = ExamService.get_session_for_user(user_id, session_id)
        return ExamService._finalize(session)

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
        answered = correct = skipped = 0
        raw = Decimal("0")
        weighted = Decimal("0")
        total_time = 0
        by_category = {}

        section_map = {s.id: s for s in ExamService._sections(session.exam_id)}
        for sq in questions:
            final = UserAnswer.query.filter_by(session_question_id=sq.id, is_final=True).first()
            total_time += sq.total_time_ms
            category = section_map.get(sq.section_id).category if section_map.get(sq.section_id) else "general"
            stats = by_category.setdefault(category, {"total": 0, "answered": 0, "correct": 0, "raw": Decimal("0"), "weighted": Decimal("0"), "time": 0})
            stats["total"] += 1
            stats["time"] += sq.total_time_ms

            if final:
                answered += 1
                stats["answered"] += 1
                if final.is_correct:
                    correct += 1
                    stats["correct"] += 1
                    raw += Decimal("1")
                    stats["raw"] += Decimal("1")
                    weighted += Decimal(str(sq.weight))
                    stats["weighted"] += Decimal(str(sq.weight))
            else:
                skipped += 1
                sq.status = "SKIPPED"

        normalized, category_scores = ExamService._calculate_scaled_scores(by_category, session.exam_id)
        result = ExamResult(
            session_id=session.id,
            user_id=session.user_id,
            exam_id=session.exam_id,
            raw_score=raw,
            weighted_score=weighted,
            normalized_score=normalized,
            total_questions=total,
            answered_questions=answered,
            correct_answers=correct,
            skipped_questions=skipped,
            total_time_ms=total_time,
            metadata_json={
                "expired": session.status == "EXPIRED",
                "scoring_version": "teil-sim-v1",
                "category_scores": category_scores,
            },
        )
        db.session.add(result)
        db.session.flush()

        for category, stats in by_category.items():
            accuracy = Decimal(stats["correct"]) / Decimal(stats["total"]) if stats["total"] else Decimal("0")
            avg_time = int(stats["time"] / stats["answered"]) if stats["answered"] else None
            db.session.add(ExamResultCategory(
                result_id=result.id,
                category=category,
                total_questions=stats["total"],
                answered_questions=stats["answered"],
                correct_answers=stats["correct"],
                raw_score=stats["raw"],
                weighted_score=stats["weighted"],
                accuracy=accuracy,
                total_time_ms=stats["time"],
                average_time_ms=avg_time,
            ))

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
    def _calculate_scaled_scores(by_category: dict, exam_id: int) -> tuple[Decimal, dict]:
        """Simulation score, deliberately not claimed to reproduce a proprietary real-world calibration."""
        sections = ExamService._sections(exam_id)
        category_configs = {s.category: (s.scoring_configuration or {}) for s in sections}
        weighted_indices = []
        category_scores = {}

        for category, stats in by_category.items():
            total = max(1, stats["total"])
            accuracy = float(stats["correct"] / total)
            completion = float(stats["answered"] / total)
            avg_ms = (stats["time"] / stats["answered"]) if stats["answered"] else DEFAULT_TARGET_TIME_MS * 1.5
            target_ms = int(category_configs.get(category, {}).get("target_time_ms", DEFAULT_TARGET_TIME_MS))
            speed_score = max(0.0, min(1.0, target_ms / max(target_ms, avg_ms)))
            performance = (0.80 * accuracy) + (0.10 * completion) + (0.10 * speed_score)
            scaled = Decimal(str(round(200 + 600 * max(0.0, min(1.0, performance)), 2)))
            category_scores[category] = {
                "score": float(scaled),
                "accuracy": round(accuracy * 100, 2),
                "completion": round(completion * 100, 2),
                "average_time_ms": int(avg_ms) if stats["answered"] else None,
            }
            category_weight = float(category_configs.get(category, {}).get("score_weight", 1.0))
            weighted_indices.append((performance, category_weight))

        if not weighted_indices:
            return Decimal("200"), category_scores
        numerator = sum(index * weight for index, weight in weighted_indices)
        denominator = sum(weight for _, weight in weighted_indices) or 1.0
        overall = max(0.0, min(1.0, numerator / denominator))
        return Decimal(str(round(200 + 600 * overall, 2))), category_scores

    @staticmethod
    def _ensure_active(session: ExamSession, allow_section_advance: bool = True) -> None:
        if session.status not in ACTIVE_SESSION_STATUSES:
            raise AppError("Exam session is not active", status_code=409)

        now = datetime.now(timezone.utc)
        if session.expires_at and now >= session.expires_at:
            ExamService._finalize(session, expired=True)
            raise AppError("Exam time has expired", status_code=409)

        ExamService._sync_section_timer(session, now=now, persist=True)

    @staticmethod
    def _sync_section_timer(session: ExamSession, now: datetime, persist: bool = True) -> None:
        sections = ExamService._sections(session.exam_id)
        state = dict(session.state or {})
        current_index = int(state.get("current_section_index", 0))
        if current_index >= len(sections):
            ExamService._finalize(session)
            return

        started = ExamService._parse_iso(state.get("section_started_at")) or session.started_at
        while current_index < len(sections):
            duration = timedelta(seconds=sections[current_index].duration_seconds or 0)
            if now < started + duration:
                break
            completed = list(state.get("completed_section_indices") or [])
            if current_index not in completed:
                completed.append(current_index)
            current_index += 1
            if current_index >= len(sections):
                session.state = {**state, "current_section_index": current_index, "completed_section_indices": completed, "locked_before_section_index": current_index}
                if persist:
                    ExamService._finalize(session, expired=True)
                return
            started = now
            state = {
                **state,
                "current_section_index": current_index,
                "section_started_at": started.isoformat(),
                "completed_section_indices": completed,
                "locked_before_section_index": current_index,
            }

        session.state = state
        session.current_question_index = ExamService._first_question_index_for_section(session, current_index)
        if persist:
            session.last_activity_at = now
            db.session.commit()

    @staticmethod
    def _advance_expired_section(session: ExamSession, now: datetime) -> ExamSession:
        ExamService._sync_section_timer(session, now=now, persist=True)
        return session

    @staticmethod
    def _assert_current_section(session: ExamSession, sq: SessionQuestion) -> None:
        sections = ExamService._sections(session.exam_id)
        current_index = int((session.state or {}).get("current_section_index", 0))
        if current_index >= len(sections) or sq.section_id != sections[current_index].id:
            raise AppError("This section is locked. Previous sections cannot be revisited.", status_code=409)

    @staticmethod
    def _current_section_started(session: ExamSession) -> datetime:
        return ExamService._parse_iso((session.state or {}).get("section_started_at")) or session.started_at

    @staticmethod
    def _sections(exam_id: int):
        return ExamSection.query.filter_by(exam_id=exam_id).order_by(ExamSection.display_order).all()

    @staticmethod
    def _first_question_index_for_section(session: ExamSession, section_index: int) -> int:
        sections = ExamService._sections(session.exam_id)
        if section_index >= len(sections):
            return 0
        section_id = sections[section_index].id
        q = (
            SessionQuestion.query.filter_by(session_id=session.id, section_id=section_id)
            .order_by(SessionQuestion.sequence_number)
            .first()
        )
        return q.sequence_number if q else 0

    @staticmethod
    def _parse_iso(value):
        if not value:
            return None
        try:
            parsed = datetime.fromisoformat(value)
            return parsed if parsed.tzinfo else parsed.replace(tzinfo=timezone.utc)
        except (TypeError, ValueError):
            return None

    @staticmethod
    def serialize_session(session: ExamSession) -> dict:
        ExamService._ensure_active(session)
        sections = ExamService._sections(session.exam_id)
        state = dict(session.state or {})
        current_index = int(state.get("current_section_index", 0))
        section_started = ExamService._current_section_started(session)
        current_section_expires = None
        if current_index < len(sections):
            current_section_expires = section_started + timedelta(seconds=sections[current_index].duration_seconds)

        questions = SessionQuestion.query.filter_by(session_id=session.id).order_by(SessionQuestion.sequence_number).all()
        serialized_questions = []
        for q in questions:
            version = db.session.get(QuestionVersion, q.question_version_id)
            serialized_questions.append({
                "id": q.id,
                "question_id": q.question_id,
                "question_version_id": q.question_version_id,
                "section_id": q.section_id,
                "sequence_number": q.sequence_number,
                "status": q.status,
                "total_time_ms": q.total_time_ms,
                "prompt": version.body if version else {},
                "visual_data": (version.question_metadata or {}).get("visual_data") if version else None,
                "question_type": version.question_type if version else None,
                "difficulty": version.difficulty if version else None,
                "solution": None,
                "answers": [
                    {"id": item.get("id"), "answer_text": item.get("answer_text"), "order": item.get("order", 0)}
                    for item in (q.answer_snapshot or [])
                ],
            })

        return {
            "id": session.id,
            "exam_id": session.exam_id,
            "status": session.status,
            "started_at": session.started_at.isoformat() if session.started_at else None,
            "expires_at": session.expires_at.isoformat() if session.expires_at else None,
            "current_question_index": session.current_question_index,
            "current_section_index": current_index,
            "section_started_at": section_started.isoformat() if section_started else None,
            "current_section_expires_at": current_section_expires.isoformat() if current_section_expires else None,
            "locked_before_section_index": int(state.get("locked_before_section_index", current_index)),
            "completed_section_indices": list(state.get("completed_section_indices") or []),
            "sections": [
                {
                    "id": s.id,
                    "name": s.name,
                    "category": s.category,
                    "display_order": s.display_order,
                    "duration_seconds": s.duration_seconds,
                    "question_count": s.question_count,
                    "instructions": s.instructions,
                    "scoring_configuration": s.scoring_configuration or {},
                    "locked": i < current_index,
                    "active": i == current_index,
                }
                for i, s in enumerate(sections)
            ],
            "questions": serialized_questions,
        }

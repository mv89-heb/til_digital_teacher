from datetime import datetime, timezone

from sqlalchemy import or_

from app.extensions import db
from app.models.teacher_feedback import TeacherFeedback


class TeacherMemoryService:
    """Persistent memory for the local teacher.

    Only approved records influence teaching. Student submissions are pending
    until an administrator approves them, preventing arbitrary user text from
    becoming authoritative teaching knowledge.
    """

    @staticmethod
    def _tokens(text: str) -> list[str]:
        return [token.strip() for token in (text or '').split() if len(token.strip()) >= 2][:10]

    @classmethod
    def retrieve(cls, *, query: str, topic: str | None = None,
                 subcategory: str | None = None, skill: str | None = None,
                 question_id: int | None = None, limit: int = 8):
        filters = [TeacherFeedback.status == 'approved']

        if topic:
            filters.append(TeacherFeedback.topic.ilike(f'%{topic}%'))
        if subcategory:
            filters.append(TeacherFeedback.subcategory.ilike(f'%{subcategory}%'))
        if skill:
            filters.append(TeacherFeedback.skill.ilike(f'%{skill}%'))
        if question_id is not None:
            filters.append(TeacherFeedback.question_id == question_id)

        tokens = cls._tokens(query)
        text_conditions = []
        for token in tokens:
            pattern = f'%{token}%'
            text_conditions.extend([
                TeacherFeedback.student_query.ilike(pattern),
                TeacherFeedback.feedback.ilike(pattern),
                TeacherFeedback.correction.ilike(pattern),
                TeacherFeedback.topic.ilike(pattern),
                TeacherFeedback.subcategory.ilike(pattern),
                TeacherFeedback.skill.ilike(pattern),
            ])

        q = TeacherFeedback.query.filter(*filters)
        if text_conditions:
            q = q.filter(or_(*text_conditions))

        return (
            q.order_by(
                TeacherFeedback.confidence.desc(),
                TeacherFeedback.times_used.desc(),
                TeacherFeedback.updated_at.desc(),
            )
            .limit(max(1, min(limit, 20)))
            .all()
        )

    @staticmethod
    def context(items: list[TeacherFeedback]) -> list[dict]:
        return [
            {
                'id': item.id,
                'topic': item.topic,
                'subcategory': item.subcategory,
                'skill': item.skill,
                'error_type': item.error_type,
                'severity': item.severity,
                'correction': item.correction,
                'correct_answer': item.correct_answer,
                'confidence': item.confidence,
            }
            for item in items
        ]

    @staticmethod
    def record(*, user_id: int, payload: dict) -> TeacherFeedback:
        required = ('student_query', 'feedback', 'correction')
        missing = [name for name in required if not str(payload.get(name) or '').strip()]
        if missing:
            raise ValueError(f'Missing required fields: {", ".join(missing)}')

        item = TeacherFeedback(
            user_id=user_id,
            question_id=payload.get('question_id'),
            topic=payload.get('topic'),
            subcategory=payload.get('subcategory'),
            skill=payload.get('skill'),
            student_query=str(payload.get('student_query')).strip(),
            original_answer=payload.get('original_answer'),
            feedback=str(payload.get('feedback')).strip(),
            correction=str(payload.get('correction')).strip(),
            correct_answer=payload.get('correct_answer'),
            error_type=payload.get('error_type'),
            severity=payload.get('severity') or 'medium',
            source=payload.get('source') or 'student',
            status='pending',
            confidence=50,
        )
        db.session.add(item)
        db.session.commit()
        return item

    @staticmethod
    def review(item_id: int, *, approved: bool, confidence: int | None = None) -> TeacherFeedback:
        item = TeacherFeedback.query.get_or_404(item_id)
        item.status = 'approved' if approved else 'rejected'
        if approved:
            item.confidence = max(80, min(100, confidence if confidence is not None else item.confidence))
        db.session.commit()
        return item

    @staticmethod
    def mark_used(items: list[TeacherFeedback]) -> None:
        if not items:
            return
        now = datetime.now(timezone.utc)
        for item in items:
            item.times_used += 1
            item.last_used_at = now
        db.session.commit()

    @classmethod
    def apply_to_local_answer(cls, answer: str, items: list[TeacherFeedback], *, mode: str) -> str:
        """Apply approved memory to the deterministic teacher without an LLM.

        Memory never replaces the canonical answer. It adds explicit teaching
        corrections and adapts the explanation style for the current session.
        """
        if not items:
            return answer

        unique = []
        seen = set()
        for item in items:
            key = (item.correction or '').strip()
            if key and key not in seen:
                seen.add(key)
                unique.append(item)

        if not unique:
            return answer

        lines = ['\n\nהתאמות הוראה שנלמדו ממשוב קודם:']
        for item in unique[:3]:
            lines.append(f'• {item.correction}')

        if mode == 'guided':
            lines.append('• במצב פתרון מודרך: נסה קודם לנסח את הכלל בעצמך לפני המעבר לפתרון מלא.')
        elif mode == 'practice':
            lines.append('• במצב תרגול: נשתמש בכלל הזה כשנבדוק את התשובה שלך.')
        elif mode == 'mistake':
            lines.append('• במצב ניתוח טעות: התמקד במקור הטעות ולא רק בתשובה הסופית.')

        return answer + '\n' + '\n'.join(lines)

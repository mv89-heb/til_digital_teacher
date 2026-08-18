from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Any

from sqlalchemy import String, cast, func, or_

from app.extensions import db
from app.models.category import Category
from app.models.constants import ContentStatus
from app.models.lesson import Lesson
from app.models.question import Question


STOP_WORDS = {
    "איך", "למה", "מה", "זה", "זו", "של", "על", "עם", "את", "אני", "לי", "תן", "תתן", "אפשר", "צריך",
    "רוצה", "ללמוד", "למד", "להסביר", "הסבר", "שאלה", "שאלות", "תרגיל", "תרגילים", "בבקשה", "במערכת",
}

TOPIC_ALIASES = {
    "שברים": {"שברים", "שבר", "fractions", "fraction"},
    "אחוזים": {"אחוזים", "אחוז", "percent", "percentage"},
    "אנלוגיות": {"אנלוגיות", "אנלוגיה", "analogies", "analogy"},
    "השלמת משפטים": {"השלמת משפטים", "השלמת משפט", "sentence completion"},
    "הבנת הנקרא": {"הבנת הנקרא", "הבנת טקסט", "קטע", "reading comprehension"},
    "סיבובים": {"סיבובים", "סיבוב", "rotation", "rotations"},
    "מטריצות": {"מטריצות", "מטריצה", "matrix", "matrices"},
    "קוביות": {"קוביות", "קוביה", "cube", "cubes"},
    "דפוסים": {"דפוסים", "דפוס", "pattern", "patterns"},
    "לוגיקה": {"לוגיקה", "הסקה", "logic", "reasoning"},
    "אנגלית": {"אנגלית", "english", "vocabulary", "grammar"},
}

FUNDAMENTAL_PLAYBOOKS = {
    "שברים": {
        "summary": "שבר מתאר חלק מתוך שלם. המונה מייצג כמה חלקים יש, והמכנה לכמה חלקים שווים השלם חולק.",
        "steps": [
            "זהה אם צריך לחבר, לחסר, לכפול, לחלק או להשוות שברים.",
            "בחיבור ובחיסור: הבא למכנה משותף, ואז חבר או חסר מונים.",
            "בכפל: כופלים מונה במונה ומכנה במכנה, ומצמצמים בסוף.",
            "בחילוק: הופכים את השבר השני וכופלים.",
            "בדוק אם אפשר לצמצם והאם התוצאה הגיונית בגודלה.",
        ],
        "mistakes": [
            "בחיבור שברים לא מחברים מכנים.",
            "לא הופכים את שני השברים בחילוק; הופכים רק את המחלק.",
            "לא מצמצמים חלק מהביטוי באופן שפוגע בשוויון.",
        ],
    },
    "אחוזים": {
        "summary": "אחוז הוא חלק מתוך 100. כדי למצוא x% ממספר, מחשבים את המספר כפול x חלקי 100.",
        "steps": [
            "זהה אם מחפשים את החלק, את האחוז או את השלם.",
            "המר אחוז לשבר מתוך 100 או לעשרוני.",
            "בבעיות שינוי השתמש באחוז השינוי ביחס לערך ההתחלתי.",
            "בדוק האם מדובר בהנחה, התייקרות או אחוז מתוך אחוז.",
        ],
        "mistakes": [
            "בלבול בין אחוז מתוך המקור לאחוז מתוך התוצאה.",
            "שימוש בערך הסופי במקום בערך ההתחלתי בבדיקת שינוי אחוזי.",
        ],
    },
}


@dataclass
class TeacherContext:
    categories: list[dict]
    lessons: list[dict]
    questions: list[dict]
    total_questions: int
    total_lessons: int


class TeacherKnowledgeService:
    """Local, database-backed knowledge retrieval for the non-LLM teacher."""

    @staticmethod
    def _clean(value: Any) -> str:
        if value is None:
            return ""
        if isinstance(value, str):
            return value
        if isinstance(value, dict):
            return str(value.get("body") or value.get("text") or "")
        return ""

    @staticmethod
    def _normalize(value: str) -> str:
        value = (value or "").lower().replace("\u200f", "").replace("\u200e", "")
        value = re.sub(r"[^\w\u0590-\u05ff]+", " ", value, flags=re.UNICODE)
        return re.sub(r"\s+", " ", value).strip()

    @classmethod
    def _tokens(cls, text: str) -> list[str]:
        return [token for token in cls._normalize(text).split() if len(token) > 2 and token not in STOP_WORDS]

    @classmethod
    def resolve_topic(cls, text: str) -> str | None:
        normalized = cls._normalize(text)
        for canonical, aliases in TOPIC_ALIASES.items():
            if any(cls._normalize(alias) in normalized for alias in aliases):
                return canonical
        return None

    @staticmethod
    def _question_payload(question: Question) -> dict:
        metadata = question.question_metadata or {}
        answers = [
            {"id": answer.id, "text": answer.answer_text, "is_correct": answer.is_correct}
            for answer in sorted(question.answers, key=lambda answer: answer.order)
        ]
        return {
            "id": question.id,
            "bank_key": metadata.get("bank_key"),
            "body": TeacherKnowledgeService._clean(question.body),
            "solution_text": TeacherKnowledgeService._clean(question.solution_text),
            "main_category": metadata.get("main_category"),
            "subcategory": metadata.get("subcategory"),
            "skill": metadata.get("skill"),
            "difficulty_level": metadata.get("difficulty_level"),
            "question_type": metadata.get("question_type"),
            "tags": metadata.get("tags", []),
            "visual_data": metadata.get("visual_data") or metadata.get("visual"),
            "answers": answers,
        }

    @classmethod
    def build_context(cls, *, query: str = "", question_id: int | None = None, limit: int = 8) -> TeacherContext:
        tokens = cls._tokens(query)
        topic = cls.resolve_topic(query)

        categories = [
            {"id": row.id, "name": row.name, "slug": row.slug, "parent_id": row.parent_id}
            for row in Category.query.order_by(Category.parent_id.asc(), Category.id.asc()).all()
        ]

        lessons = []
        lesson_query = Lesson.query.filter(Lesson.status == ContentStatus.PUBLISHED)
        if topic:
            topic_tokens = cls._tokens(topic)
            for token in topic_tokens[:3]:
                lesson_query = lesson_query.filter(Lesson.title.ilike(f"%{token}%"))
        for lesson in lesson_query.order_by(Lesson.category_id.asc(), Lesson.order_index.asc(), Lesson.id.asc()).limit(30).all():
            lessons.append({"id": lesson.id, "title": lesson.title, "category_id": lesson.category_id, "slug": lesson.slug})

        question_query = Question.query.filter(Question.status == ContentStatus.PUBLISHED)
        if question_id is not None:
            question_query = question_query.filter(Question.id == question_id)
        elif tokens:
            body_text = cast(Question.body, String)
            metadata_text = cast(Question.question_metadata, String)
            conditions = []
            for token in tokens[:10]:
                pattern = f"%{token}%"
                conditions.extend([body_text.ilike(pattern), metadata_text.ilike(pattern)])
            question_query = question_query.filter(or_(*conditions))
            question_query = question_query.order_by(Question.id.asc())
        else:
            question_query = question_query.order_by(func.random())

        rows = question_query.limit(max(1, min(limit, 20))).all()
        questions = [cls._question_payload(question) for question in rows]

        total_questions = Question.query.filter(Question.status == ContentStatus.PUBLISHED).count()
        total_lessons = Lesson.query.filter(Lesson.status == ContentStatus.PUBLISHED).count()
        return TeacherContext(categories, lessons, questions, total_questions, total_lessons)

    @classmethod
    def teach(cls, query: str, *, question_id: int | None = None, mode: str = "learn") -> dict:
        topic = cls.resolve_topic(query)
        context = cls.build_context(query=query, question_id=question_id)
        playbook = FUNDAMENTAL_PLAYBOOKS.get(topic or "")
        matched_question = context.questions[0] if context.questions else None
        matched_lesson = context.lessons[0] if context.lessons else None

        if playbook:
            answer = playbook["summary"]
            answer += "\n\nשלבי פתרון:\n" + "\n".join(f"{i + 1}. {step}" for i, step in enumerate(playbook["steps"]))
            answer += "\n\nטעויות נפוצות:\n" + "\n".join(f"• {item}" for item in playbook["mistakes"])
            if matched_question:
                answer += f"\n\nמצאתי גם שאלה רלוונטית במאגר: #{matched_question['id']}"
        elif matched_question:
            topic_label = matched_question.get("subcategory") or matched_question.get("skill") or matched_question.get("main_category") or "כללי"
            answer = (
                f"מצאתי שאלה רלוונטית בנושא {topic_label}.\n\n"
                f"{matched_question['body']}\n\n"
                "כדי ללמוד אותה נכון: קודם מזהים מה מבקשים, אחר כך מזהים את הכלל, ולבסוף בודקים את האפשרויות מול הכלל."
            )
        elif matched_lesson:
            answer = f"מצאתי שיעור מתאים: {matched_lesson['title']}. אפשר ללמוד אותו לפי הסדר שבמרכז הלמידה, ולאחר מכן לעבור לתרגול מהמאגר."
        else:
            answer = "לא מצאתי התאמה ישירה. אפשר לנסות נושא מדויק יותר, למשל: 'למד אותי שברים', 'איך פותרים אנלוגיות', 'הסבר מטריצות', או לשלוח שאלה ספציפית."

        return {
            "answer": answer,
            "topic": topic,
            "mode": mode,
            "question": matched_question,
            "lesson": matched_lesson,
            "stats": {"total_questions": context.total_questions, "total_lessons": context.total_lessons},
        }

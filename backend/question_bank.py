"""Deterministic quantitative question bank used by the production seed.

The bank is generated from audited templates rather than random text. Every
question has a stable bank_key, four answer choices, a single correct answer,
a solution, difficulty metadata and a skill/subcategory tag. The seed only
adds missing bank keys, so deployments are idempotent.
"""

from app.models.answer import Answer
from app.models.constants import ContentStatus, QuestionDifficulty
from app.models.question import Question
from question_bank_extended import build_extended_question_bank


def _rich(text: str) -> dict:
    return {"format": "markdown", "body": text.strip()}


def _answers(correct: int | float, distractors: list[int | float], explanation: str) -> list[Answer]:
    values = [correct, *distractors[:3]]
    return [
        Answer(
            answer_text=str(value),
            is_correct=(index == 0),
            explanation_if_selected=_rich(explanation if index == 0 else f"לא נכון. {explanation}"),
            order=index + 1,
        )
        for index, value in enumerate(values)
    ]


def _difficulty(index: int) -> str:
    return (
        QuestionDifficulty.EASY if index % 5 in (0, 1)
        else QuestionDifficulty.MEDIUM if index % 5 in (2, 3)
        else QuestionDifficulty.EXAM
    )


def _q(key: str, category_id: int, body: str, correct: int | float,
       distractors: list[int | float], solution: str, skill: str,
       subcategory: str, index: int, seconds: int = 15,
       lesson_id: int | None = None) -> Question:
    difficulty = _difficulty(index)
    return Question(
        category_id=category_id,
        lesson_id=lesson_id,
        question_type="multiple_choice",
        difficulty=difficulty,
        status=ContentStatus.PUBLISHED,
        body=_rich(body),
        solution_text=_rich(solution),
        recommended_time_seconds=seconds,
        question_metadata={
            "bank_key": key,
            "main_category": "חשיבה כמותית",
            "subcategory": subcategory,
            "skill": skill,
            "difficulty_level": 1 if difficulty == QuestionDifficulty.EASY else 3 if difficulty == QuestionDifficulty.MEDIUM else 5,
            "tags": [subcategory, skill],
        },
        answers=_answers(correct, distractors, solution),
    )


def build_question_bank(category_id: int, lesson_id: int | None = None) -> list[Question]:
    """Build 600 stable questions across twelve quantitative skill families."""
    questions: list[Question] = []
    n = 0

    # 1) Arithmetic and order of operations — 50
    for a in range(11, 61):
        n += 1
        b = (a % 9) + 2
        c = (a % 5) + 1
        correct = a + b * c
        questions.append(_q(
            f"arith-add-mul-{a}", category_id,
            f"חשב: {a} + {b} × {c} = ?",
            correct, [correct + 1, correct - b, a + b + c],
            f"מבצעים כפל לפני חיבור: {b} × {c} = {b*c}, ואז {a} + {b*c} = {correct}.",
            "סדר פעולות", "חשבון בסיסי", n, 12, lesson_id,
        ))

    # 2) Percentages — 50
    for base in range(20, 70):
        n += 1
        amount = base * 10
        percent = (base % 5 + 1) * 10
        correct = amount * percent // 100
        questions.append(_q(
            f"percent-{base}", category_id,
            f"כמה הם {percent}% מתוך {amount}?",
            correct, [correct + 5, correct - 5, base + percent],
            f"{percent}% הם {percent}/100, ולכן {amount} × {percent}/100 = {correct}.",
            "אחוזים", "אחוזים", n, 15, lesson_id,
        ))

    # 3) Ratios and proportions — 50
    for x in range(2, 52):
        n += 1
        left = (x % 7) + 2
        right = (x % 5) + 3
        multiplier = (x % 4) + 2
        correct = right * multiplier
        questions.append(_q(
            f"ratio-{x}", category_id,
            f"היחס בין A ל-B הוא {left}:{right}. אם A = {left*multiplier}, כמה B?",
            correct, [correct + right, correct - right, left * multiplier],
            f"מכפילים את שני חלקי היחס באותו גורם: {left} → {left*multiplier}, לכן B = {right} × {multiplier} = {correct}.",
            "יחסים", "יחסים ופרופורציות", n, 18, lesson_id,
        ))

    # 4) Number sequences — 50
    for x in range(1, 51):
        n += 1
        start = x + 2
        step = (x % 6) + 2
        a1 = start
        a2 = start + step
        a3 = start + 2 * step
        correct = start + 3 * step
        questions.append(_q(
            f"sequence-{x}", category_id,
            f"מהו האיבר הבא: {a1}, {a2}, {a3}, ?",
            correct, [correct + step, correct - 1, a3 + 1],
            f"ההפרש הקבוע הוא {step}, ולכן {a3} + {step} = {correct}.",
            "זיהוי סדרות", "סדרות מספרים", n, 16, lesson_id,
        ))

    # 5) Linear equations — 50
    for x in range(1, 51):
        n += 1
        solution = x + 3
        coefficient = (x % 6) + 2
        constant = (x % 8) + 1
        rhs = coefficient * solution + constant
        questions.append(_q(
            f"equation-{x}", category_id,
            f"פתור: {coefficient}x + {constant} = {rhs}",
            solution, [solution + 1, solution - 1, coefficient + solution],
            f"מחסרים {constant}: {coefficient}x = {rhs-constant}. מחלקים ב-{coefficient}, ולכן x = {solution}.",
            "משוואות", "אלגברה", n, 20, lesson_id,
        ))

    # 6) Applied quantitative reasoning — 50
    for x in range(1, 51):
        n += 1
        price = 100 + x * 20
        discount = ((x % 4) + 1) * 5
        correct = price * (100 - discount) // 100
        questions.append(_q(
            f"word-discount-{x}", category_id,
            f"מוצר עולה {price} ₪ ומקבלים עליו הנחה של {discount}%. מה המחיר לאחר ההנחה?",
            correct, [price - discount, correct + 5, correct - 5],
            f"מחיר לאחר הנחה = {price} × (1 - {discount}/100) = {correct} ₪.",
            "בעיות מילוליות", "יישום", n, 22, lesson_id,
        ))

    # Extended bank: 300 more questions.
    questions.extend(build_extended_question_bank(category_id, lesson_id))
    return questions

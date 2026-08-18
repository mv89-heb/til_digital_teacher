"""Extended deterministic question bank: 300 additional quantitative questions."""

from app.models.answer import Answer
from app.models.constants import ContentStatus, QuestionDifficulty
from app.models.question import Question


def _rich(text: str) -> dict:
    return {"format": "markdown", "body": text.strip()}


def _answers(correct: str, distractors: list[str], explanation: str) -> list[Answer]:
    values = [correct, *distractors[:3]]
    return [Answer(
        answer_text=value,
        is_correct=index == 0,
        explanation_if_selected=_rich(explanation if index == 0 else f"לא נכון. {explanation}"),
        order=index + 1,
    ) for index, value in enumerate(values)]


def _difficulty(index: int) -> str:
    return (
        QuestionDifficulty.EASY if index % 5 in (0, 1)
        else QuestionDifficulty.MEDIUM if index % 5 in (2, 3)
        else QuestionDifficulty.EXAM
    )


def _q(key: str, category_id: int, body: str, correct: str,
       distractors: list[str], solution: str, skill: str,
       subcategory: str, index: int, seconds: int,
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
            "tags": [subcategory, skill, "extended-bank"],
        },
        answers=_answers(correct, distractors, solution),
    )


def build_extended_question_bank(category_id: int, lesson_id: int | None = None) -> list[Question]:
    """Build 300 additional questions across six distinct quantitative families."""
    questions: list[Question] = []
    index = 301

    # 1) Averages and statistics — 50
    for i in range(1, 51):
        count = (i % 5) + 3
        average = (i % 8) + 6
        total = count * average
        removed = (i % 4) + 1
        remaining_total = total - removed
        questions.append(_q(
            f"avg-sum-{i}", category_id,
            f"ל-{count} מספרים יש ממוצע {average}. אם אחד המספרים הוא {removed}, מה סכום {count - 1} המספרים האחרים?",
            str(remaining_total),
            [str(remaining_total + average), str(total), str(remaining_total - average)],
            f"הסכום הכולל הוא {count} × {average} = {total}. מחסרים {removed}, ולכן נשאר {remaining_total}.",
            "ממוצעים", "סטטיסטיקה בסיסית", index, 20, lesson_id,
        ))
        index += 1

    # 2) Speed, time and distance — 50
    for i in range(1, 51):
        speed = (i % 7 + 3) * 10
        hours = (i % 4) + 1
        distance = speed * hours
        questions.append(_q(
            f"rate-distance-{i}", category_id,
            f"רכב נוסע במהירות {speed} קמ״ש במשך {hours} שעות. כמה קילומטרים עבר?",
            str(distance),
            [str(distance + speed), str(distance - speed), str(speed + hours)],
            f"דרך = מהירות × זמן = {speed} × {hours} = {distance} ק״מ.",
            "מהירות-זמן-דרך", "בעיות תנועה", index, 18, lesson_id,
        ))
        index += 1

    # 3) Probability — 50
    for i in range(1, 51):
        total = (i % 7) + 5
        favorable = (i % (total - 1)) + 1
        probability = f"{favorable}/{total}"
        questions.append(_q(
            f"prob-basic-{i}", category_id,
            f"בקופסה יש {total} כדורים, מתוכם {favorable} אדומים. מוציאים כדור אחד באקראי. מה ההסתברות לקבל אדום?",
            probability,
            [f"{total-favorable}/{total}", f"{favorable}/{total-favorable}", f"1/{total}"],
            f"הסתברות = תוצאות רצויות חלקי תוצאות אפשריות = {favorable}/{total}.",
            "הסתברות", "הסתברות בסיסית", index, 20, lesson_id,
        ))
        index += 1

    # 4) Geometry — 50
    for i in range(1, 51):
        width = (i % 9) + 3
        height = (i % 6) + 2
        area = width * height
        perimeter = 2 * (width + height)
        if i % 2:
            body = f"למלבן אורך {width} ס״מ ורוחב {height} ס״מ. מה השטח?"
            correct = str(area)
            distractors = [str(perimeter), str(area + width), str(area - height)]
            solution = f"שטח מלבן = אורך × רוחב = {width} × {height} = {area} סמ״ר."
            skill = "שטחים"
        else:
            body = f"למלבן אורך {width} ס״מ ורוחב {height} ס״מ. מה ההיקף?"
            correct = str(perimeter)
            distractors = [str(area), str(perimeter + width), str(perimeter - height)]
            solution = f"היקף מלבן = 2 × (אורך + רוחב) = 2 × ({width} + {height}) = {perimeter} ס״מ."
            skill = "היקפים"
        questions.append(_q(
            f"geometry-rect-{i}", category_id, body, correct, distractors,
            solution, skill, "גיאומטריה", index, 20, lesson_id,
        ))
        index += 1

    # 5) Fractions and proportional parts — 50
    for i in range(1, 51):
        denominator = (i % 7) + 3
        numerator = (i % (denominator - 1)) + 1
        whole = denominator * ((i % 8) + 2)
        part = whole * numerator // denominator
        fraction = f"{numerator}/{denominator}"
        questions.append(_q(
            f"fraction-part-{i}", category_id,
            f"כמה הם {fraction} מתוך {whole}?",
            str(part),
            [str(part + numerator), str(part + denominator), str(whole - part)],
            f"מכפילים את השלם בשבר: {whole} × {numerator}/{denominator} = {part}.",
            "שברים", "שברים וחלקים", index, 18, lesson_id,
        ))
        index += 1

    # 6) Multi-step word problems — 50
    for i in range(1, 51):
        start = 50 + i * 4
        added = (i % 6 + 2) * 5
        discount = (i % 4 + 1) * 5
        before_discount = start + added
        final_price = before_discount * (100 - discount) // 100
        questions.append(_q(
            f"word-multi-{i}", category_id,
            f"מחיר מוצר הוא {start} ₪. המחיר עולה ב-{added} ₪, ולאחר מכן ניתנת הנחה של {discount}%. מה המחיר הסופי?",
            str(final_price),
            [str(before_discount - discount), str(final_price + 5), str(final_price - 5)],
            f"תחילה: {start} + {added} = {before_discount} ₪. לאחר הנחה: {before_discount} × (100 - {discount})/100 = {final_price} ₪.",
            "פתרון רב-שלבי", "בעיות מילוליות", index, 25, lesson_id,
        ))
        index += 1

    return questions

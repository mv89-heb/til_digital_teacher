# Import all models so SQLAlchemy metadata includes every table during
# migrations and application startup.
from app.models.user import User  # noqa: F401
from app.models.category import Category  # noqa: F401
from app.models.lesson import Lesson  # noqa: F401
from app.models.lesson_content import LessonContent  # noqa: F401
from app.models.question import Question  # noqa: F401
from app.models.answer import Answer  # noqa: F401
from app.models.practice_attempt import PracticeAttempt  # noqa: F401
from app.models.user_lesson_progress import UserLessonProgress  # noqa: F401
from app.models.user_progress import UserProgress  # noqa: F401
from app.models.xp_transaction import XPTransaction  # noqa: F401
from app.models.question_version import QuestionVersion  # noqa: F401
from app.models.exam import Exam  # noqa: F401
from app.models.exam_section import ExamSection  # noqa: F401
from app.models.exam_question_pool import ExamQuestionPool  # noqa: F401
from app.models.exam_session import ExamSession  # noqa: F401
from app.models.session_question import SessionQuestion  # noqa: F401
from app.models.user_answer import UserAnswer  # noqa: F401
from app.models.exam_event import ExamEvent  # noqa: F401
from app.models.exam_result import ExamResult  # noqa: F401
from app.models.exam_result_category import ExamResultCategory  # noqa: F401
from app.models.exam_result_difficulty import ExamResultDifficulty  # noqa: F401

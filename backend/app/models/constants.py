class CategoryType:
    QUANTITATIVE = "quantitative"
    VERBAL = "verbal"
    FIGURAL = "figural"
    LOGIC = "logic"

    ALL = [QUANTITATIVE, VERBAL, FIGURAL, LOGIC]


class ContentStatus:
    """Publication state, shared by Category and Lesson.

    Defaults to DRAFT everywhere content is created — nothing is visible on
    the public /api/learning/* endpoints until an admin explicitly publishes
    it. Admin endpoints always see everything regardless of status.
    """

    DRAFT = "draft"
    PUBLISHED = "published"
    ARCHIVED = "archived"

    ALL = [DRAFT, PUBLISHED, ARCHIVED]


class LessonDifficulty:
    BEGINNER = "beginner"
    INTERMEDIATE = "intermediate"
    ADVANCED = "advanced"

    ALL = [BEGINNER, INTERMEDIATE, ADVANCED]


class QuestionType:
    MULTIPLE_CHOICE = "multiple_choice"

    ALL = [MULTIPLE_CHOICE]


class QuestionDifficulty:
    EASY = "easy"
    MEDIUM = "medium"
    EXAM = "exam"

    ALL = [EASY, MEDIUM, EXAM]


class LessonSection:
    """The pedagogical role a LessonContent block plays within a lesson.

    Matches the required 8-part lesson structure (title lives on Lesson
    itself; the other sections are content sections). New sections can be
    added here freely — the column is a plain string, not a DB enum, so
    adding a value never requires a migration. GUIDED_PRACTICE was added in
    Stage 2 to house embedded_question blocks.
    """

    SIMPLE_EXPLANATION = "simple_explanation"
    NORMAL_EXPLANATION = "normal_explanation"
    SOLVED_EXAMPLE = "solved_example"
    NORMAL_METHOD = "normal_method"
    FAST_METHOD = "fast_method"
    COMMON_MISTAKES = "common_mistakes"
    GUIDED_PRACTICE = "guided_practice"
    SUMMARY = "summary"

    ALL = [
        SIMPLE_EXPLANATION,
        NORMAL_EXPLANATION,
        SOLVED_EXAMPLE,
        NORMAL_METHOD,
        FAST_METHOD,
        COMMON_MISTAKES,
        GUIDED_PRACTICE,
        SUMMARY,
    ]


class StudentLevelValue:
    """Per-category skill level, computed by ProgressService from accuracy
    and practice volume (see _calculate_level). Not user-editable directly.
    """

    BEGINNER = "beginner"
    BASIC = "basic"
    INTERMEDIATE = "intermediate"
    EXAM_READY = "exam_ready"
    ADVANCED = "advanced"

    ALL = [BEGINNER, BASIC, INTERMEDIATE, EXAM_READY, ADVANCED]


class BlockType:
    """The content/rendering format of a single LessonContent block.

    Orthogonal to LessonSection: a section (e.g. solved_example) can in
    the future hold more than one block (e.g. a text block plus an image
    block). Only TEXT is actually produced by Stage 1 seed data — the
    rest exist so the schema never has to change when they're used.
    """

    TEXT = "text"
    IMAGE = "image"
    VIDEO = "video"
    TABLE = "table"
    FORMULA = "formula"
    INTERACTIVE = "interactive"
    EMBEDDED_QUESTION = "embedded_question"

    ALL = [TEXT, IMAGE, VIDEO, TABLE, FORMULA, INTERACTIVE, EMBEDDED_QUESTION]

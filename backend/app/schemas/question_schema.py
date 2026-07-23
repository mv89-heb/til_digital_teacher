from marshmallow import Schema, fields, validate

from app.models.constants import ContentStatus, QuestionDifficulty, QuestionType


class AnswerSchema(Schema):
    answer_text = fields.String(required=True, validate=validate.Length(min=1, max=500))
    is_correct = fields.Boolean(required=True)
    explanation_if_selected = fields.Dict(required=False, allow_none=True)
    order = fields.Integer(required=False, load_default=0)


class AnswerUpdateSchema(Schema):
    answer_text = fields.String(required=False, validate=validate.Length(min=1, max=500))
    is_correct = fields.Boolean(required=False)
    explanation_if_selected = fields.Dict(required=False, allow_none=True)
    order = fields.Integer(required=False)


class QuestionSchema(Schema):
    category_id = fields.Integer(required=True)
    lesson_id = fields.Integer(required=False, allow_none=True)
    question_type = fields.String(
        required=False, load_default=QuestionType.MULTIPLE_CHOICE, validate=validate.OneOf(QuestionType.ALL)
    )
    difficulty = fields.String(required=True, validate=validate.OneOf(QuestionDifficulty.ALL))
    status = fields.String(required=False, load_default=ContentStatus.DRAFT, validate=validate.OneOf(ContentStatus.ALL))
    body = fields.Dict(required=True)
    solution_text = fields.Dict(required=True)
    recommended_time_seconds = fields.Integer(required=False, allow_none=True, validate=validate.Range(min=1))
    metadata = fields.Dict(required=False, load_default=dict)
    answers = fields.List(fields.Nested(AnswerSchema), required=False, load_default=list)


class QuestionUpdateSchema(Schema):
    category_id = fields.Integer(required=False)
    lesson_id = fields.Integer(required=False, allow_none=True)
    question_type = fields.String(required=False, validate=validate.OneOf(QuestionType.ALL))
    difficulty = fields.String(required=False, validate=validate.OneOf(QuestionDifficulty.ALL))
    status = fields.String(required=False, validate=validate.OneOf(ContentStatus.ALL))
    body = fields.Dict(required=False)
    solution_text = fields.Dict(required=False)
    recommended_time_seconds = fields.Integer(required=False, allow_none=True, validate=validate.Range(min=1))
    metadata = fields.Dict(required=False)


question_schema = QuestionSchema()
question_update_schema = QuestionUpdateSchema()
answer_schema = AnswerSchema()
answer_update_schema = AnswerUpdateSchema()

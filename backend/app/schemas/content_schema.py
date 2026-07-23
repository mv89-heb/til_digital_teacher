from marshmallow import Schema, fields, validate

from app.models.constants import BlockType, CategoryType, ContentStatus, LessonDifficulty, LessonSection


class CategorySchema(Schema):
    name = fields.String(required=True, validate=validate.Length(min=1, max=120))
    description = fields.String(required=False, allow_none=True)
    type = fields.String(required=True, validate=validate.OneOf(CategoryType.ALL))
    icon = fields.String(required=False, allow_none=True, validate=validate.Length(max=50))
    thumbnail_url = fields.String(required=False, allow_none=True, validate=validate.Length(max=255))
    status = fields.String(required=False, load_default=ContentStatus.DRAFT, validate=validate.OneOf(ContentStatus.ALL))
    parent_id = fields.Integer(required=False, allow_none=True)
    order = fields.Integer(required=False, load_default=0)


class CategoryUpdateSchema(Schema):
    name = fields.String(required=False, validate=validate.Length(min=1, max=120))
    description = fields.String(required=False, allow_none=True)
    type = fields.String(required=False, validate=validate.OneOf(CategoryType.ALL))
    icon = fields.String(required=False, allow_none=True, validate=validate.Length(max=50))
    thumbnail_url = fields.String(required=False, allow_none=True, validate=validate.Length(max=255))
    status = fields.String(required=False, validate=validate.OneOf(ContentStatus.ALL))
    parent_id = fields.Integer(required=False, allow_none=True)
    order = fields.Integer(required=False)


class LessonSchema(Schema):
    category_id = fields.Integer(required=True)
    title = fields.String(required=True, validate=validate.Length(min=1, max=200))
    slug = fields.String(required=False, allow_none=True, validate=validate.Length(max=220))
    description = fields.String(required=False, allow_none=True)
    status = fields.String(required=False, load_default=ContentStatus.DRAFT, validate=validate.OneOf(ContentStatus.ALL))
    difficulty_level = fields.String(required=False, allow_none=True, validate=validate.OneOf(LessonDifficulty.ALL))
    estimated_duration = fields.Integer(required=False, allow_none=True, validate=validate.Range(min=1))
    icon = fields.String(required=False, allow_none=True, validate=validate.Length(max=50))
    thumbnail_url = fields.String(required=False, allow_none=True, validate=validate.Length(max=255))
    order = fields.Integer(required=False, load_default=0)


class LessonUpdateSchema(Schema):
    category_id = fields.Integer(required=False)
    title = fields.String(required=False, validate=validate.Length(min=1, max=200))
    slug = fields.String(required=False, allow_none=True, validate=validate.Length(max=220))
    description = fields.String(required=False, allow_none=True)
    status = fields.String(required=False, validate=validate.OneOf(ContentStatus.ALL))
    difficulty_level = fields.String(required=False, allow_none=True, validate=validate.OneOf(LessonDifficulty.ALL))
    estimated_duration = fields.Integer(required=False, allow_none=True, validate=validate.Range(min=1))
    icon = fields.String(required=False, allow_none=True, validate=validate.Length(max=50))
    thumbnail_url = fields.String(required=False, allow_none=True, validate=validate.Length(max=255))
    order = fields.Integer(required=False)


class LessonContentSchema(Schema):
    section = fields.String(required=True, validate=validate.OneOf(LessonSection.ALL))
    block_type = fields.String(required=True, validate=validate.OneOf(BlockType.ALL))
    order = fields.Integer(required=False, load_default=0)
    content = fields.Dict(required=True)
    metadata = fields.Dict(required=False, load_default=dict)


class LessonContentUpdateSchema(Schema):
    section = fields.String(required=False, validate=validate.OneOf(LessonSection.ALL))
    block_type = fields.String(required=False, validate=validate.OneOf(BlockType.ALL))
    order = fields.Integer(required=False)
    content = fields.Dict(required=False)
    metadata = fields.Dict(required=False)


class SolutionStrategySchema(Schema):
    category_id = fields.Integer(required=True)
    identification_tips = fields.Dict(required=True)
    normal_method = fields.Dict(required=True)
    fast_method = fields.Dict(required=True)
    shortcut_text = fields.Dict(required=False, allow_none=True)
    target_time_seconds = fields.Integer(required=False, allow_none=True)


class SolutionStrategyUpdateSchema(Schema):
    category_id = fields.Integer(required=False)
    identification_tips = fields.Dict(required=False)
    normal_method = fields.Dict(required=False)
    fast_method = fields.Dict(required=False)
    shortcut_text = fields.Dict(required=False, allow_none=True)
    target_time_seconds = fields.Integer(required=False, allow_none=True)


category_schema = CategorySchema()
category_update_schema = CategoryUpdateSchema()
lesson_schema = LessonSchema()
lesson_update_schema = LessonUpdateSchema()
lesson_content_schema = LessonContentSchema()
lesson_content_update_schema = LessonContentUpdateSchema()
solution_strategy_schema = SolutionStrategySchema()
solution_strategy_update_schema = SolutionStrategyUpdateSchema()

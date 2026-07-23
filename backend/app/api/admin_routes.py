from flask import Blueprint, g, jsonify, request

from app.schemas.content_schema import (
    category_schema,
    category_update_schema,
    lesson_content_schema,
    lesson_content_update_schema,
    lesson_schema,
    lesson_update_schema,
    solution_strategy_schema,
    solution_strategy_update_schema,
)
from app.services.category_service import CategoryService
from app.services.lesson_service import LessonService
from app.services.question_service import QuestionService
from app.services.solution_strategy_service import SolutionStrategyService
from app.utils.decorators import admin_required

admin_bp = Blueprint("admin", __name__, url_prefix="/api/admin")


# --- Categories ---

@admin_bp.route("/categories", methods=["GET"])
@admin_required
def list_categories():
    return jsonify({"categories": CategoryService.list_categories()}), 200


@admin_bp.route("/categories", methods=["POST"])
@admin_required
def create_category():
    data = category_schema.load(request.get_json() or {})
    category = CategoryService.create_category(data, g.current_user["id"])
    return jsonify({"category": category}), 201


@admin_bp.route("/categories/<int:category_id>", methods=["GET"])
@admin_required
def get_category(category_id):
    category = CategoryService.get_category(category_id)
    return jsonify({"category": category.to_dict()}), 200


@admin_bp.route("/categories/<int:category_id>", methods=["PUT"])
@admin_required
def update_category(category_id):
    data = category_update_schema.load(request.get_json() or {})
    category = CategoryService.update_category(category_id, data, g.current_user["id"])
    return jsonify({"category": category}), 200


@admin_bp.route("/categories/<int:category_id>", methods=["DELETE"])
@admin_required
def delete_category(category_id):
    CategoryService.delete_category(category_id, g.current_user["id"])
    return jsonify({"message": "Category deleted"}), 200


# --- Lessons ---

@admin_bp.route("/lessons", methods=["GET"])
@admin_required
def list_lessons():
    category_id = request.args.get("category_id", type=int)
    return jsonify({"lessons": LessonService.list_lessons(category_id)}), 200


@admin_bp.route("/lessons", methods=["POST"])
@admin_required
def create_lesson():
    data = lesson_schema.load(request.get_json() or {})
    lesson = LessonService.create_lesson(data, g.current_user["id"])
    return jsonify({"lesson": lesson}), 201


@admin_bp.route("/lessons/<int:lesson_id>", methods=["GET"])
@admin_required
def get_lesson(lesson_id):
    lesson = LessonService.get_lesson(lesson_id)
    data = lesson.to_dict()
    data["content_blocks"] = QuestionService.resolve_embedded_blocks(
        data["content_blocks"], published_only=False
    )
    return jsonify({"lesson": data}), 200


@admin_bp.route("/lessons/<int:lesson_id>", methods=["PUT"])
@admin_required
def update_lesson(lesson_id):
    data = lesson_update_schema.load(request.get_json() or {})
    lesson = LessonService.update_lesson(lesson_id, data, g.current_user["id"])
    return jsonify({"lesson": lesson}), 200


@admin_bp.route("/lessons/<int:lesson_id>", methods=["DELETE"])
@admin_required
def delete_lesson(lesson_id):
    LessonService.delete_lesson(lesson_id, g.current_user["id"])
    return jsonify({"message": "Lesson deleted"}), 200


# --- Lesson content blocks ---

@admin_bp.route("/lessons/<int:lesson_id>/content", methods=["POST"])
@admin_required
def add_content_block(lesson_id):
    data = lesson_content_schema.load(request.get_json() or {})
    block = LessonService.add_content_block(lesson_id, data, g.current_user["id"])
    return jsonify({"content_block": block}), 201


@admin_bp.route("/lesson-content/<int:block_id>", methods=["PUT"])
@admin_required
def update_content_block(block_id):
    data = lesson_content_update_schema.load(request.get_json() or {})
    block = LessonService.update_content_block(block_id, data, g.current_user["id"])
    return jsonify({"content_block": block}), 200


@admin_bp.route("/lesson-content/<int:block_id>", methods=["DELETE"])
@admin_required
def delete_content_block(block_id):
    LessonService.delete_content_block(block_id, g.current_user["id"])
    return jsonify({"message": "Content block deleted"}), 200


# --- Solution strategies ---

@admin_bp.route("/solution-strategies", methods=["GET"])
@admin_required
def list_solution_strategies():
    category_id = request.args.get("category_id", type=int)
    return jsonify({"solution_strategies": SolutionStrategyService.list_strategies(category_id)}), 200


@admin_bp.route("/solution-strategies", methods=["POST"])
@admin_required
def create_solution_strategy():
    data = solution_strategy_schema.load(request.get_json() or {})
    strategy = SolutionStrategyService.create_strategy(data, g.current_user["id"])
    return jsonify({"solution_strategy": strategy}), 201


@admin_bp.route("/solution-strategies/<int:strategy_id>", methods=["GET"])
@admin_required
def get_solution_strategy(strategy_id):
    strategy = SolutionStrategyService.get_strategy(strategy_id)
    return jsonify({"solution_strategy": strategy.to_dict()}), 200


@admin_bp.route("/solution-strategies/<int:strategy_id>", methods=["PUT"])
@admin_required
def update_solution_strategy(strategy_id):
    data = solution_strategy_update_schema.load(request.get_json() or {})
    strategy = SolutionStrategyService.update_strategy(strategy_id, data, g.current_user["id"])
    return jsonify({"solution_strategy": strategy}), 200


@admin_bp.route("/solution-strategies/<int:strategy_id>", methods=["DELETE"])
@admin_required
def delete_solution_strategy(strategy_id):
    SolutionStrategyService.delete_strategy(strategy_id, g.current_user["id"])
    return jsonify({"message": "Solution strategy deleted"}), 200

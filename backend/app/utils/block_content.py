from app.models.constants import BlockType
from app.utils.exceptions import AppError

# Minimum required keys per block_type. Deliberately minimal (existence
# checks, not deep type-checking) — the goal is to catch an obviously wrong
# payload (e.g. a "formula" block with no "latex" key), not to be a full
# content schema. ContentBlockRenderer components on the frontend can rely
# on these keys being present.
_REQUIRED_KEYS = {
    BlockType.TEXT: ["body"],
    BlockType.IMAGE: ["url"],
    BlockType.VIDEO: ["url"],
    BlockType.TABLE: ["headers", "rows"],
    BlockType.FORMULA: ["latex"],
    BlockType.INTERACTIVE: ["component"],
    BlockType.EMBEDDED_QUESTION: ["question_id"],
}


def validate_block_content(block_type: str, content: dict) -> None:
    required = _REQUIRED_KEYS.get(block_type, [])
    missing = [key for key in required if key not in (content or {})]
    if missing:
        raise AppError(
            f"Block type '{block_type}' requires content keys: {', '.join(missing)}",
            status_code=422,
        )

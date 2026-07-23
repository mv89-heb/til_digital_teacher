from datetime import datetime, timezone

from app.extensions import db


class TimestampMixin:
    """Adds created_at / updated_at to any model that inherits it."""

    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = db.Column(
        db.DateTime,
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )


class RichContentMixin:
    """Adds a rich-content structure to any model that needs formatted teaching
    content (Lesson bodies, Question stems, explanations, etc.).

    Not wired into any model yet — Stage 1/2 models (Lesson, Question) will
    inherit this once they're built. Defined now so every future content
    field is consistent from the start instead of retrofitted later.

    content_format:
        Always "markdown" for now. Kept as a column (not hardcoded) so a
        future format (e.g. a rich-text JSON doc) can be introduced without
        a schema change.

    content_body:
        The main Markdown text. Math formulas are written inline as LaTeX
        (e.g. $x^2$), rendered client-side — no separate formula field needed.

    content_media:
        JSON list of attached media, each item shaped like:
        {"type": "image" | "diagram" | "table", "url": str, "caption": str,
         "alt_text": str}
        Kept as a single JSON column rather than separate tables per media
        type, since these are always rendered inline with the text and never
        queried independently.
    """

    content_format = db.Column(db.String(20), default="markdown", nullable=False)
    content_body = db.Column(db.Text, nullable=True)
    content_media = db.Column(db.JSON, default=list)

import re

# Keep ASCII letters/digits and Hebrew letters (U+0590-U+05FF); everything
# else (spaces, punctuation, quotes) collapses to a single hyphen. Hebrew is
# kept as-is (not transliterated) since the whole product is Hebrew-first —
# readable Hebrew slugs are more useful here than romanized ones.
_NON_SLUG_CHARS = re.compile(r"[^a-z0-9\u0590-\u05FF]+")
_MULTI_HYPHEN = re.compile(r"-{2,}")


def slugify(text: str) -> str:
    text = (text or "").strip().lower()
    text = _NON_SLUG_CHARS.sub("-", text)
    text = _MULTI_HYPHEN.sub("-", text).strip("-")
    return text or "lesson"

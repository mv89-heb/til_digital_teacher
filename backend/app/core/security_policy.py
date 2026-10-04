import secrets


def require_production_secret(value: str | None, name: str) -> str:
    if not value or len(value) < 32:
        raise RuntimeError(f"{name} must be configured with at least 32 random characters")
    return value


def generate_secret() -> str:
    return secrets.token_urlsafe(48)

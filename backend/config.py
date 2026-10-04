import os

from app.core.security_policy import require_production_config, require_production_secret


def _csv_env(name: str, default: str = "") -> list[str]:
    return [item.strip() for item in os.getenv(name, default).split(",") if item.strip()]


class Config:
    """Base configuration shared by all environments."""

    SECRET_KEY = os.getenv("JWT_SECRET") or os.getenv("SECRET_KEY") or "development-only-secret-change-me"
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_DATABASE_URI = os.getenv(
        "DATABASE_URL", "postgresql://user:password@localhost/til_db"
    )
    JWT_EXPIRES_DAYS = int(os.getenv("JWT_EXPIRES_DAYS", "1"))
    CORS_ORIGINS = _csv_env("CORS_ORIGINS", "http://localhost:3000")
    MAX_CONTENT_LENGTH = int(os.getenv("MAX_CONTENT_LENGTH", str(2 * 1024 * 1024)))
    RATELIMIT_STORAGE_URI = os.getenv("RATELIMIT_STORAGE_URI", "memory://")


class DevelopmentConfig(Config):
    DEBUG = True


class TestingConfig(Config):
    TESTING = True
    DEBUG = True
    SQLALCHEMY_DATABASE_URI = os.getenv("TEST_DATABASE_URL", "sqlite:///:memory:")
    SECRET_KEY = "test-secret-key"
    CORS_ORIGINS = ["http://localhost:3000"]
    RATELIMIT_ENABLED = False


class ProductionConfig(Config):
    """Production settings are validated when the production app is created."""

    DEBUG = False
    SECRET_KEY = None
    SQLALCHEMY_DATABASE_URI = None
    CORS_ORIGINS = []


def validate_production_config(config: type[ProductionConfig]) -> None:
    """Fail closed when required production security settings are missing."""

    config.SECRET_KEY = require_production_secret(
        os.getenv("JWT_SECRET") or os.getenv("SECRET_KEY"),
        "JWT_SECRET (or SECRET_KEY)",
    )

    database_url = os.getenv("DATABASE_URL")
    if not database_url:
        raise RuntimeError(
            "DATABASE_URL must be configured in production (Neon PostgreSQL)"
        )
    config.SQLALCHEMY_DATABASE_URI = database_url

    cors_origins = _csv_env("CORS_ORIGINS")
    if not cors_origins:
        raise RuntimeError("CORS_ORIGINS must be configured in production")
    config.CORS_ORIGINS = cors_origins


config_by_name = {
    "development": DevelopmentConfig,
    "testing": TestingConfig,
    "production": ProductionConfig,
}

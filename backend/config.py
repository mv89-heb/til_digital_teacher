import os

from app.core.security_policy import require_production_secret


class Config:
    """Base configuration shared by all environments."""

    SECRET_KEY = os.getenv("JWT_SECRET") or os.getenv("SECRET_KEY") or "development-only-secret-change-me"
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_DATABASE_URI = os.getenv(
        "DATABASE_URL", "postgresql://user:password@localhost/til_db"
    )
    JWT_EXPIRES_DAYS = int(os.getenv("JWT_EXPIRES_DAYS", "1"))
    CORS_ORIGINS = os.getenv("CORS_ORIGINS", "http://localhost:3000")
    MAX_CONTENT_LENGTH = int(os.getenv("MAX_CONTENT_LENGTH", str(2 * 1024 * 1024)))
    RATELIMIT_STORAGE_URI = os.getenv("RATELIMIT_STORAGE_URI", "memory://")


class DevelopmentConfig(Config):
    DEBUG = True


class TestingConfig(Config):
    TESTING = True
    DEBUG = True
    SQLALCHEMY_DATABASE_URI = os.getenv("TEST_DATABASE_URL", "sqlite:///:memory:")
    SECRET_KEY = "test-secret-key"
    CORS_ORIGINS = "http://localhost:3000"
    RATELIMIT_ENABLED = False


class ProductionConfig(Config):
    DEBUG = False
    SECRET_KEY = require_production_secret(
        os.getenv("JWT_SECRET") or os.getenv("SECRET_KEY"),
        "JWT_SECRET (or SECRET_KEY)",
    )
    # Accept a comma-separated list, while always allowing the deployed
    # frontend origins used by this application. This prevents a stale or
    # incomplete Render environment variable from silently breaking browser
    # POST requests such as login.
    _configured_cors = os.getenv("CORS_ORIGINS", "")
    _frontend_origins = (
        "https://til-digital-teacher-0ryl.onrender.com",
        "https://til-digital-teacher.onrender.com",
    )
    CORS_ORIGINS = ",".join(
        dict.fromkeys(
            origin.strip()
            for origin in (_configured_cors.split(",") + list(_frontend_origins))
            if origin.strip()
        )
    )


config_by_name = {
    "development": DevelopmentConfig,
    "testing": TestingConfig,
    "production": ProductionConfig,
}

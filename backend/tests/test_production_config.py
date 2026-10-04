import pytest

from config import ProductionConfig, validate_production_config


def test_production_config_requires_database_url(monkeypatch):
    monkeypatch.setenv("JWT_SECRET", "a" * 48)
    monkeypatch.delenv("DATABASE_URL", raising=False)
    monkeypatch.setenv("CORS_ORIGINS", "https://example.com")

    with pytest.raises(RuntimeError, match="DATABASE_URL"):
        validate_production_config(ProductionConfig)


def test_production_config_requires_explicit_cors(monkeypatch):
    monkeypatch.setenv("JWT_SECRET", "a" * 48)
    monkeypatch.setenv("DATABASE_URL", "postgresql://example")
    monkeypatch.delenv("CORS_ORIGINS", raising=False)

    with pytest.raises(RuntimeError, match="CORS_ORIGINS"):
        validate_production_config(ProductionConfig)


def test_production_config_accepts_required_values(monkeypatch):
    monkeypatch.setenv("JWT_SECRET", "a" * 48)
    monkeypatch.setenv("DATABASE_URL", "postgresql://example")
    monkeypatch.setenv(
        "CORS_ORIGINS",
        "https://example.com, https://example.org",
    )

    validate_production_config(ProductionConfig)

    assert ProductionConfig.SQLALCHEMY_DATABASE_URI == "postgresql://example"
    assert ProductionConfig.CORS_ORIGINS == [
        "https://example.com",
        "https://example.org",
    ]

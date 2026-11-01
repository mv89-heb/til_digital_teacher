import pytest

from seed import _required_seed_admin_password


def test_seed_admin_password_requires_explicit_configuration(monkeypatch):
    monkeypatch.delenv("SEED_ADMIN_PASSWORD", raising=False)

    with pytest.raises(RuntimeError, match="SEED_ADMIN_PASSWORD"):
        _required_seed_admin_password()


def test_seed_admin_password_rejects_short_values(monkeypatch):
    monkeypatch.setenv("SEED_ADMIN_PASSWORD", "Short123!")

    with pytest.raises(RuntimeError, match="at least 16 characters"):
        _required_seed_admin_password()


def test_seed_admin_password_accepts_explicit_strong_value(monkeypatch):
    password = "A-long-random-password-2026!"
    monkeypatch.setenv("SEED_ADMIN_PASSWORD", password)

    assert _required_seed_admin_password() == password

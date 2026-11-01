from app.extensions import db


def test_liveness_does_not_depend_on_database(client, monkeypatch):
    def fail_if_database_is_touched(*args, **kwargs):
        raise AssertionError("liveness must not query the database")

    monkeypatch.setattr(db.session, "execute", fail_if_database_is_touched)

    response = client.get("/health/live")

    assert response.status_code == 200
    assert response.get_json() == {"status": "alive"}


def test_readiness_reports_database_failure(client, monkeypatch):
    def fail_database_probe(*args, **kwargs):
        raise RuntimeError("database unavailable")

    monkeypatch.setattr(db.session, "execute", fail_database_probe)

    response = client.get("/health")

    assert response.status_code == 503
    assert response.get_json() == {
        "status": "unhealthy",
        "database": "unavailable",
    }

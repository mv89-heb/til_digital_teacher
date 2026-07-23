import pytest

from app import create_app
from app.extensions import db as _db
from app.models.user import User
from werkzeug.security import generate_password_hash


@pytest.fixture
def app():
    app = create_app("testing")
    with app.app_context():
        _db.create_all()
        yield app
        _db.session.remove()
        _db.drop_all()


@pytest.fixture
def client(app):
    return app.test_client()


@pytest.fixture
def db(app):
    return _db


@pytest.fixture
def student_token(client):
    client.post("/api/auth/register", json={"email": "student@test.com", "password": "password123"})
    resp = client.post("/api/auth/login", json={"email": "student@test.com", "password": "password123"})
    return resp.get_json()["data"]["token"]


@pytest.fixture
def admin_token(app, client):
    with app.app_context():
        admin = User(
            email="admin@test.com",
            password_hash=generate_password_hash("password123"),
            role="admin",
        )
        _db.session.add(admin)
        _db.session.commit()

    resp = client.post("/api/auth/login", json={"email": "admin@test.com", "password": "password123"})
    return resp.get_json()["data"]["token"]


@pytest.fixture
def auth_headers():
    def _headers(token):
        return {"Authorization": f"Bearer {token}"}

    return _headers

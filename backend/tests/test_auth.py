def test_register_success(client):
    resp = client.post("/api/auth/register", json={"email": "student@test.com", "password": "password123"})
    assert resp.status_code == 201
    assert resp.get_json()["user"]["email"] == "student@test.com"


def test_register_duplicate_email(client):
    client.post("/api/auth/register", json={"email": "dup@test.com", "password": "password123"})
    resp = client.post("/api/auth/register", json={"email": "dup@test.com", "password": "password123"})
    assert resp.status_code == 409


def test_register_invalid_email(client):
    resp = client.post("/api/auth/register", json={"email": "not-an-email", "password": "password123"})
    assert resp.status_code == 422


def test_register_short_password(client):
    resp = client.post("/api/auth/register", json={"email": "short@test.com", "password": "123"})
    assert resp.status_code == 422


def test_login_success(client):
    client.post("/api/auth/register", json={"email": "login@test.com", "password": "password123"})
    resp = client.post("/api/auth/login", json={"email": "login@test.com", "password": "password123"})
    assert resp.status_code == 200
    body = resp.get_json()
    assert "token" in body["data"]


def test_login_wrong_password(client):
    client.post("/api/auth/register", json={"email": "wrong@test.com", "password": "password123"})
    resp = client.post("/api/auth/login", json={"email": "wrong@test.com", "password": "wrongpass"})
    assert resp.status_code == 401


def test_me_requires_token(client):
    resp = client.get("/api/auth/me")
    assert resp.status_code == 401


def test_me_with_valid_token(client):
    client.post("/api/auth/register", json={"email": "me@test.com", "password": "password123"})
    login_resp = client.post("/api/auth/login", json={"email": "me@test.com", "password": "password123"})
    token = login_resp.get_json()["data"]["token"]

    resp = client.get("/api/auth/me", headers={"Authorization": f"Bearer {token}"})
    assert resp.status_code == 200
    assert resp.get_json()["user"]["email"] == "me@test.com"


def test_me_with_invalid_token(client):
    resp = client.get("/api/auth/me", headers={"Authorization": "Bearer garbage"})
    assert resp.status_code == 401


def test_jwt_uses_active_app_secret(app, client):
    client.post("/api/auth/register", json={"email": "secret@test.com", "password": "password123"})
    app.config["SECRET_KEY"] = "a" * 48
    login_resp = client.post(
        "/api/auth/login",
        json={"email": "secret@test.com", "password": "password123"},
    )
    assert login_resp.status_code == 200
    token = login_resp.get_json()["data"]["token"]

    import jwt

    payload = jwt.decode(token, "a" * 48, algorithms=["HS256"])
    assert payload["user_id"]


def test_jwt_with_unknown_critical_header_is_rejected(app, client):
    client.post("/api/auth/register", json={"email": "crit@test.com", "password": "password123"})
    import jwt

    token = jwt.encode(
        {"user_id": 1},
        app.config["SECRET_KEY"],
        algorithm="HS256",
        headers={"crit": ["unknown-extension"]},
    )
    resp = client.get("/api/auth/me", headers={"Authorization": f"Bearer {token}"})
    assert resp.status_code == 401

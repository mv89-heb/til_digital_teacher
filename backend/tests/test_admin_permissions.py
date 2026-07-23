def test_student_cannot_create_category(client, student_token, auth_headers):
    resp = client.post(
        "/api/admin/categories",
        json={"name": "x", "type": "quantitative"},
        headers=auth_headers(student_token),
    )
    assert resp.status_code == 403


def test_student_cannot_create_lesson(client, student_token, auth_headers):
    resp = client.post(
        "/api/admin/lessons",
        json={"category_id": 1, "title": "x"},
        headers=auth_headers(student_token),
    )
    assert resp.status_code == 403


def test_no_token_rejected(client):
    resp = client.get("/api/admin/categories")
    assert resp.status_code == 401


def test_admin_routes_require_valid_token(client):
    resp = client.get("/api/admin/categories", headers={"Authorization": "Bearer garbage"})
    assert resp.status_code == 401


def test_audit_log_written_on_category_create(client, admin_token, auth_headers, app):
    resp = client.post(
        "/api/admin/categories",
        json={"name": "חשיבה כמותית", "type": "quantitative"},
        headers=auth_headers(admin_token),
    )
    category_id = resp.get_json()["category"]["id"]

    with app.app_context():
        from app.models.audit_log import AuditLog

        entry = AuditLog.query.filter_by(entity_type="Category", entity_id=category_id).first()
        assert entry is not None
        assert entry.action == "create"
        assert entry.changes["after"]["name"] == "חשיבה כמותית"


def test_audit_log_written_on_category_update(client, admin_token, auth_headers, app):
    create = client.post(
        "/api/admin/categories",
        json={"name": "A", "type": "quantitative"},
        headers=auth_headers(admin_token),
    )
    category_id = create.get_json()["category"]["id"]

    client.put(
        f"/api/admin/categories/{category_id}",
        json={"name": "B"},
        headers=auth_headers(admin_token),
    )

    with app.app_context():
        from app.models.audit_log import AuditLog

        entry = (
            AuditLog.query.filter_by(entity_type="Category", entity_id=category_id, action="update")
            .first()
        )
        assert entry is not None
        assert entry.changes["before"]["name"] == "A"
        assert entry.changes["after"]["name"] == "B"


def test_audit_log_written_on_category_delete(client, admin_token, auth_headers, app):
    create = client.post(
        "/api/admin/categories",
        json={"name": "A", "type": "quantitative"},
        headers=auth_headers(admin_token),
    )
    category_id = create.get_json()["category"]["id"]

    client.delete(f"/api/admin/categories/{category_id}", headers=auth_headers(admin_token))

    with app.app_context():
        from app.models.audit_log import AuditLog

        entry = (
            AuditLog.query.filter_by(entity_type="Category", entity_id=category_id, action="delete")
            .first()
        )
        assert entry is not None
        assert entry.changes["before"]["name"] == "A"


def test_no_content_change_without_audit_entry(client, admin_token, auth_headers, app):
    """Every create/update/delete on content must leave an AuditLog row —
    this test creates a lesson + block + update + delete and checks the
    count of audit rows matches the number of mutations exactly."""
    cat = client.post(
        "/api/admin/categories",
        json={"name": "A", "type": "quantitative"},
        headers=auth_headers(admin_token),
    ).get_json()["category"]

    lesson = client.post(
        "/api/admin/lessons",
        json={"category_id": cat["id"], "title": "L"},
        headers=auth_headers(admin_token),
    ).get_json()["lesson"]

    block = client.post(
        f"/api/admin/lessons/{lesson['id']}/content",
        json={"section": "summary", "block_type": "text", "content": {"body": "x"}},
        headers=auth_headers(admin_token),
    ).get_json()["content_block"]

    client.put(
        f"/api/admin/lesson-content/{block['id']}",
        json={"content": {"body": "y"}},
        headers=auth_headers(admin_token),
    )
    client.delete(f"/api/admin/lesson-content/{block['id']}", headers=auth_headers(admin_token))

    with app.app_context():
        from app.models.audit_log import AuditLog

        # category create, lesson create, block create, block update, block delete = 5
        assert AuditLog.query.count() == 5

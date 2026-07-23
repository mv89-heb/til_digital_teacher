def test_create_category_as_admin(client, admin_token, auth_headers):
    resp = client.post(
        "/api/admin/categories",
        json={"name": "חשיבה כמותית", "type": "quantitative"},
        headers=auth_headers(admin_token),
    )
    assert resp.status_code == 201
    body = resp.get_json()["category"]
    assert body["name"] == "חשיבה כמותית"
    assert body["type"] == "quantitative"


def test_create_category_invalid_type_rejected(client, admin_token, auth_headers):
    resp = client.post(
        "/api/admin/categories",
        json={"name": "x", "type": "not-a-real-type"},
        headers=auth_headers(admin_token),
    )
    assert resp.status_code == 422


def test_create_category_missing_name_rejected(client, admin_token, auth_headers):
    resp = client.post(
        "/api/admin/categories",
        json={"type": "quantitative"},
        headers=auth_headers(admin_token),
    )
    assert resp.status_code == 422


def test_list_categories(client, admin_token, auth_headers):
    client.post(
        "/api/admin/categories",
        json={"name": "A", "type": "quantitative"},
        headers=auth_headers(admin_token),
    )
    resp = client.get("/api/admin/categories", headers=auth_headers(admin_token))
    assert resp.status_code == 200
    assert len(resp.get_json()["categories"]) == 1


def test_update_category(client, admin_token, auth_headers):
    create = client.post(
        "/api/admin/categories",
        json={"name": "A", "type": "quantitative"},
        headers=auth_headers(admin_token),
    )
    category_id = create.get_json()["category"]["id"]

    resp = client.put(
        f"/api/admin/categories/{category_id}",
        json={"name": "B"},
        headers=auth_headers(admin_token),
    )
    assert resp.status_code == 200
    assert resp.get_json()["category"]["name"] == "B"


def test_delete_category(client, admin_token, auth_headers):
    create = client.post(
        "/api/admin/categories",
        json={"name": "A", "type": "quantitative"},
        headers=auth_headers(admin_token),
    )
    category_id = create.get_json()["category"]["id"]

    resp = client.delete(f"/api/admin/categories/{category_id}", headers=auth_headers(admin_token))
    assert resp.status_code == 200

    get_resp = client.get(f"/api/admin/categories/{category_id}", headers=auth_headers(admin_token))
    assert get_resp.status_code == 404


def test_get_nonexistent_category_404(client, admin_token, auth_headers):
    resp = client.get("/api/admin/categories/999", headers=auth_headers(admin_token))
    assert resp.status_code == 404

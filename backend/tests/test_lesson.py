import pytest


@pytest.fixture
def category_id(client, admin_token, auth_headers):
    resp = client.post(
        "/api/admin/categories",
        json={"name": "חשיבה כמותית", "type": "quantitative"},
        headers=auth_headers(admin_token),
    )
    return resp.get_json()["category"]["id"]


def test_create_lesson(client, admin_token, auth_headers, category_id):
    resp = client.post(
        "/api/admin/lessons",
        json={"category_id": category_id, "title": "סדרות מספרים", "order": 1},
        headers=auth_headers(admin_token),
    )
    assert resp.status_code == 201
    assert resp.get_json()["lesson"]["title"] == "סדרות מספרים"


def test_create_lesson_missing_category_rejected(client, admin_token, auth_headers):
    resp = client.post(
        "/api/admin/lessons",
        json={"title": "סדרות מספרים"},
        headers=auth_headers(admin_token),
    )
    assert resp.status_code == 422


def test_add_content_block_and_fetch_full_lesson(client, admin_token, auth_headers, category_id):
    lesson_resp = client.post(
        "/api/admin/lessons",
        json={"category_id": category_id, "title": "סדרות מספרים", "order": 1},
        headers=auth_headers(admin_token),
    )
    lesson_id = lesson_resp.get_json()["lesson"]["id"]

    block_resp = client.post(
        f"/api/admin/lessons/{lesson_id}/content",
        json={
            "section": "simple_explanation",
            "block_type": "text",
            "order": 1,
            "content": {"format": "markdown", "body": "הסבר פשוט"},
        },
        headers=auth_headers(admin_token),
    )
    assert block_resp.status_code == 201
    assert block_resp.get_json()["content_block"]["section"] == "simple_explanation"

    full = client.get(f"/api/admin/lessons/{lesson_id}", headers=auth_headers(admin_token))
    blocks = full.get_json()["lesson"]["content_blocks"]
    assert len(blocks) == 1
    assert blocks[0]["type"] == "text"
    assert blocks[0]["content"]["body"] == "הסבר פשוט"


def test_content_block_invalid_section_rejected(client, admin_token, auth_headers, category_id):
    lesson_resp = client.post(
        "/api/admin/lessons",
        json={"category_id": category_id, "title": "L", "order": 1},
        headers=auth_headers(admin_token),
    )
    lesson_id = lesson_resp.get_json()["lesson"]["id"]

    resp = client.post(
        f"/api/admin/lessons/{lesson_id}/content",
        json={"section": "not_a_real_section", "block_type": "text", "content": {}},
        headers=auth_headers(admin_token),
    )
    assert resp.status_code == 422


def test_content_block_invalid_type_rejected(client, admin_token, auth_headers, category_id):
    lesson_resp = client.post(
        "/api/admin/lessons",
        json={"category_id": category_id, "title": "L", "order": 1},
        headers=auth_headers(admin_token),
    )
    lesson_id = lesson_resp.get_json()["lesson"]["id"]

    resp = client.post(
        f"/api/admin/lessons/{lesson_id}/content",
        json={"section": "summary", "block_type": "not_a_real_type", "content": {}},
        headers=auth_headers(admin_token),
    )
    assert resp.status_code == 422


def test_delete_content_block(client, admin_token, auth_headers, category_id):
    lesson_resp = client.post(
        "/api/admin/lessons",
        json={"category_id": category_id, "title": "L", "order": 1},
        headers=auth_headers(admin_token),
    )
    lesson_id = lesson_resp.get_json()["lesson"]["id"]
    block_resp = client.post(
        f"/api/admin/lessons/{lesson_id}/content",
        json={"section": "summary", "block_type": "text", "content": {"body": "x"}},
        headers=auth_headers(admin_token),
    )
    block_id = block_resp.get_json()["content_block"]["id"]

    resp = client.delete(f"/api/admin/lesson-content/{block_id}", headers=auth_headers(admin_token))
    assert resp.status_code == 200

    full = client.get(f"/api/admin/lessons/{lesson_id}", headers=auth_headers(admin_token))
    assert full.get_json()["lesson"]["content_blocks"] == []


def test_delete_lesson_cascades_content_blocks(client, admin_token, auth_headers, category_id, app):
    lesson_resp = client.post(
        "/api/admin/lessons",
        json={"category_id": category_id, "title": "L", "order": 1},
        headers=auth_headers(admin_token),
    )
    lesson_id = lesson_resp.get_json()["lesson"]["id"]
    client.post(
        f"/api/admin/lessons/{lesson_id}/content",
        json={"section": "summary", "block_type": "text", "content": {"body": "x"}},
        headers=auth_headers(admin_token),
    )

    client.delete(f"/api/admin/lessons/{lesson_id}", headers=auth_headers(admin_token))

    with app.app_context():
        from app.models.lesson_content import LessonContent

        assert LessonContent.query.filter_by(lesson_id=lesson_id).count() == 0


def test_lesson_slug_auto_generated_from_hebrew_title(client, admin_token, auth_headers, category_id):
    resp = client.post(
        "/api/admin/lessons",
        json={"category_id": category_id, "title": "סדרות מספרים"},
        headers=auth_headers(admin_token),
    )
    assert resp.status_code == 201
    assert resp.get_json()["lesson"]["slug"] == "סדרות-מספרים"


def test_duplicate_lesson_title_gets_suffixed_slug(client, admin_token, auth_headers, category_id):
    first = client.post(
        "/api/admin/lessons",
        json={"category_id": category_id, "title": "סדרות מספרים"},
        headers=auth_headers(admin_token),
    ).get_json()["lesson"]
    second = client.post(
        "/api/admin/lessons",
        json={"category_id": category_id, "title": "סדרות מספרים"},
        headers=auth_headers(admin_token),
    ).get_json()["lesson"]

    assert first["slug"] != second["slug"]
    assert second["slug"] == "סדרות-מספרים-2"


def test_explicit_duplicate_slug_rejected(client, admin_token, auth_headers, category_id):
    client.post(
        "/api/admin/lessons",
        json={"category_id": category_id, "title": "A", "slug": "my-slug"},
        headers=auth_headers(admin_token),
    )
    resp = client.post(
        "/api/admin/lessons",
        json={"category_id": category_id, "title": "B", "slug": "my-slug"},
        headers=auth_headers(admin_token),
    )
    assert resp.status_code == 409


def test_lesson_defaults_to_draft_status(client, admin_token, auth_headers, category_id):
    resp = client.post(
        "/api/admin/lessons",
        json={"category_id": category_id, "title": "A"},
        headers=auth_headers(admin_token),
    )
    assert resp.get_json()["lesson"]["status"] == "draft"


def test_text_block_missing_body_rejected(client, admin_token, auth_headers, category_id):
    lesson_id = client.post(
        "/api/admin/lessons",
        json={"category_id": category_id, "title": "L"},
        headers=auth_headers(admin_token),
    ).get_json()["lesson"]["id"]

    resp = client.post(
        f"/api/admin/lessons/{lesson_id}/content",
        json={"section": "summary", "block_type": "text", "content": {"wrong_key": "x"}},
        headers=auth_headers(admin_token),
    )
    assert resp.status_code == 422


def test_image_block_missing_url_rejected(client, admin_token, auth_headers, category_id):
    lesson_id = client.post(
        "/api/admin/lessons",
        json={"category_id": category_id, "title": "L"},
        headers=auth_headers(admin_token),
    ).get_json()["lesson"]["id"]

    resp = client.post(
        f"/api/admin/lessons/{lesson_id}/content",
        json={"section": "summary", "block_type": "image", "content": {"caption": "x"}},
        headers=auth_headers(admin_token),
    )
    assert resp.status_code == 422


def test_table_block_requires_headers_and_rows(client, admin_token, auth_headers, category_id):
    lesson_id = client.post(
        "/api/admin/lessons",
        json={"category_id": category_id, "title": "L"},
        headers=auth_headers(admin_token),
    ).get_json()["lesson"]["id"]

    resp = client.post(
        f"/api/admin/lessons/{lesson_id}/content",
        json={"section": "summary", "block_type": "table", "content": {"headers": ["a"]}},
        headers=auth_headers(admin_token),
    )
    assert resp.status_code == 422

    ok = client.post(
        f"/api/admin/lessons/{lesson_id}/content",
        json={
            "section": "summary",
            "block_type": "table",
            "content": {"headers": ["a", "b"], "rows": [[1, 2]]},
        },
        headers=auth_headers(admin_token),
    )
    assert ok.status_code == 201


def test_formula_block_requires_latex(client, admin_token, auth_headers, category_id):
    lesson_id = client.post(
        "/api/admin/lessons",
        json={"category_id": category_id, "title": "L"},
        headers=auth_headers(admin_token),
    ).get_json()["lesson"]["id"]

    resp = client.post(
        f"/api/admin/lessons/{lesson_id}/content",
        json={"section": "summary", "block_type": "formula", "content": {}},
        headers=auth_headers(admin_token),
    )
    assert resp.status_code == 422


def test_update_block_content_revalidates_against_effective_type(
    client, admin_token, auth_headers, category_id
):
    lesson_id = client.post(
        "/api/admin/lessons",
        json={"category_id": category_id, "title": "L"},
        headers=auth_headers(admin_token),
    ).get_json()["lesson"]["id"]
    block = client.post(
        f"/api/admin/lessons/{lesson_id}/content",
        json={"section": "summary", "block_type": "text", "content": {"body": "x"}},
        headers=auth_headers(admin_token),
    ).get_json()["content_block"]

    # switching block_type to "formula" without a "latex" key must fail
    resp = client.put(
        f"/api/admin/lesson-content/{block['id']}",
        json={"block_type": "formula"},
        headers=auth_headers(admin_token),
    )
    assert resp.status_code == 422

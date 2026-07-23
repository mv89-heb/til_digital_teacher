import pytest


@pytest.fixture
def category_id(client, admin_token, auth_headers):
    resp = client.post(
        "/api/admin/categories",
        json={"name": "חשיבה כמותית", "type": "quantitative", "status": "published"},
        headers=auth_headers(admin_token),
    )
    return resp.get_json()["category"]["id"]


def test_create_question_with_answers(client, admin_token, auth_headers, category_id):
    resp = client.post(
        "/api/admin/questions",
        json={
            "category_id": category_id,
            "difficulty": "easy",
            "body": {"format": "markdown", "body": "2, 5, 8, 11, ?"},
            "solution_text": {"format": "markdown", "body": "הפרש קבוע 3"},
            "recommended_time_seconds": 8,
            "answers": [
                {"answer_text": "14", "is_correct": True},
                {"answer_text": "13", "is_correct": False},
            ],
        },
        headers=auth_headers(admin_token),
    )
    assert resp.status_code == 201
    question = resp.get_json()["question"]
    assert len(question["answers"]) == 2
    assert question["answers"][0]["answer_text"] == "14"
    assert question["status"] == "draft"  # default


def test_create_question_missing_difficulty_rejected(client, admin_token, auth_headers, category_id):
    resp = client.post(
        "/api/admin/questions",
        json={
            "category_id": category_id,
            "body": {"body": "x"},
            "solution_text": {"body": "y"},
        },
        headers=auth_headers(admin_token),
    )
    assert resp.status_code == 422


def test_create_question_two_correct_answers_rejected(client, admin_token, auth_headers, category_id):
    resp = client.post(
        "/api/admin/questions",
        json={
            "category_id": category_id,
            "difficulty": "easy",
            "body": {"body": "x"},
            "solution_text": {"body": "y"},
            "answers": [
                {"answer_text": "A", "is_correct": True},
                {"answer_text": "B", "is_correct": True},
            ],
        },
        headers=auth_headers(admin_token),
    )
    assert resp.status_code == 422


def test_add_second_correct_answer_rejected(client, admin_token, auth_headers, category_id):
    question = client.post(
        "/api/admin/questions",
        json={
            "category_id": category_id,
            "difficulty": "easy",
            "body": {"body": "x"},
            "solution_text": {"body": "y"},
            "answers": [{"answer_text": "A", "is_correct": True}],
        },
        headers=auth_headers(admin_token),
    ).get_json()["question"]

    resp = client.post(
        f"/api/admin/questions/{question['id']}/answers",
        json={"answer_text": "B", "is_correct": True},
        headers=auth_headers(admin_token),
    )
    assert resp.status_code == 409


def test_update_answer_to_correct_when_another_already_correct_rejected(
    client, admin_token, auth_headers, category_id
):
    question = client.post(
        "/api/admin/questions",
        json={
            "category_id": category_id,
            "difficulty": "easy",
            "body": {"body": "x"},
            "solution_text": {"body": "y"},
            "answers": [
                {"answer_text": "A", "is_correct": True},
                {"answer_text": "B", "is_correct": False},
            ],
        },
        headers=auth_headers(admin_token),
    ).get_json()["question"]
    second_answer_id = question["answers"][1]["id"]

    resp = client.put(
        f"/api/admin/answers/{second_answer_id}",
        json={"is_correct": True},
        headers=auth_headers(admin_token),
    )
    assert resp.status_code == 409


def test_delete_question_cascades_answers(client, admin_token, auth_headers, category_id, app):
    question = client.post(
        "/api/admin/questions",
        json={
            "category_id": category_id,
            "difficulty": "easy",
            "body": {"body": "x"},
            "solution_text": {"body": "y"},
            "answers": [{"answer_text": "A", "is_correct": True}],
        },
        headers=auth_headers(admin_token),
    ).get_json()["question"]

    client.delete(f"/api/admin/questions/{question['id']}", headers=auth_headers(admin_token))

    with app.app_context():
        from app.models.answer import Answer

        assert Answer.query.filter_by(question_id=question["id"]).count() == 0


def test_student_cannot_create_question(client, student_token, auth_headers, category_id):
    resp = client.post(
        "/api/admin/questions",
        json={"category_id": category_id, "difficulty": "easy", "body": {}, "solution_text": {}},
        headers=auth_headers(student_token),
    )
    assert resp.status_code == 403


def test_embedded_question_block_requires_existing_question(client, admin_token, auth_headers, category_id):
    lesson_id = client.post(
        "/api/admin/lessons",
        json={"category_id": category_id, "title": "L"},
        headers=auth_headers(admin_token),
    ).get_json()["lesson"]["id"]

    resp = client.post(
        f"/api/admin/lessons/{lesson_id}/content",
        json={"section": "guided_practice", "block_type": "embedded_question", "content": {"question_id": 999}},
        headers=auth_headers(admin_token),
    )
    assert resp.status_code == 404


def test_embedded_question_resolved_in_admin_lesson_get(client, admin_token, auth_headers, category_id):
    lesson_id = client.post(
        "/api/admin/lessons",
        json={"category_id": category_id, "title": "L"},
        headers=auth_headers(admin_token),
    ).get_json()["lesson"]["id"]

    question = client.post(
        "/api/admin/questions",
        json={
            "category_id": category_id,
            "difficulty": "easy",
            "body": {"body": "2,4,6,?"},
            "solution_text": {"body": "8"},
            "answers": [{"answer_text": "8", "is_correct": True}],
        },
        headers=auth_headers(admin_token),
    ).get_json()["question"]

    client.post(
        f"/api/admin/lessons/{lesson_id}/content",
        json={
            "section": "guided_practice",
            "block_type": "embedded_question",
            "content": {"question_id": question["id"]},
        },
        headers=auth_headers(admin_token),
    )

    resp = client.get(f"/api/admin/lessons/{lesson_id}", headers=auth_headers(admin_token))
    block = resp.get_json()["lesson"]["content_blocks"][0]
    assert block["question"]["id"] == question["id"]
    assert block["question"]["answers"][0]["answer_text"] == "8"


def test_embedded_draft_question_hidden_on_public_api(client, admin_token, auth_headers, category_id):
    lesson_id = client.post(
        "/api/admin/lessons",
        json={"category_id": category_id, "title": "L", "status": "published"},
        headers=auth_headers(admin_token),
    ).get_json()["lesson"]["id"]

    question = client.post(  # status defaults to draft
        "/api/admin/questions",
        json={
            "category_id": category_id,
            "difficulty": "easy",
            "body": {"body": "x"},
            "solution_text": {"body": "y"},
            "answers": [{"answer_text": "A", "is_correct": True}],
        },
        headers=auth_headers(admin_token),
    ).get_json()["question"]

    client.post(
        f"/api/admin/lessons/{lesson_id}/content",
        json={
            "section": "guided_practice",
            "block_type": "embedded_question",
            "content": {"question_id": question["id"]},
        },
        headers=auth_headers(admin_token),
    )

    resp = client.get(f"/api/learning/lessons/{lesson_id}")
    block = resp.get_json()["lesson"]["content_blocks"][0]
    assert block["question"] is None


def test_embedded_published_question_visible_on_public_api(client, admin_token, auth_headers, category_id):
    lesson_id = client.post(
        "/api/admin/lessons",
        json={"category_id": category_id, "title": "L", "status": "published"},
        headers=auth_headers(admin_token),
    ).get_json()["lesson"]["id"]

    question = client.post(
        "/api/admin/questions",
        json={
            "category_id": category_id,
            "difficulty": "easy",
            "status": "published",
            "body": {"body": "x"},
            "solution_text": {"body": "y"},
            "answers": [
                {"answer_text": "A", "is_correct": True, "explanation_if_selected": {"body": "right"}},
                {"answer_text": "B", "is_correct": False, "explanation_if_selected": {"body": "wrong"}},
            ],
        },
        headers=auth_headers(admin_token),
    ).get_json()["question"]

    client.post(
        f"/api/admin/lessons/{lesson_id}/content",
        json={
            "section": "guided_practice",
            "block_type": "embedded_question",
            "content": {"question_id": question["id"]},
        },
        headers=auth_headers(admin_token),
    )

    resp = client.get(f"/api/learning/lessons/{lesson_id}")
    block = resp.get_json()["lesson"]["content_blocks"][0]
    assert block["question"]["id"] == question["id"]
    assert block["question"]["answers"][0]["answer_text"] == "A"

    # SECURITY: the public API must never leak which answer is correct, nor
    # the explanation, nor the solution text — only the server (via
    # /questions/<id>/submit) may reveal these.
    for answer in block["question"]["answers"]:
        assert "is_correct" not in answer
        assert "explanation_if_selected" not in answer
    assert block["question"]["solution_text"] is None


def test_admin_lesson_get_still_reveals_correct_answer(client, admin_token, auth_headers, category_id):
    lesson_id = client.post(
        "/api/admin/lessons",
        json={"category_id": category_id, "title": "L"},
        headers=auth_headers(admin_token),
    ).get_json()["lesson"]["id"]

    question = client.post(
        "/api/admin/questions",
        json={
            "category_id": category_id,
            "difficulty": "easy",
            "body": {"body": "x"},
            "solution_text": {"body": "y"},
            "answers": [{"answer_text": "A", "is_correct": True}],
        },
        headers=auth_headers(admin_token),
    ).get_json()["question"]

    client.post(
        f"/api/admin/lessons/{lesson_id}/content",
        json={
            "section": "guided_practice",
            "block_type": "embedded_question",
            "content": {"question_id": question["id"]},
        },
        headers=auth_headers(admin_token),
    )

    resp = client.get(f"/api/admin/lessons/{lesson_id}", headers=auth_headers(admin_token))
    block = resp.get_json()["lesson"]["content_blocks"][0]
    # admin authoring view still needs to see the correct answer
    assert block["question"]["answers"][0]["is_correct"] is True
    assert block["question"]["solution_text"] == {"body": "y"}


def test_audit_log_written_for_question_create(client, admin_token, auth_headers, category_id, app):
    question = client.post(
        "/api/admin/questions",
        json={
            "category_id": category_id,
            "difficulty": "easy",
            "body": {"body": "x"},
            "solution_text": {"body": "y"},
        },
        headers=auth_headers(admin_token),
    ).get_json()["question"]

    with app.app_context():
        from app.models.audit_log import AuditLog

        entry = AuditLog.query.filter_by(entity_type="Question", entity_id=question["id"], action="create").first()
        assert entry is not None

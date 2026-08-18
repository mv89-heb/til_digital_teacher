import pytest


@pytest.fixture
def adaptive_questions(client, admin_token, auth_headers):
    category = client.post(
        "/api/admin/categories",
        json={"name": "אדפטיבי", "type": "quantitative", "status": "published"},
        headers=auth_headers(admin_token),
    ).get_json()["category"]

    questions = []
    for index, skill in enumerate(("שברים", "שברים", "אחוזים")):
        response = client.post(
            "/api/admin/questions",
            json={
                "category_id": category["id"],
                "difficulty": "medium",
                "status": "published",
                "body": {"body": f"שאלה {index + 1}"},
                "solution_text": {"body": "פתרון נסתר"},
                "metadata": {"skill": skill},
                "answers": [
                    {"answer_text": "A", "is_correct": True},
                    {"answer_text": "B", "is_correct": False},
                ],
            },
            headers=auth_headers(admin_token),
        )
        assert response.status_code in (200, 201)
        questions.append(response.get_json()["question"])
    return {"category": category, "questions": questions}


def test_adaptive_endpoint_is_secure_and_returns_target(
    client, student_token, auth_headers, adaptive_questions
):
    response = client.get(
        "/api/learning/practice/questions?mode=adaptive&limit=3",
        headers=auth_headers(student_token),
    )
    assert response.status_code == 200
    body = response.get_json()
    assert body["mode"] == "adaptive"
    assert "target" in body
    assert "questions" in body
    for question in body["questions"]:
        assert question["solution_text"] is None
        for answer in question["answers"]:
            assert "is_correct" not in answer


def test_adaptive_profile_updates_after_wrong_answer(
    client, student_token, auth_headers, adaptive_questions
):
    questions = adaptive_questions["questions"]
    wrong_answer_id = next(a["id"] for a in questions[0]["answers"] if a["answer_text"] == "B")
    response = client.post(
        f"/api/learning/questions/{questions[0]['id']}/submit",
        json={"answer_id": wrong_answer_id},
        headers=auth_headers(student_token),
    )
    assert response.status_code == 200

    adaptive = client.get(
        "/api/learning/practice/questions?mode=adaptive&limit=3",
        headers=auth_headers(student_token),
    )
    assert adaptive.status_code == 200
    body = adaptive.get_json()
    assert body["profile"]["attempts_considered"] >= 1
    assert body["target"]["skill"] is not None

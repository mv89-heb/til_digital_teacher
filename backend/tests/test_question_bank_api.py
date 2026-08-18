def test_question_bank_requires_auth(client):
    response = client.get("/api/learning/question-bank")
    assert response.status_code == 401


def test_question_bank_hides_correct_answers_and_solution(
    client, admin_token, student_token, auth_headers
):
    category = client.post(
        "/api/admin/categories",
        json={"name": "מאגר", "type": "quantitative", "status": "published"},
        headers=auth_headers(admin_token),
    ).get_json()["category"]

    client.post(
        "/api/admin/questions",
        json={
            "category_id": category["id"],
            "difficulty": "medium",
            "status": "published",
            "body": {"format": "markdown", "body": "מהו 2+2?"},
            "solution_text": {"format": "markdown", "body": "הפתרון הוא 4"},
            "metadata": {
                "bank_key": "QB-001",
                "main_category": "חשיבה כמותית",
                "skill": "חישוב",
            },
            "answers": [
                {"answer_text": "3", "is_correct": False},
                {"answer_text": "4", "is_correct": True},
            ],
        },
        headers=auth_headers(admin_token),
    )

    response = client.get(
        "/api/learning/question-bank?search=QB-001",
        headers=auth_headers(student_token),
    )
    assert response.status_code == 200
    payload = response.get_json()
    assert payload["total"] == 1

    question = payload["questions"][0]
    assert question["bank_key"] == "QB-001"
    assert question["solution_text"] is None
    assert all("is_correct" not in answer for answer in question["answers"])
    assert all("explanation_if_selected" not in answer for answer in question["answers"])


def test_question_bank_filters_by_difficulty_and_search(
    client, admin_token, student_token, auth_headers
):
    category = client.post(
        "/api/admin/categories",
        json={"name": "סינון", "type": "quantitative", "status": "published"},
        headers=auth_headers(admin_token),
    ).get_json()["category"]

    for difficulty, bank_key in (("easy", "EASY-1"), ("exam", "EXAM-1")):
        client.post(
            "/api/admin/questions",
            json={
                "category_id": category["id"],
                "difficulty": difficulty,
                "status": "published",
                "body": {"format": "markdown", "body": bank_key},
                "solution_text": {"format": "markdown", "body": "פתרון"},
                "metadata": {"bank_key": bank_key},
                "answers": [{"answer_text": "א", "is_correct": True}],
            },
            headers=auth_headers(admin_token),
        )

    response = client.get(
        "/api/learning/question-bank?difficulty=exam&search=EXAM-1",
        headers=auth_headers(student_token),
    )
    assert response.status_code == 200
    payload = response.get_json()
    assert payload["total"] == 1
    assert payload["questions"][0]["difficulty"] == "exam"
    assert payload["questions"][0]["bank_key"] == "EXAM-1"

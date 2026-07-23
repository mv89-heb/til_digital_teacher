import pytest


@pytest.fixture
def published_lesson_with_question(client, admin_token, auth_headers):
    category = client.post(
        "/api/admin/categories",
        json={"name": "חשיבה כמותית", "type": "quantitative", "status": "published"},
        headers=auth_headers(admin_token),
    ).get_json()["category"]

    lesson = client.post(
        "/api/admin/lessons",
        json={"category_id": category["id"], "title": "L", "status": "published"},
        headers=auth_headers(admin_token),
    ).get_json()["lesson"]

    question = client.post(
        "/api/admin/questions",
        json={
            "category_id": category["id"],
            "difficulty": "easy",
            "status": "published",
            "body": {"body": "2, 4, 6, ?"},
            "solution_text": {"body": "הפרש קבוע 2"},
            "answers": [
                {"answer_text": "8", "is_correct": True, "explanation_if_selected": {"body": "נכון!"}},
                {"answer_text": "7", "is_correct": False, "explanation_if_selected": {"body": "קרוב"}},
            ],
        },
        headers=auth_headers(admin_token),
    ).get_json()["question"]

    return {"lesson": lesson, "question": question}


def test_submit_correct_answer_awards_xp(client, student_token, auth_headers, published_lesson_with_question):
    question = published_lesson_with_question["question"]
    correct_answer_id = next(a["id"] for a in question["answers"] if a["answer_text"] == "8")

    resp = client.post(
        f"/api/learning/questions/{question['id']}/submit",
        json={"answer_id": correct_answer_id},
        headers=auth_headers(student_token),
    )
    assert resp.status_code == 200
    body = resp.get_json()
    assert body["is_correct"] is True
    assert body["xp_earned"] == 10
    assert body["xp_total"] == 10
    assert body["correct_answer_id"] == correct_answer_id


def test_submit_wrong_answer_no_xp(client, student_token, auth_headers, published_lesson_with_question):
    question = published_lesson_with_question["question"]
    wrong_answer_id = next(a["id"] for a in question["answers"] if a["answer_text"] == "7")

    resp = client.post(
        f"/api/learning/questions/{question['id']}/submit",
        json={"answer_id": wrong_answer_id},
        headers=auth_headers(student_token),
    )
    assert resp.status_code == 200
    body = resp.get_json()
    assert body["is_correct"] is False
    assert body["xp_earned"] == 0
    assert body["xp_total"] is None
    # correct_answer_id still revealed after an attempt, so the UI can highlight it
    assert body["correct_answer_id"] is not None


def test_submit_requires_auth(client, published_lesson_with_question):
    question = published_lesson_with_question["question"]
    answer_id = question["answers"][0]["id"]

    resp = client.post(f"/api/learning/questions/{question['id']}/submit", json={"answer_id": answer_id})
    assert resp.status_code == 401


def test_submit_answer_not_belonging_to_question_rejected(
    client, student_token, auth_headers, admin_token, published_lesson_with_question
):
    other_question = client.post(
        "/api/admin/questions",
        json={
            "category_id": published_lesson_with_question["question"]["category_id"],
            "difficulty": "easy",
            "status": "published",
            "body": {"body": "x"},
            "solution_text": {"body": "y"},
            "answers": [{"answer_text": "Z", "is_correct": True}],
        },
        headers=auth_headers(admin_token),
    ).get_json()["question"]
    foreign_answer_id = other_question["answers"][0]["id"]

    question = published_lesson_with_question["question"]
    resp = client.post(
        f"/api/learning/questions/{question['id']}/submit",
        json={"answer_id": foreign_answer_id},
        headers=auth_headers(student_token),
    )
    assert resp.status_code == 422


def test_practice_attempt_recorded(client, student_token, auth_headers, published_lesson_with_question, app):
    question = published_lesson_with_question["question"]
    answer_id = question["answers"][0]["id"]

    client.post(
        f"/api/learning/questions/{question['id']}/submit",
        json={"answer_id": answer_id},
        headers=auth_headers(student_token),
    )

    with app.app_context():
        from app.models.practice_attempt import PracticeAttempt

        assert PracticeAttempt.query.filter_by(question_id=question["id"]).count() == 1


def test_complete_lesson_awards_xp_once(client, student_token, auth_headers, published_lesson_with_question):
    lesson = published_lesson_with_question["lesson"]

    first = client.post(
        f"/api/learning/lessons/{lesson['id']}/complete", headers=auth_headers(student_token)
    )
    assert first.status_code == 200
    assert first.get_json()["progress"]["completed"] is True
    assert first.get_json()["progress"]["xp_earned"] == 50

    # completing again must NOT award XP a second time
    second = client.post(
        f"/api/learning/lessons/{lesson['id']}/complete", headers=auth_headers(student_token)
    )
    assert second.get_json()["progress"]["xp_earned"] == 50

    me = client.get("/api/auth/me", headers=auth_headers(student_token))
    assert me.get_json()["user"]["xp_total"] == 50


def test_complete_lesson_requires_auth(client, published_lesson_with_question):
    lesson = published_lesson_with_question["lesson"]
    resp = client.post(f"/api/learning/lessons/{lesson['id']}/complete")
    assert resp.status_code == 401


def test_get_lesson_progress_default_state(client, student_token, auth_headers, published_lesson_with_question):
    lesson = published_lesson_with_question["lesson"]
    resp = client.get(f"/api/learning/lessons/{lesson['id']}/progress", headers=auth_headers(student_token))
    assert resp.status_code == 200
    assert resp.get_json()["progress"]["completed"] is False


def test_get_lesson_progress_after_completion(client, student_token, auth_headers, published_lesson_with_question):
    lesson = published_lesson_with_question["lesson"]
    client.post(f"/api/learning/lessons/{lesson['id']}/complete", headers=auth_headers(student_token))

    resp = client.get(f"/api/learning/lessons/{lesson['id']}/progress", headers=auth_headers(student_token))
    assert resp.get_json()["progress"]["completed"] is True


def test_resubmitting_same_correct_answer_does_not_double_award_xp(
    client, student_token, auth_headers, published_lesson_with_question
):
    question = published_lesson_with_question["question"]
    correct_answer_id = next(a["id"] for a in question["answers"] if a["answer_text"] == "8")

    first = client.post(
        f"/api/learning/questions/{question['id']}/submit",
        json={"answer_id": correct_answer_id},
        headers=auth_headers(student_token),
    )
    assert first.get_json()["xp_earned"] == 10

    second = client.post(
        f"/api/learning/questions/{question['id']}/submit",
        json={"answer_id": correct_answer_id},
        headers=auth_headers(student_token),
    )
    assert second.get_json()["is_correct"] is True
    assert second.get_json()["xp_earned"] == 0  # already earned XP for this question once

    me = client.get("/api/auth/me", headers=auth_headers(student_token))
    assert me.get_json()["user"]["xp_total"] == 10


def test_total_xp_accumulates_across_questions_and_lesson(
    client, student_token, auth_headers, published_lesson_with_question
):
    question = published_lesson_with_question["question"]
    lesson = published_lesson_with_question["lesson"]
    correct_answer_id = next(a["id"] for a in question["answers"] if a["answer_text"] == "8")

    client.post(
        f"/api/learning/questions/{question['id']}/submit",
        json={"answer_id": correct_answer_id},
        headers=auth_headers(student_token),
    )
    client.post(f"/api/learning/lessons/{lesson['id']}/complete", headers=auth_headers(student_token))

    me = client.get("/api/auth/me", headers=auth_headers(student_token))
    assert me.get_json()["user"]["xp_total"] == 60  # 10 (question) + 50 (lesson)

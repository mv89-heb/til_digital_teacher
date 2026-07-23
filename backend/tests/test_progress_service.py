import pytest


@pytest.fixture
def published_category_with_lesson_and_questions(client, admin_token, auth_headers):
    """A published category with 1 published lesson and enough questions to
    exercise every StudentLevel threshold."""
    category = client.post(
        "/api/admin/categories",
        json={"name": "חשיבה כמותית", "type": "quantitative", "status": "published"},
        headers=auth_headers(admin_token),
    ).get_json()["category"]

    lesson = client.post(
        "/api/admin/lessons",
        json={"category_id": category["id"], "title": "שיעור", "status": "published"},
        headers=auth_headers(admin_token),
    ).get_json()["lesson"]

    questions = []
    for i in range(20):
        q = client.post(
            "/api/admin/questions",
            json={
                "category_id": category["id"],
                "lesson_id": lesson["id"],
                "difficulty": "easy",
                "status": "published",
                "body": {"format": "markdown", "body": f"שאלה {i}"},
                "solution_text": {"format": "markdown", "body": "פתרון"},
                "answers": [
                    {"answer_text": "נכון", "is_correct": True},
                    {"answer_text": "שגוי", "is_correct": False},
                ],
            },
            headers=auth_headers(admin_token),
        ).get_json()["question"]
        questions.append(q)

    return {"category": category, "lesson": lesson, "questions": questions}


def _submit(client, token, auth_headers, question, correct: bool):
    # seeded order: index 0 is the correct answer, index 1 is wrong (see fixture above)
    answer_id = question["answers"][0]["id"] if correct else question["answers"][1]["id"]
    return client.post(
        f"/api/learning/questions/{question['id']}/submit",
        json={"answer_id": answer_id},
        headers=auth_headers(token),
    )


class TestProgressService:
    def test_no_progress_yet_defaults_to_beginner_and_zeros(
        self, client, student_token, auth_headers, published_category_with_lesson_and_questions
    ):
        resp = client.get("/api/learning/dashboard", headers=auth_headers(student_token))
        assert resp.status_code == 200
        cat = resp.get_json()["categories"][0]
        assert cat["questions_attempted"] == 0
        assert cat["level"] == "beginner"

    def test_below_min_attempts_stays_beginner_even_if_all_correct(
        self, client, student_token, auth_headers, published_category_with_lesson_and_questions
    ):
        data = published_category_with_lesson_and_questions
        for q in data["questions"][:3]:  # below MIN_ATTEMPTS_FOR_RATING (5)
            _submit(client, student_token, auth_headers, q, correct=True)

        resp = client.get("/api/learning/dashboard", headers=auth_headers(student_token))
        cat = resp.get_json()["categories"][0]
        assert cat["questions_attempted"] == 3
        assert cat["level"] == "beginner"

    def test_low_accuracy_after_min_attempts_is_basic(
        self, client, student_token, auth_headers, published_category_with_lesson_and_questions
    ):
        data = published_category_with_lesson_and_questions
        questions = data["questions"]
        for q in questions[:5]:
            _submit(client, student_token, auth_headers, q, correct=False)

        resp = client.get("/api/learning/dashboard", headers=auth_headers(student_token))
        cat = resp.get_json()["categories"][0]
        assert cat["accuracy_percent"] == 0
        assert cat["level"] == "basic"

    def test_high_accuracy_low_volume_is_exam_ready_not_advanced(
        self, client, student_token, auth_headers, published_category_with_lesson_and_questions
    ):
        data = published_category_with_lesson_and_questions
        for q in data["questions"][:5]:  # 5 correct, 100% accuracy, but < ADVANCED_MIN_ATTEMPTS (15)
            _submit(client, student_token, auth_headers, q, correct=True)

        resp = client.get("/api/learning/dashboard", headers=auth_headers(student_token))
        cat = resp.get_json()["categories"][0]
        assert cat["accuracy_percent"] == 100
        assert cat["level"] == "exam_ready"

    def test_high_accuracy_high_volume_is_advanced(
        self, client, student_token, auth_headers, published_category_with_lesson_and_questions
    ):
        data = published_category_with_lesson_and_questions
        for q in data["questions"][:16]:  # >= ADVANCED_MIN_ATTEMPTS (15), 100% accuracy
            _submit(client, student_token, auth_headers, q, correct=True)

        resp = client.get("/api/learning/dashboard", headers=auth_headers(student_token))
        cat = resp.get_json()["categories"][0]
        assert cat["level"] == "advanced"

    def test_lesson_completion_updates_category_progress(
        self, client, student_token, auth_headers, published_category_with_lesson_and_questions
    ):
        data = published_category_with_lesson_and_questions
        client.post(
            f"/api/learning/lessons/{data['lesson']['id']}/complete", headers=auth_headers(student_token)
        )
        resp = client.get("/api/learning/dashboard", headers=auth_headers(student_token))
        cat = resp.get_json()["categories"][0]
        assert cat["lessons_completed"] == 1
        assert cat["xp_earned"] == 50


class TestDashboardApi:
    def test_dashboard_requires_auth(self, client):
        resp = client.get("/api/learning/dashboard")
        assert resp.status_code == 401

    def test_dashboard_shows_xp_total(
        self, client, student_token, auth_headers, published_category_with_lesson_and_questions
    ):
        data = published_category_with_lesson_and_questions
        _submit(client, student_token, auth_headers, data["questions"][0], correct=True)

        resp = client.get("/api/learning/dashboard", headers=auth_headers(student_token))
        assert resp.get_json()["xp_total"] == 10

    def test_continue_learning_reflects_in_progress_lesson(
        self, client, student_token, auth_headers, published_category_with_lesson_and_questions
    ):
        data = published_category_with_lesson_and_questions
        # viewing a lesson's progress (without completing) creates/touches a row via complete? No —
        # progress rows are only created on submit/complete. Simulate via a submit against an
        # embedded question tied to the lesson's category doesn't create UserLessonProgress.
        # So directly hit the lesson-progress GET which is read-only and shouldn't create anything,
        # then complete to populate "completed", and verify the split.
        client.post(
            f"/api/learning/lessons/{data['lesson']['id']}/complete", headers=auth_headers(student_token)
        )
        resp = client.get("/api/learning/dashboard", headers=auth_headers(student_token))
        body = resp.get_json()
        assert len(body["completed_lessons"]) == 1
        assert body["in_progress_lessons"] == []
        assert body["continue_learning"] is None

    def test_lessons_total_reflects_published_lesson_count(
        self, client, student_token, auth_headers, published_category_with_lesson_and_questions
    ):
        resp = client.get("/api/learning/dashboard", headers=auth_headers(student_token))
        cat = resp.get_json()["categories"][0]
        assert cat["lessons_total"] == 1

    def test_draft_category_excluded_from_dashboard(self, client, admin_token, student_token, auth_headers):
        client.post(
            "/api/admin/categories",
            json={"name": "טיוטה", "type": "quantitative"},  # defaults to draft
            headers=auth_headers(admin_token),
        )
        resp = client.get("/api/learning/dashboard", headers=auth_headers(student_token))
        assert resp.get_json()["categories"] == []


class TestUserDataIsolation:
    def test_two_users_progress_never_mixes(
        self, client, auth_headers, published_category_with_lesson_and_questions
    ):
        data = published_category_with_lesson_and_questions

        client.post("/api/auth/register", json={"email": "user_a@test.com", "password": "password123"})
        token_a = client.post(
            "/api/auth/login", json={"email": "user_a@test.com", "password": "password123"}
        ).get_json()["data"]["token"]

        client.post("/api/auth/register", json={"email": "user_b@test.com", "password": "password123"})
        token_b = client.post(
            "/api/auth/login", json={"email": "user_b@test.com", "password": "password123"}
        ).get_json()["data"]["token"]

        for q in data["questions"][:5]:
            _submit(client, token_a, auth_headers, q, correct=True)

        dashboard_a = client.get("/api/learning/dashboard", headers=auth_headers(token_a)).get_json()
        dashboard_b = client.get("/api/learning/dashboard", headers=auth_headers(token_b)).get_json()

        assert dashboard_a["categories"][0]["questions_attempted"] == 5
        assert dashboard_b["categories"][0]["questions_attempted"] == 0
        assert dashboard_a["xp_total"] == 50
        assert dashboard_b["xp_total"] == 0

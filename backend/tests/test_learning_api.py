def test_get_categories_no_auth_required(client, admin_token, auth_headers):
    client.post(
        "/api/admin/categories",
        json={"name": "חשיבה כמותית", "type": "quantitative", "status": "published"},
        headers=auth_headers(admin_token),
    )

    resp = client.get("/api/learning/categories")
    assert resp.status_code == 200
    assert len(resp.get_json()["categories"]) == 1


def test_draft_category_hidden_from_public_api(client, admin_token, auth_headers):
    client.post(
        "/api/admin/categories",
        json={"name": "טיוטה", "type": "quantitative"},  # status defaults to draft
        headers=auth_headers(admin_token),
    )

    resp = client.get("/api/learning/categories")
    assert resp.status_code == 200
    assert resp.get_json()["categories"] == []


def test_draft_lesson_hidden_from_published_category(client, admin_token, auth_headers):
    cat = client.post(
        "/api/admin/categories",
        json={"name": "A", "type": "quantitative", "status": "published"},
        headers=auth_headers(admin_token),
    ).get_json()["category"]

    client.post(
        "/api/admin/lessons",
        json={"category_id": cat["id"], "title": "טיוטה"},  # draft by default
        headers=auth_headers(admin_token),
    )

    resp = client.get("/api/learning/categories")
    assert resp.get_json()["categories"][0]["lesson_count"] == 0
    assert resp.get_json()["categories"][0]["lessons"] == []


def test_draft_lesson_detail_returns_404_on_public_api(client, admin_token, auth_headers):
    cat = client.post(
        "/api/admin/categories",
        json={"name": "A", "type": "quantitative", "status": "published"},
        headers=auth_headers(admin_token),
    ).get_json()["category"]
    lesson = client.post(
        "/api/admin/lessons",
        json={"category_id": cat["id"], "title": "טיוטה"},
        headers=auth_headers(admin_token),
    ).get_json()["lesson"]

    resp = client.get(f"/api/learning/lessons/{lesson['id']}")
    assert resp.status_code == 404


def test_get_lesson_detail_no_auth_required(client, admin_token, auth_headers):
    cat = client.post(
        "/api/admin/categories",
        json={"name": "חשיבה כמותית", "type": "quantitative", "status": "published"},
        headers=auth_headers(admin_token),
    ).get_json()["category"]

    lesson = client.post(
        "/api/admin/lessons",
        json={"category_id": cat["id"], "title": "סדרות מספרים", "status": "published"},
        headers=auth_headers(admin_token),
    ).get_json()["lesson"]

    client.post(
        f"/api/admin/lessons/{lesson['id']}/content",
        json={
            "section": "simple_explanation",
            "block_type": "text",
            "order": 1,
            "content": {"format": "markdown", "body": "טקסט הסבר"},
        },
        headers=auth_headers(admin_token),
    )

    resp = client.get(f"/api/learning/lessons/{lesson['id']}")
    assert resp.status_code == 200
    data = resp.get_json()["lesson"]
    assert data["title"] == "סדרות מספרים"
    assert data["category"]["name"] == "חשיבה כמותית"
    assert len(data["content_blocks"]) == 1
    assert data["content_blocks"][0]["section"] == "simple_explanation"


def test_get_nonexistent_lesson_404(client):
    resp = client.get("/api/learning/lessons/999")
    assert resp.status_code == 404


def test_seed_data_loads_successfully(app):
    """Runs the actual seed script against the test DB and validates the
    full pedagogical structure it's supposed to produce."""
    with app.app_context():
        from app.models.constants import LessonSection
        from app.models.lesson import Lesson
        from app.models.question import Question
        from seed import seed_demo_data

        summary = seed_demo_data()
        assert summary["lesson_id"] is not None
        assert summary["bank_added"] >= 0
        assert summary["published_questions"] >= 5

        from app.extensions import db
        lesson = db.session.get(Lesson, summary["lesson_id"])
        assert lesson is not None
        sections = {block.section for block in lesson.content_blocks}
        assert sections == {
            LessonSection.SIMPLE_EXPLANATION,
            LessonSection.NORMAL_EXPLANATION,
            LessonSection.SOLVED_EXAMPLE,
            LessonSection.NORMAL_METHOD,
            LessonSection.FAST_METHOD,
            LessonSection.COMMON_MISTAKES,
            LessonSection.SUMMARY,
        }
        assert len(lesson.content_blocks) == 7

        embedded_blocks = [b for b in lesson.content_blocks if b.block_type == "embedded_question"]
        assert embedded_blocks == []

        questions = Question.query.filter_by(lesson_id=lesson.id).all()
        assert len(questions) == 5
        for question in questions:
            assert len(question.answers) == 4
            assert sum(1 for a in question.answers if a.is_correct) == 1

        # re-running must be idempotent
        second_run = seed_demo_data()
        assert second_run["lesson_id"] == summary["lesson_id"]
        assert second_run["bank_added"] == 0
        assert Lesson.query.count() >= 1
        assert Question.query.count() >= 5

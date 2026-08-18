def test_feedback_requires_approval_before_teacher_memory(
    client, student_token, admin_token, auth_headers
):
    student_headers = auth_headers(student_token)
    admin_headers = auth_headers(admin_token)

    create = client.post(
        "/api/learning/teacher/feedback",
        json={
            "student_query": "איך פותרים שברים?",
            "feedback": "המערכת צריכה להדגיש מכנה משותף.",
            "correction": "בחיבור שברים יש להביא למכנה משותף לפני חיבור המונים.",
            "topic": "שברים",
            "skill": "שברים",
            "severity": "medium",
        },
        headers=student_headers,
    )
    assert create.status_code == 201
    feedback_id = create.get_json()["feedback"]["id"]
    assert create.get_json()["feedback"]["status"] == "pending"

    pending = client.post(
        "/api/learning/teacher/teach",
        json={"query": "שברים", "mode": "learn"},
        headers=student_headers,
    )
    assert pending.status_code == 200
    assert feedback_id not in [item["id"] for item in pending.get_json()["memory"]["items"]]

    review = client.post(
        f"/api/learning/teacher/feedback/{feedback_id}/review",
        json={"approved": True, "confidence": 95},
        headers=admin_headers,
    )
    assert review.status_code == 200
    assert review.get_json()["feedback"]["status"] == "approved"

    approved = client.post(
        "/api/learning/teacher/teach",
        json={"query": "שברים", "mode": "learn"},
        headers=student_headers,
    )
    assert approved.status_code == 200
    assert feedback_id in [item["id"] for item in approved.get_json()["memory"]["items"]]

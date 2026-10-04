def test_teacher_modes_are_distinct(client, student_token, auth_headers, app):
    with app.app_context():
        from seed import seed_demo_data
        from app.models.question import Question

        seed_demo_data()
        question = Question.query.first()
        assert question is not None
        question_id = question.id

    headers = auth_headers(student_token)
    responses = {}
    for mode in ("learn", "guided", "practice", "mistake"):
        response = client.post(
            "/api/learning/teacher/teach",
            json={"query": "", "question_id": question_id, "mode": mode},
            headers=headers,
        )
        assert response.status_code == 200
        responses[mode] = response.get_json()
        assert responses[mode]["mode"] == mode
        assert responses[mode]["question"]["solution_text"] is None
        for answer in responses[mode]["question"]["answers"]:
            assert "is_correct" not in answer

    assert responses["guided"]["answer"] != responses["learn"]["answer"]
    assert responses["practice"]["answer"] != responses["guided"]["answer"]
    assert responses["mistake"]["answer"] != responses["practice"]["answer"]
    assert responses["practice"]["question"]["solution_text"] is None

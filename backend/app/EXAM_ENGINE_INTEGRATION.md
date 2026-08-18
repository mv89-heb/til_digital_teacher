# Exam Engine integration

The exam engine is implemented in `app/api/exam_routes.py` and registered by `register_exam_blueprints` in `app/api/exam_registration.py`.

Call this once from `create_app()` after the existing blueprints are registered:

```python
from app.api.exam_registration import register_exam_blueprints
register_exam_blueprints(app)
```

The migration `20260818_exam_engine_hardening.py` must be applied before starting exam sessions.

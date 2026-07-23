# Marshmallow instance lives in app.extensions (single source of truth,
# initialized once in create_app). Re-exported here for convenience so
# schema modules can `from app.schemas import ma`.
from app.extensions import ma

__all__ = ["ma"]

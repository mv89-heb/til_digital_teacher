from datetime import datetime, timedelta, timezone

import jwt
from werkzeug.security import check_password_hash, generate_password_hash

from config import Config
from app.extensions import db
from app.models.user import User
from app.utils.exceptions import AppError


class AuthService:
    SECRET_KEY = Config.SECRET_KEY
    JWT_EXPIRES_DAYS = Config.JWT_EXPIRES_DAYS

    @staticmethod
    def register_user(email: str, password: str) -> dict:
        normalized_email = email.strip().lower()
        if User.query.filter(db.func.lower(User.email) == normalized_email).first():
            raise AppError("Email already exists", status_code=409)

        hashed_password = generate_password_hash(password)
        new_user = User(email=normalized_email, password_hash=hashed_password)
        db.session.add(new_user)
        try:
            db.session.commit()
        except Exception:
            db.session.rollback()
            raise
        return new_user.to_dict()

    @staticmethod
    def login_user(email: str, password: str) -> dict:
        normalized_email = email.strip().lower()
        user = User.query.filter(db.func.lower(User.email) == normalized_email).first()

        if not user:
            raise AppError("Invalid email or password", status_code=401)

        try:
            password_valid = check_password_hash(user.password_hash, password)
        except (TypeError, ValueError):
            password_valid = False

        if not password_valid:
            raise AppError("Invalid email or password", status_code=401)

        if getattr(user, "is_active", True) is False:
            raise AppError("Account is inactive", status_code=403)

        now = datetime.now(timezone.utc)
        payload = {
            "user_id": user.id,
            "iat": now,
            "exp": now + timedelta(days=AuthService.JWT_EXPIRES_DAYS),
        }

        try:
            token = jwt.encode(payload, AuthService.SECRET_KEY, algorithm="HS256")
        except Exception as exc:
            db.session.rollback()
            raise AppError("Authentication configuration error", status_code=500) from exc

        # Authentication must not fail merely because recording the optional
        # last-login timestamp fails. The token is already valid at this point.
        # This also makes staged deployments tolerant of an older database
        # schema while migrations propagate.
        try:
            if hasattr(user, "last_login_at"):
                user.last_login_at = now
                db.session.commit()
        except Exception:
            db.session.rollback()

        return {"user": user.to_dict(), "token": token}

    @staticmethod
    def verify_token(token: str) -> dict:
        try:
            payload = jwt.decode(token, AuthService.SECRET_KEY, algorithms=["HS256"])
        except jwt.ExpiredSignatureError:
            raise AppError("Token expired", status_code=401)
        except jwt.InvalidTokenError:
            raise AppError("Invalid token", status_code=401)

        user_id = payload.get("user_id")
        if not user_id:
            raise AppError("Invalid token", status_code=401)

        user = db.session.get(User, user_id)
        if not user:
            raise AppError("User not found", status_code=401)
        if getattr(user, "is_active", True) is False:
            raise AppError("User not found", status_code=401)

        return user.to_dict()

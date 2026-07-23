import os
from datetime import datetime, timedelta, timezone

import jwt
from werkzeug.security import check_password_hash, generate_password_hash

from app.extensions import db
from app.models.user import User
from app.utils.exceptions import AppError


class AuthService:
    SECRET_KEY = os.getenv("JWT_SECRET", "super-secret-fallback-key")
    JWT_EXPIRES_DAYS = int(os.getenv("JWT_EXPIRES_DAYS", "7"))

    @staticmethod
    def register_user(email: str, password: str) -> dict:
        if User.query.filter_by(email=email).first():
            raise AppError("Email already exists", status_code=409)

        hashed_password = generate_password_hash(password)
        new_user = User(email=email, password_hash=hashed_password)

        db.session.add(new_user)
        db.session.commit()

        return new_user.to_dict()

    @staticmethod
    def login_user(email: str, password: str) -> dict:
        user = User.query.filter_by(email=email).first()
        if not user or not check_password_hash(user.password_hash, password):
            raise AppError("Invalid email or password", status_code=401)

        payload = {
            "user_id": user.id,
            "role": user.role,
            "exp": datetime.now(timezone.utc) + timedelta(days=AuthService.JWT_EXPIRES_DAYS),
        }
        token = jwt.encode(payload, AuthService.SECRET_KEY, algorithm="HS256")

        return {"user": user.to_dict(), "token": token}

    @staticmethod
    def verify_token(token: str) -> dict:
        try:
            payload = jwt.decode(token, AuthService.SECRET_KEY, algorithms=["HS256"])
        except jwt.ExpiredSignatureError:
            raise AppError("Token expired", status_code=401)
        except jwt.InvalidTokenError:
            raise AppError("Invalid token", status_code=401)

        user = db.session.get(User, payload["user_id"])
        if not user:
            raise AppError("User not found", status_code=401)

        return user.to_dict()

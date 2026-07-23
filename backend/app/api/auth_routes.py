from flask import Blueprint, g, jsonify, request

from app.schemas.auth_schema import login_schema, register_schema
from app.services.auth_service import AuthService
from app.utils.decorators import jwt_required

auth_bp = Blueprint("auth", __name__, url_prefix="/api/auth")


@auth_bp.route("/register", methods=["POST"])
def register():
    data = register_schema.load(request.get_json() or {})
    user_data = AuthService.register_user(data["email"], data["password"])
    return jsonify({"message": "User created successfully", "user": user_data}), 201


@auth_bp.route("/login", methods=["POST"])
def login():
    data = login_schema.load(request.get_json() or {})
    login_data = AuthService.login_user(data["email"], data["password"])
    return jsonify({"message": "Login successful", "data": login_data}), 200


@auth_bp.route("/me", methods=["GET"])
@jwt_required
def get_me():
    return jsonify({"user": g.current_user}), 200

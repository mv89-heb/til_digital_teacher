from flask import Blueprint, jsonify

from app.services.content_integrity_service import ContentIntegrityService
from app.utils.decorators import admin_required

content_integrity_bp = Blueprint("content_integrity", __name__, url_prefix="/api/admin/content")


@content_integrity_bp.route("/validate", methods=["GET"])
@admin_required
def validate_content():
    return jsonify(ContentIntegrityService.validate_all()), 200

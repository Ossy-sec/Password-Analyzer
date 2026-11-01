"""Server-side password strength check — used by the analyzer's "verify on
the server too" flow and by registration. The password is only ever held in
memory for the duration of this request; it is never logged or written to
the database."""

from flask import Blueprint, jsonify, request

from security.strength import rate

bp = Blueprint("password", __name__, url_prefix="/api")


@bp.post("/check-password")
def check_password():
    data = request.get_json(silent=True) or {}
    password = data.get("password") or ""
    return jsonify(rate(password))

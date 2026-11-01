"""
Registration, login, logout, and the "who am I" endpoint the login page uses
to skip sign-in when a session already exists.

Login failures are intentionally generic ("Invalid username or password")
regardless of whether the username exists, to avoid revealing which accounts
are registered (user enumeration). Registration is the one place that says
"username already taken" — a common, documented trade-off; see the README's
"Future improvements" for how to remove even that.
"""

import re
from functools import wraps

from flask import Blueprint, current_app, jsonify, request, session

from db import get_db
from security.brute_force import apply_progressive_delay, get_lockout_remaining, record_attempt
from security.password_hashing import hash_password, verify_password
from security.strength import meets_minimum, rate
from timeutils import utc_now_iso

bp = Blueprint("auth", __name__, url_prefix="/api")

USERNAME_RE = re.compile(r"^[a-zA-Z0-9_]{3,32}$")
# Attempted (not necessarily registered) usernames are logged as-is for
# detection purposes, but are capped so an attacker can't stuff arbitrarily
# large strings into the database via unauthenticated login attempts.
MAX_IDENTIFIER_LENGTH = 64

# A hash of a value nobody will ever type, used to keep the login endpoint's
# timing similar whether or not the username exists — so an attacker can't
# tell the two cases apart just by measuring response time.
_DECOY_HASH = hash_password("this-is-not-a-real-password-just-for-timing")


def login_required(view):
    @wraps(view)
    def wrapped(*args, **kwargs):
        if "user_id" not in session:
            return jsonify(error="Authentication required"), 401
        return view(*args, **kwargs)
    return wrapped


@bp.post("/register")
def register():
    data = request.get_json(silent=True) or {}
    username = (data.get("username") or "").strip()
    password = data.get("password") or ""

    if not USERNAME_RE.match(username):
        return jsonify(error="Username must be 3-32 characters: letters, numbers, underscore"), 400

    if len(password) > 128:
        return jsonify(error="Password must be 128 characters or fewer"), 400

    if not meets_minimum(password, current_app.config["MIN_REGISTRATION_RATING"]):
        result = rate(password)
        return jsonify(
            error=f"Password too weak ({result['rating']}). Minimum required: "
                  f"{current_app.config['MIN_REGISTRATION_RATING']}.",
            issues=result["issues"],
        ), 400

    db = get_db()
    existing = db.execute("SELECT 1 FROM users WHERE username = ?", (username,)).fetchone()
    if existing is not None:
        return jsonify(error="Username already taken"), 409

    db.execute(
        "INSERT INTO users (username, password_hash, created_at) VALUES (?, ?, ?)",
        (username, hash_password(password), utc_now_iso()),
    )
    db.commit()
    return jsonify(message="Account created"), 201


@bp.post("/login")
def login():
    data = request.get_json(silent=True) or {}
    username = (data.get("username") or "").strip()[:MAX_IDENTIFIER_LENGTH]
    password = data.get("password") or ""
    ip_address = request.remote_addr or "unknown"
    config = current_app.config

    remaining = get_lockout_remaining(username)
    if remaining > 0:
        response = jsonify(
            error="Account temporarily locked due to repeated failed attempts",
            retry_after_seconds=int(remaining) + 1,
        )
        response.status_code = 429
        response.headers["Retry-After"] = str(int(remaining) + 1)
        return response

    apply_progressive_delay(config, username)

    db = get_db()
    user = db.execute("SELECT * FROM users WHERE username = ?", (username,)).fetchone()

    if user is not None:
        password_ok = verify_password(user["password_hash"], password)
    else:
        # Still run a hash comparison against a decoy so a nonexistent
        # username doesn't respond measurably faster than a wrong password.
        verify_password(_DECOY_HASH, password)
        password_ok = False

    record_attempt(config, username, ip_address, success=password_ok)

    if not password_ok:
        return jsonify(error="Invalid username or password"), 401

    session.clear()
    session["user_id"] = user["id"]
    session["username"] = user["username"]
    return jsonify(message="Logged in", username=user["username"])


@bp.post("/logout")
def logout():
    session.clear()
    return jsonify(message="Logged out")


@bp.get("/me")
@login_required
def me():
    return jsonify(username=session["username"])

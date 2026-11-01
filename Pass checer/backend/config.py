"""
Central place for every tunable value in the app.

Nothing here is hard-coded into the logic that uses it — brute_force.py,
app.py, etc. all read their settings from a Config object, and every value
can be overridden with an environment variable (see .env.example).
"""

import os
from pathlib import Path

from dotenv import load_dotenv

BACKEND_DIR = Path(__file__).resolve().parent
load_dotenv(BACKEND_DIR / ".env")


def _int(name, default):
    return int(os.environ.get(name, default))


def _float(name, default):
    return float(os.environ.get(name, default))


def _bool(name, default):
    raw = os.environ.get(name)
    if raw is None:
        return default
    return raw.strip().lower() in ("1", "true", "yes", "on")


class Config:
    # --- Core Flask / session settings ---
    SECRET_KEY = os.environ.get("SECRET_KEY", "dev-secret-change-me")
    DEBUG = _bool("FLASK_DEBUG", False)

    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = "Lax"
    # Only requires HTTPS when not running on plain localhost/dev.
    SESSION_COOKIE_SECURE = _bool("SESSION_COOKIE_SECURE", False)

    # Reject oversized request bodies outright (e.g. a multi-megabyte
    # "password") before they reach any route handler.
    MAX_CONTENT_LENGTH = 1_000_000  # 1 MB

    # --- Database ---
    DATABASE_PATH = str(BACKEND_DIR / os.environ.get("DATABASE_PATH", "instance/app.db"))

    # --- Brute-force detection thresholds (all overridable via env vars) ---
    BF_WINDOW_SECONDS = _int("BF_WINDOW_SECONDS", 300)
    BF_SUSPICIOUS_THRESHOLD = _int("BF_SUSPICIOUS_THRESHOLD", 5)
    BF_BRUTE_FORCE_THRESHOLD = _int("BF_BRUTE_FORCE_THRESHOLD", 10)
    BF_BASE_LOCKOUT_SECONDS = _int("BF_BASE_LOCKOUT_SECONDS", 30)
    BF_LOCKOUT_MULTIPLIER = _float("BF_LOCKOUT_MULTIPLIER", 2)
    BF_MAX_LOCKOUT_SECONDS = _int("BF_MAX_LOCKOUT_SECONDS", 900)

    # Progressive per-request delay: seconds added per recent failed attempt,
    # capped at BF_MAX_DELAY_SECONDS so the demo server never hangs for long.
    BF_DELAY_PER_ATTEMPT = _float("BF_DELAY_PER_ATTEMPT", 0.25)
    BF_MAX_DELAY_SECONDS = _float("BF_MAX_DELAY_SECONDS", 3.0)

    # Minimum acceptable password strength rating at registration time.
    # Must be one of the ratings returned by security/strength.py.
    MIN_REGISTRATION_RATING = os.environ.get("MIN_REGISTRATION_RATING", "Fair")


class TestConfig(Config):
    """Used by the pytest suite: isolated in-memory DB, debugger off, no
    real cookie-security restrictions that would complicate the test client."""

    TESTING = True
    DATABASE_PATH = ":memory:"
    SECRET_KEY = "test-secret"
    # Keep tests fast and deterministic — no artificial throttling delay.
    BF_DELAY_PER_ATTEMPT = 0
    BF_MAX_DELAY_SECONDS = 0

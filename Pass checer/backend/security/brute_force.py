"""
Brute-force detection and the defensive responses that go with it:
rate limiting (via a short server-side delay), temporary lockout, and
security-event logging. Every threshold is read from app.config, so nothing
here is hard-coded — see config.py / .env.example.

Every login attempt goes through record_attempt(), which logs it and runs
detection.
"""

import time
from datetime import timedelta

from db import get_db
from timeutils import iso, parse_iso, seconds_ago_iso, utc_now, utc_now_iso


def get_lockout_remaining(identifier: str) -> float:
    """Seconds left on any active lockout for this username, or 0 if none."""
    db = get_db()
    row = db.execute(
        "SELECT locked_until FROM users WHERE username = ?", (identifier,)
    ).fetchone()
    if row is None or row["locked_until"] is None:
        return 0.0
    remaining = (parse_iso(row["locked_until"]) - utc_now()).total_seconds()
    return max(0.0, remaining)


def apply_progressive_delay(config, identifier: str) -> None:
    """A small, capped sleep proportional to recent failures — makes rapid
    scripted guessing noticeably slower without blocking the server for long.
    This is a demo-scale technique; a production system would rate-limit at
    the network/proxy layer instead of sleeping inside the request."""
    if config["BF_DELAY_PER_ATTEMPT"] <= 0:
        return
    db = get_db()
    window_start = seconds_ago_iso(config["BF_WINDOW_SECONDS"])
    count = db.execute(
        """SELECT COUNT(*) FROM login_attempts
           WHERE identifier = ? AND success = 0 AND timestamp >= ?""",
        (identifier, window_start),
    ).fetchone()[0]
    delay = min(count * config["BF_DELAY_PER_ATTEMPT"], config["BF_MAX_DELAY_SECONDS"])
    if delay > 0:
        time.sleep(delay)


def _log_event(event_type: str, identifier: str, ip_address: str, details: str, severity: str) -> None:
    db = get_db()
    db.execute(
        """INSERT INTO security_events (event_type, identifier, ip_address, details, severity, timestamp)
           VALUES (?, ?, ?, ?, ?, ?)""",
        (event_type, identifier, ip_address, details, severity, utc_now_iso()),
    )
    db.commit()


def _apply_lockout(config, identifier: str, ip_address: str) -> int:
    db = get_db()
    prior = db.execute(
        """SELECT COUNT(*) FROM security_events
           WHERE identifier = ? AND event_type = 'brute_force_detected'""",
        (identifier,),
    ).fetchone()[0]
    lockout_seconds = min(
        config["BF_BASE_LOCKOUT_SECONDS"] * (config["BF_LOCKOUT_MULTIPLIER"] ** prior),
        config["BF_MAX_LOCKOUT_SECONDS"],
    )
    locked_until = iso(utc_now() + timedelta(seconds=lockout_seconds))
    db.execute("UPDATE users SET locked_until = ? WHERE username = ?", (locked_until, identifier))
    db.commit()
    _log_event(
        "lockout_applied", identifier, ip_address,
        f"Locked for {int(lockout_seconds)}s after repeated brute-force detections", "high",
    )
    return int(lockout_seconds)


def record_attempt(config, identifier: str, ip_address: str, success: bool) -> dict:
    """Records one login attempt and runs it through detection.

    Returns {"status": "normal" | "suspicious" | "brute_force", "failed_count": int}.
    Never receives or stores the password that was attempted.
    """
    db = get_db()
    db.execute(
        """INSERT INTO login_attempts (identifier, ip_address, success, timestamp)
           VALUES (?, ?, ?, ?)""",
        (identifier, ip_address, int(success), utc_now_iso()),
    )
    db.commit()

    if success:
        return {"status": "normal", "failed_count": 0}

    window_start = seconds_ago_iso(config["BF_WINDOW_SECONDS"])
    failed_count = db.execute(
        """SELECT COUNT(*) FROM login_attempts
           WHERE identifier = ? AND success = 0 AND timestamp >= ?""",
        (identifier, window_start),
    ).fetchone()[0]

    if failed_count >= config["BF_BRUTE_FORCE_THRESHOLD"]:
        _log_event(
            "brute_force_detected", identifier, ip_address,
            f"{failed_count} failed attempts within {config['BF_WINDOW_SECONDS']}s", "high",
        )
        # Only lock an account that actually exists.
        row = db.execute("SELECT 1 FROM users WHERE username = ?", (identifier,)).fetchone()
        if row is not None:
            _apply_lockout(config, identifier, ip_address)
        return {"status": "brute_force", "failed_count": failed_count}

    if failed_count >= config["BF_SUSPICIOUS_THRESHOLD"]:
        _log_event(
            "suspicious_activity", identifier, ip_address,
            f"{failed_count} failed attempts within {config['BF_WINDOW_SECONDS']}s", "medium",
        )
        return {"status": "suspicious", "failed_count": failed_count}

    return {"status": "normal", "failed_count": failed_count}

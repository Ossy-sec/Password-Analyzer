"""Read-only endpoints that feed the security dashboard. No sign-in required."""

from flask import Blueprint, jsonify, request

from db import get_db
from timeutils import seconds_ago_iso

bp = Blueprint("security", __name__, url_prefix="/api/security")


@bp.get("/stats")
def stats():
    db = get_db()
    day_ago = seconds_ago_iso(24 * 3600)

    total_24h = db.execute(
        "SELECT COUNT(*) FROM login_attempts WHERE timestamp >= ?", (day_ago,)
    ).fetchone()[0]
    failed_24h = db.execute(
        "SELECT COUNT(*) FROM login_attempts WHERE timestamp >= ? AND success = 0", (day_ago,)
    ).fetchone()[0]
    suspicious_24h = db.execute(
        """SELECT COUNT(*) FROM security_events
           WHERE timestamp >= ? AND event_type = 'suspicious_activity'""",
        (day_ago,),
    ).fetchone()[0]
    brute_force_24h = db.execute(
        """SELECT COUNT(*) FROM security_events
           WHERE timestamp >= ? AND event_type = 'brute_force_detected'""",
        (day_ago,),
    ).fetchone()[0]
    locked_now = db.execute(
        "SELECT COUNT(*) FROM users WHERE locked_until IS NOT NULL AND locked_until > datetime('now')"
    ).fetchone()[0]

    # Failed attempts bucketed by hour, for the dashboard's bar chart.
    rows = db.execute(
        """SELECT strftime('%Y-%m-%d %H:00:00', timestamp) AS hour, COUNT(*) AS count
           FROM login_attempts
           WHERE timestamp >= ? AND success = 0
           GROUP BY hour ORDER BY hour""",
        (day_ago,),
    ).fetchall()
    hourly_failed = [{"hour": row["hour"], "count": row["count"]} for row in rows]

    return jsonify(
        total_attempts_24h=total_24h,
        failed_attempts_24h=failed_24h,
        suspicious_events_24h=suspicious_24h,
        brute_force_events_24h=brute_force_24h,
        currently_locked_accounts=locked_now,
        hourly_failed_attempts=hourly_failed,
    )


@bp.get("/events")
def events():
    limit = min(request.args.get("limit", 50, type=int) or 50, 200)
    db = get_db()
    rows = db.execute(
        "SELECT event_type, identifier, ip_address, details, severity, timestamp "
        "FROM security_events ORDER BY id DESC LIMIT ?",
        (limit,),
    ).fetchall()
    return jsonify([dict(row) for row in rows])


@bp.get("/attempts")
def attempts():
    limit = min(request.args.get("limit", 50, type=int) or 50, 200)
    db = get_db()
    rows = db.execute(
        "SELECT identifier, ip_address, success, timestamp "
        "FROM login_attempts ORDER BY id DESC LIMIT ?",
        (limit,),
    ).fetchall()
    return jsonify([dict(row) for row in rows])

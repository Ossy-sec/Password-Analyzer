"""
Safe stand-in for an actual brute-force attack script.

Instead of writing (or asking anyone to run) real credential-guessing code,
the dashboard has a button that calls this endpoint a few times in a row.
Each call feeds one synthetic failed login attempt through the exact same
detection pipeline (security/brute_force.py) that real login attempts use,
so you can watch suspicious/brute-force detection trigger without ever
touching a real login form or a real password.

Gated three ways, since even a "fake" endpoint that can lock accounts and
write security events needs care:
  1. config.SIMULATE_ENABLED must be true (off by default outside dev — see
     .env.example) — the single switch to disable this in any non-local setup.
  2. The request must come from localhost, matching what "local-only
     simulation" means in practice.
"""

from flask import Blueprint, current_app, jsonify, request

from security.brute_force import record_attempt

bp = Blueprint("simulate", __name__, url_prefix="/api/simulate")

_LOCAL_ADDRESSES = {"127.0.0.1", "::1"}


@bp.post("/failed-login")
def simulate_failed_login():
    if not current_app.config["SIMULATE_ENABLED"]:
        return jsonify(error="Simulation is disabled on this server"), 403

    if request.remote_addr not in _LOCAL_ADDRESSES:
        return jsonify(error="Simulation is only allowed from localhost"), 403

    data = request.get_json(silent=True) or {}
    identifier = (data.get("identifier") or "").strip()
    if not identifier:
        return jsonify(error="identifier is required"), 400

    outcome = record_attempt(current_app.config, identifier, "127.0.0.1 (simulated)", success=False)
    return jsonify(simulated=True, **outcome)

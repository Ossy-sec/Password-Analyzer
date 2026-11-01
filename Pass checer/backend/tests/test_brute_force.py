from db import get_db
from security.brute_force import get_lockout_remaining, record_attempt
from security.password_hashing import hash_password
from timeutils import utc_now_iso


def _create_user(app, username="bob", password="Correct-Horse-42!"):
    with app.app_context():
        db = get_db()
        db.execute(
            "INSERT INTO users (username, password_hash, created_at) VALUES (?, ?, ?)",
            (username, hash_password(password), utc_now_iso()),
        )
        db.commit()


def test_few_failures_stay_normal(app):
    with app.app_context():
        for _ in range(4):
            outcome = record_attempt(app.config, "carol", "127.0.0.1", success=False)
        assert outcome["status"] == "normal"


def test_five_to_nine_failures_are_suspicious(app):
    with app.app_context():
        for i in range(7):
            outcome = record_attempt(app.config, "dave", "127.0.0.1", success=False)
        assert outcome["status"] == "suspicious"

        db = get_db()
        row = db.execute(
            "SELECT COUNT(*) FROM security_events WHERE event_type = 'suspicious_activity'"
        ).fetchone()
        assert row[0] >= 1


def test_ten_plus_failures_trigger_brute_force_and_lockout(app):
    _create_user(app, "erin")
    with app.app_context():
        outcome = None
        for _ in range(app.config["BF_BRUTE_FORCE_THRESHOLD"]):
            outcome = record_attempt(app.config, "erin", "127.0.0.1", success=False)

        assert outcome["status"] == "brute_force"

        db = get_db()
        bf_events = db.execute(
            "SELECT COUNT(*) FROM security_events WHERE event_type = 'brute_force_detected'"
        ).fetchone()[0]
        assert bf_events >= 1

        remaining = get_lockout_remaining("erin")
        assert remaining > 0


def test_locked_account_rejects_login_even_with_correct_password(client, app):
    _create_user(app, "frank", "Correct-Horse-42!")
    with app.app_context():
        for _ in range(app.config["BF_BRUTE_FORCE_THRESHOLD"]):
            record_attempt(app.config, "frank", "127.0.0.1", success=False)

    response = client.post("/api/login", json={"username": "frank", "password": "Correct-Horse-42!"})
    assert response.status_code == 429
    assert "Retry-After" in response.headers


def test_successful_attempt_does_not_count_toward_threshold(app):
    with app.app_context():
        for _ in range(3):
            record_attempt(app.config, "grace", "127.0.0.1", success=False)
        outcome = record_attempt(app.config, "grace", "127.0.0.1", success=True)
        assert outcome["status"] == "normal"
        outcome = record_attempt(app.config, "grace", "127.0.0.1", success=False)
        # Only 4 failures total so far (3 + 1) — still below the suspicious threshold of 5.
        assert outcome["status"] == "normal"

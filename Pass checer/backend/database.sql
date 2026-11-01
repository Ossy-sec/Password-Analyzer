-- Schema for the Password Security Suite demo app.
-- Applied once by init_db.py (or automatically for the in-memory test DB).

CREATE TABLE IF NOT EXISTS users (
    id            INTEGER PRIMARY KEY AUTOINCREMENT,
    username      TEXT UNIQUE NOT NULL,
    password_hash TEXT NOT NULL,          -- Argon2id hash only — never plaintext
    created_at    TEXT NOT NULL,
    locked_until  TEXT                    -- NULL, or an ISO timestamp the lockout expires at
);

-- A record of every login attempt, used to detect brute-force behaviour.
-- Deliberately has NO password column — only whether the attempt succeeded.
CREATE TABLE IF NOT EXISTS login_attempts (
    id         INTEGER PRIMARY KEY AUTOINCREMENT,
    identifier TEXT NOT NULL,             -- the username that was attempted
    ip_address TEXT NOT NULL,
    success    INTEGER NOT NULL,          -- 0 = failed, 1 = succeeded
    timestamp  TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS security_events (
    id         INTEGER PRIMARY KEY AUTOINCREMENT,
    event_type TEXT NOT NULL,             -- e.g. suspicious_activity, brute_force_detected
    identifier TEXT NOT NULL,
    ip_address TEXT,
    details    TEXT,
    severity   TEXT NOT NULL,             -- low | medium | high
    timestamp  TEXT NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_login_attempts_identifier_time
    ON login_attempts (identifier, timestamp);

CREATE INDEX IF NOT EXISTS idx_security_events_time
    ON security_events (timestamp);

# Password Security Suite

A local, educational security demo with two parts:

1. **Password Strength Analyzer** (`frontend/index.html`) — real-time, client-side entropy scoring, pattern detection, and a k-anonymity breach check. No backend involved; nothing you type ever leaves the browser.
2. **Login + Brute-Force Detection** (`frontend/login.html`, backed by `backend/`) — a small Flask app with real accounts (Argon2id-hashed passwords) and a login endpoint that detects and defends against brute-force guessing.

Everything runs from **one Flask process on one port** — the backend serves the frontend's static files itself, so there's no separate dev server and no CORS configuration.

**New here? Follow [USAGE.md](USAGE.md)** for a step-by-step walkthrough (install → run → try the analyzer → register/log in). The sections below are the reference doc — architecture, API, security notes.

## Architecture

```
Browser  ─────  Flask (backend/app.py), port 5000
                                 ├─ serves frontend/*.html/css/js as static files
                                 └─ /api/*  (JSON)
                                 ├─ auth.py      register / login / logout / me
                                 └─ password.py  check-password (strength)
                                         │
                                         security/brute_force.py  ← detection + lockout logic
                                         security/password_hashing.py  ← Argon2id
                                         security/strength.py  ← entropy scoring
                                                                        │
                                                                    SQLite (backend/instance/app.db)
```

See [db.py](backend/db.py) / [database.sql](backend/database.sql) for the schema (`users`, `login_attempts` — no password column, `security_events`), and [security/brute_force.py](backend/security/brute_force.py) for the detection algorithm (sliding-window failed-attempt counting → suspicious/brute-force thresholds → exponential-backoff lockout + a progressive per-request delay).

## Installation

Requires Python 3.10+.

```bash
cd backend
python -m venv .venv
.venv\Scripts\activate        # Windows
# source .venv/bin/activate   # macOS/Linux
pip install -r requirements.txt
```

## Database setup

```bash
python init_db.py
```

This creates `backend/instance/app.db` with the three tables. Safe to re-run — it won't touch existing data.

## Running the app

```bash
python app.py
```

Open **http://localhost:5000**:

- `/` — the strength analyzer
- `/login.html` — register or log in

Copy `backend/.env.example` to `backend/.env` to change any setting (thresholds, `SECRET_KEY`, etc.) — see that file for what each variable does. `SECRET_KEY` in particular should be a real random value for anything beyond local experimentation:

```bash
python -c "import secrets; print(secrets.token_hex(32))"
```

## How to test password strength

- Visually: type into the analyzer at `/` (or the register form at `/login.html`, which shows a live rating too).
- Via the API directly:
  ```bash
  curl -X POST http://localhost:5000/api/check-password \
       -H "Content-Type: application/json" \
       -d '{"password":"correct-horse-battery-staple"}'
  ```
  Returns `{"bits": ..., "rating": "...", "description": "...", "issues": [...]}`. The password in the request is scored in memory and never logged or stored.

## Running the tests

```bash
cd backend
pytest
```

**Test cases covered** (`backend/tests/`):

- **`test_password_strength.py`** — common passwords score "Very Weak"; a common password embedded in a longer string (e.g. `MyPassword123!`) is still caught; long random/passphrase-style passwords score "Strong"/"Very Strong"; empty input scores 0.
- **`test_brute_force.py`** — 4 failed attempts stay "normal"; 5–9 are flagged "suspicious" with a logged event; 10+ trigger "brute_force" detection, a logged event, and an account lockout; a locked account rejects login (429 + `Retry-After`) even with the correct password.
- **`test_auth.py`** — registration success/duplicate-username/weak-password/invalid-username; login success sets a session; wrong password and nonexistent username return the *same* generic error (no user enumeration); logout clears the session; `/api/check-password` doesn't require login.

## Security considerations

- Passwords are hashed with **Argon2id** (`argon2-cffi`) and never logged or stored in plaintext. `login_attempts` has no password column at all — only whether an attempt succeeded.
- Login failures return one generic message regardless of cause, to avoid revealing which usernames are registered. Registration is the one place that says "username already taken" — a deliberate, documented trade-off (see Future improvements).
- All SQL uses parameterized queries (`?` placeholders) — never string-built SQL.
- Session cookies are `HttpOnly` + `SameSite=Lax`; `SECRET_KEY` comes from `.env` (a startup warning fires if you're still on the default).
- Detection (`security/brute_force.py`) applies a lockout check *before* verifying a password, plus a small capped progressive delay — both are demo-scale techniques; a production system would rate-limit at the network/proxy layer instead of sleeping inside a request.
- `debug=False` by default; error handlers never return stack traces to the client.
- Request bodies are capped at 1 MB (`MAX_CONTENT_LENGTH`) and usernames/passwords have explicit length limits, so oversized payloads are rejected outright rather than processed.

## Project structure

```
frontend/
  index.html, style.css, script.js   Strength analyzer (static, no backend needed)
  theme.css                          Shared design tokens + reusable components
  login.html, auth.css, auth.js      Register / log in
backend/
  app.py            Flask app factory — serves frontend/ + registers the API
  config.py          All tunables, env-var overridable (see .env.example)
  db.py, database.sql, init_db.py    SQLite connection + schema + setup script
  security/
    password_hashing.py   Argon2id hash/verify
    strength.py            Entropy scoring (server-side mirror of script.js)
    brute_force.py         Detection thresholds, lockout, progressive delay
  routes/
    auth.py, password.py
  tests/            pytest suite (see "Running the tests" above)
```

## Future improvements

- Make registration errors generic too (or add a CAPTCHA) to close the last user-enumeration gap.
- IP-based blocklists in addition to per-account lockout.
- Swap the in-request `time.sleep` throttle for a proper rate limiter (e.g. Redis-backed) if this ever needs to run with multiple worker processes.
- Email verification / password reset flow.

## License

MIT — see [LICENSE](LICENSE).

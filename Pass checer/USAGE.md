# Step-by-Step Usage Guide

This walks through using the Password Security Suite from a clean checkout to
registering and logging in. For the architecture/API/security reference, see
[README.md](README.md).

## Step 1 — Install dependencies

Requires Python 3.10+.

```bash
cd backend
python -m venv .venv
.venv\Scripts\activate        # Windows
# source .venv/bin/activate   # macOS/Linux
pip install -r requirements.txt
```

You should see Flask, argon2-cffi, python-dotenv, and pytest install with no errors.

## Step 2 — Create the database

Still inside `backend/`:

```bash
python init_db.py
```

Expected output:

```
Database ready at: .../backend/instance/app.db
```

This only needs to be run once. Re-running it later is harmless.

## Step 3 — Start the server

```bash
python app.py
```

Expected output:

```
 * Running on http://127.0.0.1:5000
```

Leave this running — it's serving both the web pages and the API. Open your
browser to **http://localhost:5000**.

> If you see a `SECRET_KEY` warning printed at startup, that's expected on a
> fresh checkout — see the note at the end of Step 6.

## Step 4 — Try the Password Strength Analyzer

This part needs no account.

1. Go to **http://localhost:5000/** (loads automatically).
2. Type a password into the field, e.g. `password123`.
   - Watch the **verdict** ("Very Weak" → "Very Strong"), the **entropy in bits**, the **crack-time estimate**, and the requirement checklist update live as you type.
   - Try `correct-horse-battery-staple-42` and compare the result.
3. Click the **eye icon** to reveal/hide what you typed.
4. Click the **lightning bolt icon** to generate a strong random passphrase — it's copied to your clipboard automatically (a small toast confirms this).
5. Optional: wait a moment after typing a longer password and check the **Breach check** row — it queries the Have I Been Pwned API using k-anonymity (only the first 5 characters of a SHA-1 hash are sent, so your real password never leaves your device). Requires internet access; if you're offline it says so.

## Step 5 — Register an account

1. Go to **http://localhost:5000/login.html**.
2. Click the **Register** tab.
3. Enter a username (3–32 letters/numbers/underscore) and a password.
   - Watch the **strength hint** next to the password field update as you type — this calls the same server-side scorer used to enforce the minimum.
   - Passwords rated below **"Fair"** are rejected (try `123456` to see the error).
4. Click **Create Account**. On success you're switched to the **Log In** tab with your username pre-filled.

## Step 6 — Log in

1. Enter your password and click **Log In**.
2. You're redirected to the analyzer at `/`.

> **Security note:** the demo ships with a default `SECRET_KEY`. That's fine for
> this local walkthrough, but if you ever run this anywhere reachable by
> others, copy `backend/.env.example` to `backend/.env` and set a real one:
> `python -c "import secrets; print(secrets.token_hex(32))"`.

## Step 7 — Run the automated tests

```bash
cd backend
pytest
```

All 21 tests should pass, covering password scoring, every detection
threshold, lockout enforcement, and the auth endpoints — see the README's
"Running the tests" section for exactly what each test checks.

## Step 8 — Stop the server / start fresh

- Stop the server with `Ctrl+C` in its terminal.
- To reset all data (delete every account, attempt, and event) and start clean: stop the server, delete `backend/instance/app.db`, then re-run `python init_db.py`.

## Troubleshooting

| Symptom | Fix |
|---|---|
| `ModuleNotFoundError: No module named 'flask'` | You're not in the virtualenv — re-run the `activate` command from Step 1. |
| "Account temporarily locked" when you didn't do anything | Someone (or a script) generated 10+ failed attempts for that username within the last 5 minutes — wait for the lockout to expire. |
| Breach check says "unavailable" | You're offline, or the request timed out — this feature needs internet access to reach the Have I Been Pwned API. |
| Port 5000 already in use | Another process is bound to it — stop it, or change the port in `backend/app.py`'s `app.run(...)` call. |

"""
Thin SQLite connection helper.

One connection per request, cached on Flask's `g` so route handlers can call
get_db() as many times as they like without reopening the file, and closed
automatically at the end of every request.
"""

import sqlite3
from pathlib import Path

from flask import current_app, g

SCHEMA_PATH = Path(__file__).resolve().parent / "database.sql"


def get_db():
    if "db" not in g:
        db_path = current_app.config["DATABASE_PATH"]
        if db_path != ":memory:":
            Path(db_path).parent.mkdir(parents=True, exist_ok=True)
        g.db = sqlite3.connect(db_path)
        g.db.row_factory = sqlite3.Row
        g.db.execute("PRAGMA foreign_keys = ON")
    return g.db


def close_db(_exception=None):
    db = g.pop("db", None)
    if db is not None:
        db.close()


def init_db(app):
    """Create the schema (idempotent — safe to call on every startup)."""
    with app.app_context():
        db = get_db()
        db.executescript(SCHEMA_PATH.read_text(encoding="utf-8"))
        db.commit()


def register_app(app):
    app.teardown_appcontext(close_db)

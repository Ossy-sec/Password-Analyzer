"""
One-time (but safe-to-repeat) database setup.

Run this once before starting the server:

    python init_db.py

It creates backend/instance/app.db and the three tables defined in
database.sql. Running it again is harmless — every CREATE statement uses
IF NOT EXISTS, so existing data is left alone.
"""

from app import create_app
from config import Config
from db import init_db

if __name__ == "__main__":
    app = create_app(Config)
    init_db(app)
    print(f"Database ready at: {Config.DATABASE_PATH}")

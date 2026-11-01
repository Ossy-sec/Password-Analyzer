"""
Shared pytest fixtures.

Each test gets its own throwaway SQLite file (not ":memory:" — Flask opens a
fresh connection per request, and an in-memory database would be wiped
between requests inside the same test). The file is deleted automatically
once the test finishes.
"""

import os
import tempfile

import pytest

from app import create_app
from config import TestConfig
from db import init_db


@pytest.fixture
def app():
    db_fd, db_path = tempfile.mkstemp(suffix=".db")

    class _Config(TestConfig):
        DATABASE_PATH = db_path

    flask_app = create_app(_Config)
    init_db(flask_app)

    yield flask_app

    os.close(db_fd)
    os.unlink(db_path)


@pytest.fixture
def client(app):
    return app.test_client()

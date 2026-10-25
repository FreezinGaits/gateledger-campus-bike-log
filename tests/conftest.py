"""Pytest fixtures for GateLedger automated test suite."""

import os
import tempfile
import pytest
from app import create_app
import database


@pytest.fixture
def temp_db_path():
    """Create a temporary SQLite database file for isolated testing."""
    fd, path = tempfile.mkstemp(suffix=".db")
    os.close(fd)
    yield path
    if os.path.exists(path):
        try:
            os.remove(path)
        except OSError:
            pass


@pytest.fixture
def app(temp_db_path):
    """Create an isolated test application instance."""
    app_instance = create_app({
        "TESTING": True,
        "DATABASE_PATH": temp_db_path,
        "POW_DIFFICULTY": 2,
        "SECRET_KEY": "test-secret-key-12345",
        "WTF_CSRF_ENABLED": False,
    })
    yield app_instance


@pytest.fixture
def client(app):
    """Test client without authentication."""
    return app.test_client()


@pytest.fixture
def db_conn(temp_db_path, app):
    """Direct database connection to the isolated test database."""
    conn = database.get_db(temp_db_path)
    yield conn
    conn.close()


@pytest.fixture
def auth_guard(client):
    """Authenticate test client as Security Guard."""
    with client.session_transaction() as sess:
        sess["user_id"] = 2
        sess["username"] = "guard@campus.local"
        sess["role"] = "guard"
        sess["_csrf_token"] = "valid-test-csrf-token"
    return client


@pytest.fixture
def auth_admin(client):
    """Authenticate test client as System Administrator."""
    with client.session_transaction() as sess:
        sess["user_id"] = 1
        sess["username"] = "admin@campus.local"
        sess["role"] = "admin"
        sess["_csrf_token"] = "valid-test-csrf-token"
    return client

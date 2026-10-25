"""Automated tests for User Authentication, Access Control, and CSRF Protection."""

import pytest
from flask import session
import database


def test_successful_login(client):
    """Logging in with correct credentials establishes an authenticated session."""
    # First get login page to set session CSRF token
    client.get("/login")
    with client.session_transaction() as sess:
        token = sess["_csrf_token"]

    resp = client.post(
        "/login",
        data={
            "username": "guard@campus.local",
            "password": "Guard@123",
            "csrf_token": token,
        },
        follow_redirects=True,
    )
    assert resp.status_code == 200
    assert b"Welcome back, guard@campus.local!" in resp.data
    assert b"Campus Security Dashboard" in resp.data


def test_rejection_of_incorrect_password(client):
    """Logging in with incorrect password fails and displays error message."""
    client.get("/login")
    with client.session_transaction() as sess:
        token = sess["_csrf_token"]

    resp = client.post(
        "/login",
        data={
            "username": "guard@campus.local",
            "password": "WrongPassword999",
            "csrf_token": token,
        },
        follow_redirects=True,
    )
    assert resp.status_code == 200
    assert b"Invalid username or password" in resp.data


def test_unauthenticated_access_redirects_to_login(client):
    """Unauthenticated access to protected routes must redirect to /login."""
    resp = client.get("/", follow_redirects=False)
    assert resp.status_code == 302
    assert "/login" in resp.headers["Location"]

    resp2 = client.get("/events/new", follow_redirects=False)
    assert resp2.status_code == 302
    assert "/login" in resp2.headers["Location"]


def test_guard_cannot_access_admin_user_management(auth_guard):
    """A user with 'guard' role must be denied access to /admin/users."""
    resp = auth_guard.get("/admin/users", follow_redirects=True)
    assert resp.status_code == 200
    assert b"Access denied. Administrator privileges are required." in resp.data


def test_admin_can_access_user_management(auth_admin):
    """A user with 'admin' role has access to /admin/users."""
    resp = auth_admin.get("/admin/users", follow_redirects=True)
    assert resp.status_code == 200
    assert b"User Account Administration" in resp.data


def test_deactivated_account_cannot_login(client, db_conn):
    """Deactivated accounts are blocked from logging in."""
    # Deactivate guard account
    cur = db_conn.cursor()
    cur.execute("UPDATE users SET is_active = 0 WHERE username = 'guard@campus.local'")
    db_conn.commit()

    client.get("/login")
    with client.session_transaction() as sess:
        token = sess["_csrf_token"]

    resp = client.post(
        "/login",
        data={
            "username": "guard@campus.local",
            "password": "Guard@123",
            "csrf_token": token,
        },
        follow_redirects=True,
    )
    assert b"Your account has been deactivated" in resp.data


def test_csrf_protection_on_post_requests(client):
    """POST request without a valid CSRF token must be rejected with 400 Bad Request."""
    resp = client.post(
        "/login",
        data={
            "username": "guard@campus.local",
            "password": "Guard@123",
            # No CSRF token provided
        },
    )
    assert resp.status_code == 400
    assert b"400" in resp.data or b"CSRF" in resp.data


def test_cannot_deactivate_last_active_admin(db_conn):
    """System must prevent deactivating the only active administrator."""
    cur = db_conn.cursor()
    cur.execute("SELECT id FROM users WHERE role = 'admin' AND is_active = 1")
    admin_id = cur.fetchone()["id"]

    success, msg = database.toggle_user_active_status(db_conn, admin_id)
    assert success is False
    assert "Cannot deactivate the only remaining active administrator" in msg

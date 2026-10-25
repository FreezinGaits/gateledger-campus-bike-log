"""GateLedger Authentication & Authorization Module
=================================================
Session-based authentication, role-based access control decorators,
and lightweight CSRF token management.
"""

from functools import wraps
import hmac
import secrets
from typing import Any, Callable, Dict, Optional
from flask import abort, flash, redirect, request, session, url_for
from werkzeug.security import check_password_hash, generate_password_hash

import database


def hash_password(password: str) -> str:
    """Generate secure password hash using PBKDF2/SHA256."""
    return generate_password_hash(password)


def verify_password(stored_hash: str, password: str) -> bool:
    """Verify plaintext password against stored hash."""
    return check_password_hash(stored_hash, password)


def login_user(user: Dict[str, Any]) -> None:
    """Store authenticated user details in the active session."""
    session.clear()
    session["user_id"] = user["id"]
    session["username"] = user["username"]
    session["role"] = user["role"]
    # Initialize CSRF token for the session
    get_or_create_csrf_token()


def logout_user() -> None:
    """Clear all session data on logout."""
    session.clear()


def get_current_user(conn) -> Optional[Dict[str, Any]]:
    """Retrieve the full user record for the current session."""
    user_id = session.get("user_id")
    if not user_id:
        return None
    user = database.get_user_by_id(conn, user_id)
    if not user or user["is_active"] != 1:
        return None
    return user


def get_or_create_csrf_token() -> str:
    """Retrieve or generate a cryptographically secure CSRF token in session."""
    if "_csrf_token" not in session:
        session["_csrf_token"] = secrets.token_hex(32)
    return session["_csrf_token"]


def validate_csrf(token: Optional[str]) -> bool:
    """Validate a submitted CSRF token using constant-time comparison."""
    session_token = session.get("_csrf_token")
    if not session_token or not token:
        return False
    return hmac.compare_digest(session_token, token)


def login_required(f: Callable) -> Callable:
    """Decorator requiring an authenticated and active user session."""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if "user_id" not in session:
            flash("Please log in to access this page.", "warning")
            return redirect(url_for("login", next=request.path))
        return f(*args, **kwargs)
    return decorated_function


def admin_required(f: Callable) -> Callable:
    """Decorator requiring an authenticated user with 'admin' role."""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if "user_id" not in session:
            flash("Please log in to access this page.", "warning")
            return redirect(url_for("login", next=request.path))
        if session.get("role") != "admin":
            flash("Access denied. Administrator privileges are required.", "danger")
            return redirect(url_for("dashboard"))
        return f(*args, **kwargs)
    return decorated_function

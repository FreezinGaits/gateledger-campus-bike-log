"""Configuration settings for GateLedger."""
import os
from pathlib import Path
from zoneinfo import ZoneInfo
from dotenv import load_dotenv

# Load environment variables from .env if present
BASE_DIR = Path(__file__).resolve().parent
load_dotenv(BASE_DIR / ".env")


class Config:
    """Base application configuration."""
    SECRET_KEY = os.environ.get(
        "SECRET_KEY", "gateledger-academic-blockchain-campus-security-key-2026"
    )
    
    # On Vercel serverless environments, root is read-only; use /tmp for SQLite
    IS_VERCEL = os.environ.get("VERCEL") == "1"
    DEFAULT_DB_PATH = "/tmp/gateledger.db" if IS_VERCEL else str(BASE_DIR / "gateledger.db")
    DATABASE_PATH = os.environ.get("DATABASE_PATH", DEFAULT_DB_PATH)
    
    POW_DIFFICULTY = int(os.environ.get("POW_DIFFICULTY", "2"))
    APP_TIMEZONE = os.environ.get("APP_TIMEZONE", "Asia/Kolkata")
    
    # Session Cookie Security
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = "Lax"
    SESSION_COOKIE_SECURE = False  # Allows both HTTP local and HTTPS Vercel

    # Default Demo Credentials
    DEFAULT_ADMIN_USER = os.environ.get("DEFAULT_ADMIN_USER", "admin@campus.local")
    DEFAULT_ADMIN_PASSWORD = os.environ.get("DEFAULT_ADMIN_PASSWORD", "Admin@123")
    DEFAULT_GUARD_USER = os.environ.get("DEFAULT_GUARD_USER", "guard@campus.local")
    DEFAULT_GUARD_PASSWORD = os.environ.get("DEFAULT_GUARD_PASSWORD", "Guard@123")

    @classmethod
    def get_tz(cls) -> ZoneInfo:
        """Returns the configured application ZoneInfo."""
        try:
            return ZoneInfo(cls.APP_TIMEZONE)
        except Exception:
            return ZoneInfo("UTC")

from pathlib import Path

from .base import *  # noqa: F403,F401

DEBUG = False

ALLOWED_HOSTS = [".vercel.app", "localhost", "127.0.0.1"]
CORS_ALLOW_ALL_ORIGINS = True

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": Path("/tmp") / "mentriq360-vercel.sqlite3",
    }
}

SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True
SECURE_BROWSER_XSS_FILTER = True
SECURE_CONTENT_TYPE_NOSNIFF = True
SECURE_SSL_REDIRECT = False
X_FRAME_OPTIONS = "DENY"

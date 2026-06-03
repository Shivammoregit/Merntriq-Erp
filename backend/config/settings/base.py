from datetime import timedelta
from pathlib import Path
import re

import environ

BASE_DIR = Path(__file__).resolve().parents[2]

env = environ.Env(
    DJANGO_DEBUG=(bool, False),
    DJANGO_USE_SQLITE=(bool, False),
    DJANGO_ALLOWED_HOSTS=(list, ["localhost", "127.0.0.1"]),
    DJANGO_CORS_ALLOWED_ORIGINS=(list, ["http://localhost:3000"]),
    DJANGO_ACCESS_TOKEN_MINUTES=(int, 30),
    DJANGO_REFRESH_TOKEN_DAYS=(int, 7),
    DJANGO_THROTTLE_ANON_RATE=(str, "30/minute"),
    DJANGO_THROTTLE_USER_RATE=(str, "300/minute"),
    DJANGO_THROTTLE_AUTH_RATE=(str, "10/minute"),
    DJANGO_THROTTLE_CAPTCHA_RATE=(str, "30/minute"),
    DJANGO_THROTTLE_HARDWARE_CAPTURE_RATE=(str, "1200/minute"),
    DJANGO_CACHE_URL=(str, ""),
    CAMPUS_DATABASE_URLS=(str, ""),
    DJANGO_TENANT_DOMAIN_SUFFIX=(str, ""),
    DJANGO_TENANT_ROUTED_APPS=(str, "admin,auth,contenttypes,sessions,token_blacklist,accounts,core"),
)

environ.Env.read_env(BASE_DIR.parent / ".env")

SECRET_KEY = env("DJANGO_SECRET_KEY", default="change-me")
DEBUG = env("DJANGO_DEBUG")
ALLOWED_HOSTS = env("DJANGO_ALLOWED_HOSTS")

INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "corsheaders",
    "drf_spectacular",
    "django_filters",
    "rest_framework",
    "rest_framework_simplejwt",
    "rest_framework_simplejwt.token_blacklist",
    "apps.accounts",
    "apps.core",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "whitenoise.middleware.WhiteNoiseMiddleware",
    "corsheaders.middleware.CorsMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "apps.core.middleware.CampusTenantMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "config.urls"
WSGI_APPLICATION = "config.wsgi.application"
ASGI_APPLICATION = "config.asgi.application"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ]
        },
    }
]

def campus_database_alias(campus_code: str) -> str:
    slug = re.sub(r"[^a-z0-9]+", "_", campus_code.strip().lower()).strip("_")
    return f"campus_{slug}" if slug else ""


def parse_campus_database_urls(raw_value: str) -> tuple[dict, dict[str, str]]:
    databases = {}
    aliases = {}
    for entry in [item.strip() for item in raw_value.split(";") if item.strip()]:
        if "=" not in entry:
            raise ValueError("CAMPUS_DATABASE_URLS entries must use CAMPUS_CODE=database_url format.")
        campus_code, database_url = entry.split("=", 1)
        campus_code = campus_code.strip().upper()
        alias = campus_database_alias(campus_code)
        if not alias:
            raise ValueError("CAMPUS_DATABASE_URLS contains an empty campus code.")
        databases[alias] = environ.Env.db_url_config(database_url.strip())
        aliases[campus_code] = alias
    return databases, aliases


if env("DJANGO_USE_SQLITE"):
    DATABASES = {
        "default": {
            "ENGINE": "django.db.backends.sqlite3",
            "NAME": BASE_DIR / "db.sqlite3",
        }
    }
else:
    DATABASES = {
        "default": {
            "ENGINE": "django.db.backends.postgresql",
            "NAME": env("POSTGRES_DB", default="mentriq360"),
            "USER": env("POSTGRES_USER", default="mentriq360"),
            "PASSWORD": env("POSTGRES_PASSWORD", default="change-me"),
            "HOST": env("POSTGRES_HOST", default="localhost"),
            "PORT": env("POSTGRES_PORT", default="5432"),
        }
    }

CAMPUS_DATABASES, CAMPUS_DATABASE_ALIASES = parse_campus_database_urls(env("CAMPUS_DATABASE_URLS"))
DATABASES.update(CAMPUS_DATABASES)
CAMPUS_DATABASE_ALIAS_SET = set(CAMPUS_DATABASES.keys())
TENANT_ROUTED_APPS = tuple(
    item.strip()
    for item in env("DJANGO_TENANT_ROUTED_APPS").split(",")
    if item.strip()
)
TENANT_CAMPUS_HEADER = "HTTP_X_CAMPUS_CODE"
TENANT_DOMAIN_SUFFIX = env("DJANGO_TENANT_DOMAIN_SUFFIX").strip().lower().strip(".")
DATABASE_ROUTERS = ["apps.core.db_router.CampusTenantRouter"]

AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"},
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator"},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]

LANGUAGE_CODE = "en-us"
TIME_ZONE = "Asia/Kolkata"
USE_I18N = True
USE_TZ = True

STATIC_URL = "/static/"
STATIC_ROOT = BASE_DIR / "staticfiles"
MEDIA_URL = "/media/"
MEDIA_ROOT = BASE_DIR / "media"

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"
AUTH_USER_MODEL = "accounts.User"

CORS_ALLOWED_ORIGINS = env("DJANGO_CORS_ALLOWED_ORIGINS")

cache_url = env("DJANGO_CACHE_URL")
if cache_url:
    CACHES = {
        "default": {
            "BACKEND": "django_redis.cache.RedisCache",
            "LOCATION": cache_url,
            "OPTIONS": {
                "CLIENT_CLASS": "django_redis.client.DefaultClient",
            },
        }
    }
else:
    CACHES = {
        "default": {
            "BACKEND": "django.core.cache.backends.locmem.LocMemCache",
            "LOCATION": "mentriq360-local",
        }
    }

REST_FRAMEWORK = {
    "DEFAULT_AUTHENTICATION_CLASSES": (
        "rest_framework_simplejwt.authentication.JWTAuthentication",
    ),
    "DEFAULT_PERMISSION_CLASSES": (
        "rest_framework.permissions.IsAuthenticated",
    ),
    "DEFAULT_SCHEMA_CLASS": "drf_spectacular.openapi.AutoSchema",
    "DEFAULT_FILTER_BACKENDS": (
        "django_filters.rest_framework.DjangoFilterBackend",
        "rest_framework.filters.OrderingFilter",
        "rest_framework.filters.SearchFilter",
    ),
    "DEFAULT_THROTTLE_CLASSES": (
        "rest_framework.throttling.AnonRateThrottle",
        "rest_framework.throttling.UserRateThrottle",
        "rest_framework.throttling.ScopedRateThrottle",
    ),
    "DEFAULT_THROTTLE_RATES": {
        "anon": env("DJANGO_THROTTLE_ANON_RATE"),
        "user": env("DJANGO_THROTTLE_USER_RATE"),
        "auth": env("DJANGO_THROTTLE_AUTH_RATE"),
        "captcha": env("DJANGO_THROTTLE_CAPTCHA_RATE"),
        "hardware_capture": env("DJANGO_THROTTLE_HARDWARE_CAPTURE_RATE"),
    },
}

SIMPLE_JWT = {
    "ACCESS_TOKEN_LIFETIME": timedelta(minutes=env("DJANGO_ACCESS_TOKEN_MINUTES")),
    "REFRESH_TOKEN_LIFETIME": timedelta(days=env("DJANGO_REFRESH_TOKEN_DAYS")),
    "ROTATE_REFRESH_TOKENS": True,
    "BLACKLIST_AFTER_ROTATION": True,
}

SPECTACULAR_SETTINGS = {
    "TITLE": "Mentriq360 API",
    "DESCRIPTION": "Production-grade ERP API starter.",
    "VERSION": "1.0.0",
}

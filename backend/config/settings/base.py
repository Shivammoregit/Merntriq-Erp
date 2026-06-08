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
    DJANGO_CSRF_TRUSTED_ORIGINS=(list, []),
    DJANGO_USE_X_FORWARDED_HOST=(bool, False),
    DJANGO_ACCESS_TOKEN_MINUTES=(int, 30),
    DJANGO_REFRESH_TOKEN_DAYS=(int, 7),
    DJANGO_THROTTLE_ANON_RATE=(str, "30/minute"),
    DJANGO_THROTTLE_USER_RATE=(str, "300/minute"),
    DJANGO_THROTTLE_AUTH_RATE=(str, "10/minute"),
    DJANGO_THROTTLE_CAPTCHA_RATE=(str, "30/minute"),
    DJANGO_THROTTLE_HARDWARE_CAPTURE_RATE=(str, "1200/minute"),
    DJANGO_THROTTLE_PAYMENT_RATE=(str, "120/minute"),
    DJANGO_PAGE_SIZE=(int, 50),
    DJANGO_MAX_PAGE_SIZE=(int, 200),
    DJANGO_CACHE_URL=(str, ""),
    DATABASE_URL=(str, ""),
    POSTGRES_CONN_MAX_AGE=(int, 60),
    POSTGRES_SSLMODE=(str, ""),
    CAMPUS_DATABASE_URLS=(str, ""),
    DJANGO_TENANT_DOMAIN_SUFFIX=(str, ""),
    DJANGO_TENANT_ROUTED_APPS=(str, "admin,auth,contenttypes,sessions,token_blacklist,accounts,core"),
    DJANGO_MEDIA_URL=(str, "/media/"),
    DJANGO_MEDIA_ROOT=(str, ""),
    DJANGO_FILE_UPLOAD_MAX_MEMORY_SIZE=(int, 10485760),
    DJANGO_DATA_UPLOAD_MAX_MEMORY_SIZE=(int, 10485760),
    DJANGO_LOG_LEVEL=(str, "INFO"),
    MENTRIQ_AI_PROVIDER=(str, "local"),
    MENTRIQ_AI_MODEL=(str, "role-scoped-summary"),
    MENTRIQ_AI_API_KEY=(str, ""),
    MENTRIQ_UPLOAD_LOGO_MAX_BYTES=(int, 524288),
    MENTRIQ_UPLOAD_BANNER_MAX_BYTES=(int, 1048576),
    MENTRIQ_UPLOAD_PHOTO_MAX_BYTES=(int, 2097152),
    MENTRIQ_UPLOAD_DOCUMENT_MAX_BYTES=(int, 5242880),
    MENTRIQ_UPLOAD_ACADEMIC_MAX_BYTES=(int, 10485760),
    MENTRIQ_SUPER_ADMIN_USERNAME=(str, "super.admin"),
    MENTRIQ_SUPER_ADMIN_EMAIL=(str, "super.admin@mentriq360.local"),
    MENTRIQ_SUPER_ADMIN_PASSWORD=(str, ""),
)

environ.Env.read_env(BASE_DIR.parent / ".env")

SECRET_KEY = env("DJANGO_SECRET_KEY", default="change-me")
DEBUG = env("DJANGO_DEBUG")
ALLOWED_HOSTS = env("DJANGO_ALLOWED_HOSTS")
CSRF_TRUSTED_ORIGINS = env("DJANGO_CSRF_TRUSTED_ORIGINS")
USE_X_FORWARDED_HOST = env("DJANGO_USE_X_FORWARDED_HOST")

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


def apply_database_runtime_options(config: dict) -> dict:
    engine = config.get("ENGINE", "")
    if "postgresql" not in engine:
        return config
    config["CONN_MAX_AGE"] = env("POSTGRES_CONN_MAX_AGE")
    sslmode = env("POSTGRES_SSLMODE").strip()
    if sslmode:
        config.setdefault("OPTIONS", {})["sslmode"] = sslmode
    return config


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
        databases[alias] = apply_database_runtime_options(environ.Env.db_url_config(database_url.strip()))
        aliases[campus_code] = alias
    return databases, aliases


database_url = env("DATABASE_URL").strip()
if database_url:
    DATABASES = {
        "default": apply_database_runtime_options(environ.Env.db_url_config(database_url))
    }
elif env("DJANGO_USE_SQLITE"):
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
    DATABASES["default"] = apply_database_runtime_options(DATABASES["default"])

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
    {
        "NAME": "django.contrib.auth.password_validation.MinimumLengthValidator",
        "OPTIONS": {"min_length": 10},
    },
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]

LANGUAGE_CODE = "en-us"
TIME_ZONE = "Asia/Kolkata"
USE_I18N = True
USE_TZ = True

STATIC_URL = "/static/"
STATIC_ROOT = BASE_DIR / "staticfiles"
MEDIA_URL = env("DJANGO_MEDIA_URL")
MEDIA_ROOT = Path(env("DJANGO_MEDIA_ROOT")) if env("DJANGO_MEDIA_ROOT") else BASE_DIR / "media"
FILE_UPLOAD_MAX_MEMORY_SIZE = env("DJANGO_FILE_UPLOAD_MAX_MEMORY_SIZE")
DATA_UPLOAD_MAX_MEMORY_SIZE = env("DJANGO_DATA_UPLOAD_MAX_MEMORY_SIZE")

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"
AUTH_USER_MODEL = "accounts.User"

MENTRIQ_SUPER_ADMIN_USERNAME = env("MENTRIQ_SUPER_ADMIN_USERNAME").strip()
MENTRIQ_SUPER_ADMIN_EMAIL = env("MENTRIQ_SUPER_ADMIN_EMAIL").strip()
MENTRIQ_SUPER_ADMIN_PASSWORD = env("MENTRIQ_SUPER_ADMIN_PASSWORD")
MENTRIQ_AI_PROVIDER = env("MENTRIQ_AI_PROVIDER").strip()
MENTRIQ_AI_MODEL = env("MENTRIQ_AI_MODEL").strip()
MENTRIQ_AI_API_KEY = env("MENTRIQ_AI_API_KEY")
MENTRIQ_UPLOAD_LOGO_MAX_BYTES = env("MENTRIQ_UPLOAD_LOGO_MAX_BYTES")
MENTRIQ_UPLOAD_BANNER_MAX_BYTES = env("MENTRIQ_UPLOAD_BANNER_MAX_BYTES")
MENTRIQ_UPLOAD_PHOTO_MAX_BYTES = env("MENTRIQ_UPLOAD_PHOTO_MAX_BYTES")
MENTRIQ_UPLOAD_DOCUMENT_MAX_BYTES = env("MENTRIQ_UPLOAD_DOCUMENT_MAX_BYTES")
MENTRIQ_UPLOAD_ACADEMIC_MAX_BYTES = env("MENTRIQ_UPLOAD_ACADEMIC_MAX_BYTES")

CORS_ALLOWED_ORIGINS = env("DJANGO_CORS_ALLOWED_ORIGINS")
CORS_ALLOW_CREDENTIALS = True

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
        "payment": env("DJANGO_THROTTLE_PAYMENT_RATE"),
    },
    "DEFAULT_PAGINATION_CLASS": "apps.core.pagination.OptionalPageNumberPagination",
    "PAGE_SIZE": env("DJANGO_PAGE_SIZE"),
}

MAX_PAGE_SIZE = env("DJANGO_MAX_PAGE_SIZE")

SIMPLE_JWT = {
    "ACCESS_TOKEN_LIFETIME": timedelta(minutes=env("DJANGO_ACCESS_TOKEN_MINUTES")),
    "REFRESH_TOKEN_LIFETIME": timedelta(days=env("DJANGO_REFRESH_TOKEN_DAYS")),
    "ROTATE_REFRESH_TOKENS": True,
    "BLACKLIST_AFTER_ROTATION": True,
    "UPDATE_LAST_LOGIN": True,
    "ALGORITHM": "HS256",
    "AUTH_HEADER_TYPES": ("Bearer",),
    "AUTH_TOKEN_CLASSES": ("rest_framework_simplejwt.tokens.AccessToken",),
}

SPECTACULAR_SETTINGS = {
    "TITLE": "Mentriq360 API",
    "DESCRIPTION": "Production-grade ERP API starter.",
    "VERSION": "1.0.0",
    "ENUM_NAME_OVERRIDES": {
        "AcademicEventTypeEnum": "apps.core.models.AcademicEventType.choices",
        "AcademicWorkStatusEnum": "apps.core.models.AcademicWorkStatus.choices",
        "AdmitCardStatusEnum": "apps.core.models.AdmitCardStatus.choices",
        "AnnouncementAudienceEnum": "apps.core.models.AnnouncementAudience.choices",
        "ApprovalStatusEnum": "apps.core.models.ApprovalStatus.choices",
        "AssignmentSubmissionStatusEnum": "apps.core.models.AssignmentSubmissionStatus.choices",
        "AttendanceCaptureMethodEnum": "apps.core.models.AttendanceCaptureMethod.choices",
        "AttendanceStatusEnum": "apps.core.models.AttendanceStatus.choices",
        "AuditActionEnum": "apps.core.models.AuditAction.choices",
        "CampusMemberRoleEnum": "apps.core.models.CampusMemberRole.choices",
        "DeviceStatusEnum": "apps.core.models.DeviceStatus.choices",
        "DeviceSyncStatusEnum": "apps.core.models.DeviceSyncStatus.choices",
        "ExamScheduleStatusEnum": "apps.core.models.ExamScheduleStatus.choices",
        "FeeStatusEnum": "apps.core.models.FeeStatus.choices",
        "FinanceEventTypeEnum": "apps.core.models.FinanceEventType.choices",
        "GatewayProviderEnum": "apps.core.models.GatewayProvider.choices",
        "LibraryBookStatusEnum": "apps.core.models.LibraryBookStatus.choices",
        "LibraryLoanStatusEnum": "apps.core.models.LibraryLoanStatus.choices",
        "MessageChannelEnum": "apps.core.models.MessageChannel.choices",
        "MessageStatusEnum": "apps.core.models.MessageStatus.choices",
        "PaymentMethodEnum": "apps.core.models.PaymentMethod.choices",
        "RecordStatusEnum": "apps.core.models.RecordStatus.choices",
        "ResourceTypeEnum": "apps.core.models.ResourceType.choices",
        "ResultReviewStatusEnum": "apps.core.models.ResultReviewStatus.choices",
        "RS485FunctionEnum": "apps.core.models.RS485Function.choices",
        "SalaryPaymentStatusEnum": "apps.core.models.SalaryPaymentStatus.choices",
        "SchoolStatusEnum": "apps.core.models.SchoolStatus.choices",
        "StaffAttendanceStatusEnum": "apps.core.models.StaffAttendanceStatus.choices",
        "StaffEmploymentTypeEnum": "apps.core.models.StaffEmploymentType.choices",
        "StaffProfileStatusEnum": "apps.core.models.StaffProfileStatus.choices",
        "StudentStatusEnum": "apps.core.models.StudentStatus.choices",
        "SupportTicketPriorityEnum": "apps.core.models.SupportTicketPriority.choices",
        "SupportTicketStatusEnum": "apps.core.models.SupportTicketStatus.choices",
        "TransactionStatusEnum": "apps.core.models.TransactionStatus.choices",
        "WeekdayEnum": "apps.core.models.Weekday.choices",
        "GenderChoiceEnum": "apps.accounts.models.GenderChoice.choices",
        "UserRoleEnum": "apps.accounts.models.UserRole.choices",
    },
}

LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "console": {
            "format": "%(levelname)s %(asctime)s %(name)s %(message)s",
        },
    },
    "handlers": {
        "console": {
            "class": "logging.StreamHandler",
            "formatter": "console",
        },
    },
    "loggers": {
        "django": {
            "handlers": ["console"],
            "level": env("DJANGO_LOG_LEVEL"),
        },
        "apps": {
            "handlers": ["console"],
            "level": env("DJANGO_LOG_LEVEL"),
            "propagate": False,
        },
    },
}

from .production import *  # noqa: F403,F401

VERCEL_FRONTEND_ORIGINS = [
    "https://mentriq-erp.vercel.app",
    "https://web-preetammore106-gmailcoms-projects.vercel.app",
    "https://web-preetammore2-preetammore106-gmailcoms-projects.vercel.app",
]

ALLOWED_HOSTS = env.list(  # noqa: F405
    "DJANGO_ALLOWED_HOSTS",
    default=[".vercel.app", "backend-nu-self-91.vercel.app", "localhost", "127.0.0.1"],
)
CORS_ALLOWED_ORIGINS = env.list("DJANGO_CORS_ALLOWED_ORIGINS", default=VERCEL_FRONTEND_ORIGINS)  # noqa: F405
CSRF_TRUSTED_ORIGINS = env.list("DJANGO_CSRF_TRUSTED_ORIGINS", default=VERCEL_FRONTEND_ORIGINS)  # noqa: F405

# Vercel terminates TLS before invoking the Python runtime.
SECURE_SSL_REDIRECT = env.bool("DJANGO_SECURE_SSL_REDIRECT", default=False)  # noqa: F405

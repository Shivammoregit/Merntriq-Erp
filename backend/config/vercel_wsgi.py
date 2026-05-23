import os
from pathlib import Path

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings.vercel")
os.environ.setdefault("DJANGO_SECRET_KEY", "mentriq360-vercel-demo-key")
os.environ.setdefault("DJANGO_USE_SQLITE", "True")

from django.core.management import call_command  # noqa: E402
from django.core.wsgi import get_wsgi_application  # noqa: E402

application = get_wsgi_application()


def bootstrap_demo_database() -> None:
    marker = Path("/tmp/mentriq360-demo-ready")
    if marker.exists():
        return
    call_command("migrate", interactive=False, verbosity=0)
    call_command("seed_demo", verbosity=0)
    marker.touch()


try:
    bootstrap_demo_database()
except Exception as exc:  # pragma: no cover - Vercel runtime guard
    print(f"MentriQ360 Vercel bootstrap failed: {exc}")

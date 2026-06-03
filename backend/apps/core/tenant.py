from __future__ import annotations

from contextvars import ContextVar, Token
import re

from django.conf import settings

_campus_code: ContextVar[str | None] = ContextVar("campus_code", default=None)
_database_alias: ContextVar[str | None] = ContextVar("campus_database_alias", default=None)


def normalize_campus_database_alias(campus_code: str) -> str:
    slug = re.sub(r"[^a-z0-9]+", "_", campus_code.strip().lower()).strip("_")
    return f"campus_{slug}" if slug else ""


def configured_database_aliases() -> set[str]:
    return set(getattr(settings, "DATABASES", {}).keys())


def get_current_campus_code() -> str | None:
    return _campus_code.get()


def get_current_database_alias() -> str | None:
    alias = _database_alias.get()
    if alias and alias in configured_database_aliases():
        return alias
    return None


def activate_campus_tenant(campus_code: str, database_alias: str) -> tuple[Token[str | None], Token[str | None]]:
    return (
        _campus_code.set(campus_code.strip().upper()),
        _database_alias.set(database_alias),
    )


def reset_campus_tenant(tokens: tuple[Token[str | None], Token[str | None]] | None) -> None:
    if not tokens:
        return
    code_token, alias_token = tokens
    _campus_code.reset(code_token)
    _database_alias.reset(alias_token)

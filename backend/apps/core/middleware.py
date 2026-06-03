from __future__ import annotations

import re

from django.apps import apps
from django.conf import settings
from django.http import JsonResponse

from .tenant import (
    activate_campus_tenant,
    normalize_campus_database_alias,
    reset_campus_tenant,
)


RESERVED_TENANT_HOSTS = {"admin", "app", "erp", "login", "portal", "www"}


class CampusTenantMiddleware:
    """
    Activates a configured campus database for the request.

    Clients select the tenant with X-Campus-Code, the campus_code query param,
    or an enabled subdomain suffix such as north.schools.example.com. The code
    resolves first through CAMPUS_DATABASE_ALIASES from settings, then through
    the default Campus catalog database_alias field, then through the normalized
    campus_<code> alias.
    """

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        campus_code = self._campus_code_from_request(request)
        tokens = None
        database_alias = None

        if campus_code:
            database_alias = self._resolve_database_alias(campus_code)
            if database_alias not in settings.DATABASES:
                return JsonResponse(
                    {
                        "detail": (
                            f"Campus database for {campus_code} is not configured. "
                            f"Expected Django database alias '{database_alias}'."
                        )
                    },
                    status=400,
                )
            tokens = activate_campus_tenant(campus_code, database_alias)
            request.campus_code = campus_code
            request.campus_database_alias = database_alias

        try:
            response = self.get_response(request)
            if campus_code and database_alias:
                response["X-Campus-Code"] = campus_code
                response["X-Campus-Database"] = database_alias
            return response
        finally:
            reset_campus_tenant(tokens)

    def _campus_code_from_request(self, request) -> str:
        header_name = getattr(settings, "TENANT_CAMPUS_HEADER", "HTTP_X_CAMPUS_CODE")
        value = request.META.get(header_name) or request.GET.get("campus_code", "")
        campus_code = self._normalize_campus_code(value)
        if campus_code:
            return campus_code
        return self._campus_code_from_host(request)

    def _campus_code_from_host(self, request) -> str:
        suffix = getattr(settings, "TENANT_DOMAIN_SUFFIX", "")
        if not suffix:
            return ""

        forwarded_host = request.META.get("HTTP_X_FORWARDED_HOST") if getattr(settings, "USE_X_FORWARDED_HOST", False) else ""
        raw_host = forwarded_host or request.META.get("HTTP_HOST") or request.META.get("SERVER_NAME", "")
        host = raw_host.split(",", 1)[0].split(":", 1)[0].strip().lower().rstrip(".")
        suffix = suffix.strip().lower().strip(".")
        if not host.endswith(f".{suffix}"):
            return ""

        tenant_host = host[: -(len(suffix) + 1)].split(".")[-1]
        if not tenant_host or tenant_host in RESERVED_TENANT_HOSTS:
            return ""
        return self._normalize_campus_code(tenant_host)

    def _normalize_campus_code(self, value: str) -> str:
        return re.sub(r"[^a-zA-Z0-9_-]+", "", (value or "").strip()).upper()

    def _resolve_database_alias(self, campus_code: str) -> str:
        configured_alias = getattr(settings, "CAMPUS_DATABASE_ALIASES", {}).get(campus_code)
        if configured_alias:
            return configured_alias

        catalog_alias = self._catalog_database_alias(campus_code)
        if catalog_alias:
            return catalog_alias

        return normalize_campus_database_alias(campus_code)

    def _catalog_database_alias(self, campus_code: str) -> str:
        try:
            Campus = apps.get_model("core", "Campus")
            campus = (
                Campus.objects.using("default")
                .filter(code__iexact=campus_code)
                .only("database_alias")
                .first()
            )
        except Exception:
            return ""
        return (campus.database_alias or "").strip() if campus else ""

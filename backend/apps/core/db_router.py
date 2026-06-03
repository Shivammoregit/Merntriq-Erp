from __future__ import annotations

from django.conf import settings

from .tenant import get_current_database_alias


class CampusTenantRouter:
    """
    Routes ERP models to the active campus database.

    The active database is set by CampusTenantMiddleware from X-Campus-Code.
    Without that header the app continues to use the default database, preserving
    existing local/demo behavior.
    """

    def _is_routed_app(self, app_label: str) -> bool:
        routed_apps = getattr(settings, "TENANT_ROUTED_APPS", ())
        return app_label in routed_apps

    def db_for_read(self, model, **hints):
        if self._is_routed_app(model._meta.app_label):
            return get_current_database_alias()
        return None

    def db_for_write(self, model, **hints):
        if self._is_routed_app(model._meta.app_label):
            return get_current_database_alias()
        return None

    def allow_relation(self, obj1, obj2, **hints):
        db1 = obj1._state.db
        db2 = obj2._state.db
        if db1 and db2:
            return db1 == db2
        return None

    def allow_migrate(self, db, app_label, model_name=None, **hints):
        if db == "default":
            return True
        if db in getattr(settings, "CAMPUS_DATABASE_ALIAS_SET", set()):
            return self._is_routed_app(app_label)
        return None

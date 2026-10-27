"""Health check logic. Never returns internal error details."""

import logging
import secrets

from django.conf import settings
from django.db import connection

logger = logging.getLogger(__name__)

OK = "ok"
UNAVAILABLE = "unavailable"


def password_is_valid(candidate):
    expected = getattr(settings, "HEALTH_CHECK_PASSWORD", "") or ""
    if not expected or not candidate:
        return False
    return secrets.compare_digest(
        str(candidate).encode("utf-8"), expected.encode("utf-8")
    )


def _check_database():
    with connection.cursor() as cursor:
        cursor.execute("SELECT 1")
        cursor.fetchone()


def _check_redis():
    from config.celery import app

    with app.connection_for_read() as conn:
        conn.ensure_connection(max_retries=1)


def _check_celery():
    from config.celery import app

    if not app.control.ping(timeout=1.0):
        raise RuntimeError("no workers")


def run_readiness_checks():
    """Return ``{name: "ok" | "unavailable"}`` for every enabled dependency."""
    checks = {"database": _check_database}
    if getattr(settings, "CELERY_ENABLED", False):
        checks["redis"] = _check_redis
        checks["celery"] = _check_celery

    results = {}
    for name, check in checks.items():
        try:
            check()
            results[name] = OK
        except Exception:  # noqa: BLE001 - details intentionally not exposed
            logger.warning("Readiness check failed: %s", name)
            results[name] = UNAVAILABLE
    return results

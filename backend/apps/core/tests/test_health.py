from unittest import mock

import pytest
from rest_framework.test import APIClient

PASSWORD = "test-health-password"
HEALTH = "/api/v1/health/"
READY = "/api/v1/health/ready/"


@pytest.fixture(autouse=True)
def _health_settings(settings):
    settings.HEALTH_CHECK_PASSWORD = PASSWORD
    settings.CELERY_ENABLED = False


@pytest.fixture
def client():
    return APIClient()


def test_health_endpoint_returns_success_with_valid_password(client):
    r = client.get(HEALTH, HTTP_X_HEALTH_CHECK_TOKEN=PASSWORD)
    assert r.status_code == 200
    assert r.json() == {
        "success": True,
        "message": "Service is healthy.",
        "data": {"status": "healthy"},
    }
    assert client.get(HEALTH, {"password": PASSWORD}).status_code == 200


def test_health_endpoint_rejects_invalid_password(client):
    expected = {
        "success": False,
        "message": "Invalid health check password.",
        "errors": {},
    }
    r = client.get(HEALTH, {"password": "wrong"})
    assert r.status_code == 403
    assert r.json() == expected
    r = client.get(HEALTH, HTTP_X_HEALTH_CHECK_TOKEN="wrong")
    assert r.status_code == 403


def test_health_endpoint_requires_password(client):
    r = client.get(HEALTH)
    assert r.status_code == 403
    assert r.json()["message"] == "Invalid health check password."


def test_health_endpoint_does_not_expose_secret(client):
    for kwargs in ({"HTTP_X_HEALTH_CHECK_TOKEN": PASSWORD}, {}):
        r = client.get(HEALTH, {"password": PASSWORD}, **kwargs)
        assert PASSWORD not in r.content.decode()
    assert PASSWORD not in client.get(HEALTH, {"password": "x"}).content.decode()


def test_health_rejects_when_server_password_unset(client, settings):
    settings.HEALTH_CHECK_PASSWORD = ""
    assert client.get(HEALTH, {"password": ""}).status_code == 403
    assert client.get(HEALTH).status_code == 403


def test_health_does_not_touch_database(client):
    with mock.patch("apps.core.services.connection") as conn:
        conn.cursor.side_effect = RuntimeError("db down")
        r = client.get(HEALTH, HTTP_X_HEALTH_CHECK_TOKEN=PASSWORD)
    assert r.status_code == 200


@pytest.mark.django_db
def test_ready_ok_with_celery_disabled(client):
    r = client.get(READY, HTTP_X_HEALTH_CHECK_TOKEN=PASSWORD)
    assert r.status_code == 200
    assert r.json() == {
        "success": True,
        "message": "Service is ready.",
        "data": {"status": "ready", "checks": {"database": "ok"}},
    }


def test_ready_requires_valid_password(client):
    assert client.get(READY).status_code == 403
    assert client.get(READY, {"password": "bad"}).status_code == 403


def test_ready_database_failure_returns_503_without_details(client):
    with mock.patch("apps.core.services.connection") as conn:
        conn.cursor.side_effect = RuntimeError("secret-db-host:5432 refused")
        r = client.get(READY, HTTP_X_HEALTH_CHECK_TOKEN=PASSWORD)
    assert r.status_code == 503
    assert r.json() == {
        "success": False,
        "message": "Service is not ready.",
        "errors": {"checks": {"database": "unavailable"}},
    }
    assert "secret-db-host" not in r.content.decode()


@pytest.mark.django_db
def test_ready_checks_redis_and_celery_when_enabled(client, settings):
    settings.CELERY_ENABLED = True
    with (
        mock.patch("apps.core.services._check_redis"),
        mock.patch("apps.core.services._check_celery", side_effect=RuntimeError),
    ):
        r = client.get(READY, HTTP_X_HEALTH_CHECK_TOKEN=PASSWORD)
    assert r.status_code == 503
    assert r.json()["errors"] == {"checks": {"celery": "unavailable"}}


@pytest.mark.django_db
def test_ready_all_enabled_ok(client, settings):
    settings.CELERY_ENABLED = True
    with (
        mock.patch("apps.core.services._check_redis"),
        mock.patch("apps.core.services._check_celery"),
    ):
        r = client.get(READY, HTTP_X_HEALTH_CHECK_TOKEN=PASSWORD)
    assert r.json()["data"]["checks"] == {
        "database": "ok",
        "redis": "ok",
        "celery": "ok",
    }


def test_health_rate_limit_returns_429(client, settings, monkeypatch):
    from django.core.cache import cache
    from rest_framework.throttling import SimpleRateThrottle

    settings.CACHES = {
        "default": {
            "BACKEND": "django.core.cache.backends.locmem.LocMemCache",
            "LOCATION": "health-throttle-tests",
        }
    }
    cache.clear()
    monkeypatch.setattr(
        SimpleRateThrottle,
        "THROTTLE_RATES",
        {"anon": "60/minute", "health": "2/minute"},
    )
    codes = [
        client.get(HEALTH, HTTP_X_HEALTH_CHECK_TOKEN=PASSWORD).status_code
        for _ in range(3)
    ]
    cache.clear()
    assert codes == [200, 200, 429]

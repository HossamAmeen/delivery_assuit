import pytest
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient
from rest_framework.throttling import SimpleRateThrottle

pytestmark = [pytest.mark.urls("common.tests.urls"), pytest.mark.django_db]

RATE_BODY = {"success": False, "message": "Request rate limit exceeded.", "errors": {}}


@pytest.fixture(autouse=True)
def isolated_cache(settings, monkeypatch):
    """Fresh locmem cache per test; rates patched (DRF reads them at import)."""
    settings.CACHES = {
        "default": {
            "BACKEND": "django.core.cache.backends.locmem.LocMemCache",
            "LOCATION": "throttle-tests",
        }
    }
    from django.core.cache import cache

    cache.clear()
    rates = {
        "anon": "3/minute",
        "user": "5/minute",
        "auth": "2/minute",
        "sensitive": "4/minute",
        "health": "6/minute",
    }
    monkeypatch.setattr(SimpleRateThrottle, "THROTTLE_RATES", rates)
    yield
    cache.clear()


def hit(client, path, n):
    return [client.get(path).status_code for _ in range(n)]


def test_api_allows_requests_within_rate_limit():
    assert hit(APIClient(), "/ok/", 3) == [200, 200, 200]


def test_api_rejects_requests_after_rate_limit():
    c = APIClient()
    assert hit(c, "/ok/", 3) == [200] * 3
    r = c.get("/ok/")
    assert r.status_code == 429
    assert r.json() == RATE_BODY
    assert "Retry-After" in r


def test_anonymous_user_uses_anonymous_throttle():
    c = APIClient()
    hit(c, "/ok/", 3)
    assert c.get("/ok/").status_code == 429
    # a different client IP has its own bucket
    assert c.get("/ok/", REMOTE_ADDR="10.0.0.9").status_code == 200


def test_authenticated_user_uses_user_throttle():
    u = get_user_model().objects.create_user(username="a", password="x")
    c = APIClient()
    c.force_authenticate(u)
    assert hit(c, "/ok/", 5) == [200] * 5  # beyond anon limit of 3
    r = c.get("/ok/")
    assert r.status_code == 429 and r.json() == RATE_BODY


def test_auth_endpoint_uses_stricter_throttle():
    c = APIClient()
    assert hit(c, "/auth/", 2) == [200, 200]
    r = c.get("/auth/")
    assert r.status_code == 429 and r.json() == RATE_BODY
    assert APIClient().get("/ok/").status_code == 200  # global scope unaffected


def test_sensitive_endpoint_has_stricter_rate_limit():
    c = APIClient()
    assert hit(c, "/sensitive/", 4) == [200] * 4
    r = c.get("/sensitive/")
    assert r.status_code == 429 and r.json() == RATE_BODY


def test_health_endpoint_has_own_scope():
    c = APIClient()
    assert hit(c, "/health/", 6) == [200] * 6
    assert c.get("/health/").status_code == 429
    assert c.get("/ok/").status_code == 200
